# fitness_chatbot/chains/history_chain.py
import logging
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

from fitness_chatbot.core.db_connector import DatabaseConnector
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

# Constante para la tabla
TABLE_NAME = "gym.ejercicios"

class HistoryChain:
    """
    Cadena para procesar consultas sobre el historial de ejercicios del usuario.
    Utiliza LLM para generar consultas SQL y formatear respuestas.
    """
    
    @staticmethod
    async def process_query(user_id: str, query: str) -> str:
        """
        Procesa una consulta sobre historial y devuelve una respuesta formateada.
        
        Args:
            user_id: ID del usuario
            query: Consulta en lenguaje natural
            
        Returns:
            Respuesta formateada para el usuario
        """
        logger.info(f"HistoryChain procesando: '{query}' para usuario {user_id}")
        
        try:
            # Obtener LLM
            llm = get_llm()
            
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return "Lo siento, no puedo procesar tu consulta en este momento. Por favor, intenta más tarde."
            
            # Usar el LLM para generar la consulta SQL con el sistema de prompt
            messages = PromptManager.get_prompt_messages(
                "history", 
                query=query,
                user_id=user_id
            )
            
            # Invocar el LLM
            logger.info("Generando consulta SQL mediante LLM con Chain of Thought")
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extraer el JSON de la respuesta
            sql_data = HistoryChain._extract_sql_from_response(content)
            
            if not sql_data:
                logger.error("No se pudo generar una consulta SQL válida")
                return "Lo siento, no pude entender completamente tu consulta. ¿Podrías reformularla?"
            
            # Asegurarse de que la tabla sea correcta (sin confiar en la IA para esto)
            sql_data["sql"] = HistoryChain._ensure_correct_table(sql_data["sql"])
            
            # Eliminar cualquier referencia a google_id en la consulta SQL
            sql_data["sql"] = HistoryChain._remove_google_id_from_query(sql_data["sql"])
            
            # Ejecutar la consulta SQL
            logger.info(f"Ejecutando SQL: {sql_data['sql']}")
            logger.info(f"Con parámetros: {sql_data['params']}")
            
            # Pasar user_id para que pueda sustituir parámetros si es necesario
            results = HistoryChain._execute_sql_query(sql_data["sql"], sql_data["params"], user_id)
            
            # Identificar el tipo de consulta para formatear los resultados adecuadamente
            tipo_consulta = sql_data.get("tipo_consulta", "")
            exercise_name = HistoryChain._get_exercise_from_params(sql_data["params"])
            
            # Formatear los resultados según el tipo de consulta
            return HistoryChain._format_results(results, exercise_name, tipo_consulta)
        
        except Exception as e:
            logger.exception(f"Error en HistoryChain: {str(e)}")
            return "Lo siento, tuve un problema al procesar tu consulta sobre tu historial de ejercicios."
    
    @staticmethod
    def _extract_sql_from_response(content: str) -> Optional[Dict[str, Any]]:
        """
        Extrae la consulta SQL y los parámetros del contenido generado por el LLM.
        
        Args:
            content: Respuesta del LLM
            
        Returns:
            Diccionario con la consulta SQL y los parámetros, o None si no se pudo extraer
        """
        # Buscar un objeto JSON en la respuesta
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if not json_match:
            logger.warning("No se encontró JSON en la respuesta del LLM")
            return None
        
        try:
            sql_data = json.loads(json_match.group(0))
            
            if "sql" not in sql_data or "params" not in sql_data:
                logger.warning("JSON encontrado pero sin campos sql o params")
                return None
            
            # Validar el número de parámetros vs placeholders %s
            placeholder_count = sql_data["sql"].count("%s")
            param_count = len(sql_data["params"])
            
            if placeholder_count != param_count:
                logger.warning(f"Número de placeholders (%s) no coincide con parámetros: {placeholder_count} vs {param_count}")
                # Ajustar la lista de parámetros si faltan o sobran
                if placeholder_count > param_count:
                    # Agregar más parámetros 'user_id' para completar
                    sql_data["params"].extend(['user_id'] * (placeholder_count - param_count))
                elif placeholder_count < param_count:
                    # Recortar los parámetros excedentes
                    sql_data["params"] = sql_data["params"][:placeholder_count]
            
            # Verificar si hay una explicación del tipo de consulta
            if "tipo_consulta" not in sql_data:
                # Intentar inferir el tipo de consulta desde el SQL
                if "LIMIT 1" in sql_data["sql"]:
                    sql_data["tipo_consulta"] = "última_sesión"
                elif "LIMIT" in sql_data["sql"]:
                    sql_data["tipo_consulta"] = "múltiples_sesiones"
                else:
                    sql_data["tipo_consulta"] = "listado_general"
            
            return sql_data
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON de la respuesta del LLM")
            return None
    
    @staticmethod
    def _ensure_correct_table(sql: str) -> str:
        """
        Asegura que la consulta SQL use la tabla correcta.
        
        Args:
            sql: Consulta SQL generada por la IA
            
        Returns:
            Consulta SQL corregida con la tabla correcta
        """
        # Reemplazar cualquier tabla por la tabla correcta
        table_pattern = r'FROM\s+([^\s]+)'
        match = re.search(table_pattern, sql)
        
        if match:
            current_table = match.group(1)
            if current_table != TABLE_NAME:
                logger.warning(f"Tabla incorrecta detectada: {current_table}. Reemplazando por {TABLE_NAME}")
                return sql.replace(f"FROM {current_table}", f"FROM {TABLE_NAME}")
        
        return sql
    
    @staticmethod
    def _remove_google_id_from_query(sql: str) -> str:
        """
        Elimina cualquier referencia a google_id en la consulta SQL.
        
        Args:
            sql: Consulta SQL a corregir
            
        Returns:
            Consulta SQL sin referencias a google_id
        """
        # Buscar y quitar cláusulas que mencionen google_id
        google_id_pattern = r'\s+OR\s+google_id\s*=\s*%s'
        return re.sub(google_id_pattern, '', sql)
    
    @staticmethod
    def _get_exercise_from_params(params: List) -> Optional[str]:
        """
        Intenta extraer el nombre del ejercicio de los parámetros.
        
        Args:
            params: Lista de parámetros para la consulta SQL
            
        Returns:
            Nombre del ejercicio o None si no se puede detectar
        """
        for param in params:
            if isinstance(param, str) and param.startswith("%") and param.endswith("%"):
                # Es probablemente un parámetro de ejercicio (ILIKE)
                exercise = param.strip("%")
                return exercise
        
        return None
    
    @staticmethod
    def _execute_sql_query(sql_query: str, params: List, user_id: str) -> List:
        """
        Ejecuta la consulta SQL.
        
        Args:
            sql_query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            user_id: ID del usuario para sustituir parámetros si es necesario
            
        Returns:
            Resultados de la consulta
        """
        conn = None
        try:
            # Procesar parámetros para sustituir cualquier referencia a 'user_id' por el valor real
            processed_params = []
            for param in params:
                if param == 'user_id':
                    # Reemplazar con el valor real
                    processed_params.append(user_id)
                else:
                    processed_params.append(param)
            
            db_config = DatabaseConnector.get_db_config()
            logger.info(f"Configuración DB: {db_config}")
            conn = psycopg2.connect(**db_config)
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(sql_query, processed_params)
            results = cursor.fetchall()
            cursor.close()
            
            logger.info(f"Consulta ejecutada. Resultados: {len(results)}")
            return results
        except Exception as e:
            logger.error(f"Error ejecutando consulta SQL: {str(e)}")
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def _format_results(results: List, exercise_name: Optional[str], tipo_consulta: str) -> str:
        """
        Formatea los resultados de la consulta en una respuesta para el usuario.
        
        Args:
            results: Resultados de la consulta SQL
            exercise_name: Nombre del ejercicio (si se detectó)
            tipo_consulta: Tipo de consulta (última_sesión, múltiples_sesiones, etc.)
            
        Returns:
            Respuesta formateada
        """
        # Si no hay resultados
        if not results:
            if exercise_name:
                return f"No encontré registros de **{exercise_name}** en tu historial. ¿Quieres registrar este ejercicio?"
            else:
                return "No encontré registros de ejercicios en tu historial. ¿Quieres empezar a registrar tus entrenamientos?"
        
        # Formatear según el tipo de consulta
        if tipo_consulta == "última_sesión" and len(results) > 0:
            # Si el ejercicio es dominadas y la consulta es sobre repeticiones
            if exercise_name and "dominada" in exercise_name.lower():
                return HistoryChain._format_dominadas_reps_response(results[0])
            else:
                return HistoryChain._format_single_session(results[0], exercise_name)
        elif tipo_consulta == "múltiples_sesiones" and len(results) > 0:
            return HistoryChain._format_session_list(results, exercise_name)
        else:
            # Por defecto, resumen de ejercicios o resultado genérico
            if 'ejercicio' in results[0] and 'total' in results[0]:
                return HistoryChain._format_exercise_summary(results)
            else:
                return HistoryChain._format_session_list(results, exercise_name)
    
    @staticmethod
    def _format_dominadas_reps_response(result: Dict) -> str:
        """
        Formatea una respuesta específica para la consulta de repeticiones de dominadas.
        
        Args:
            result: Resultado de la consulta SQL
            
        Returns:
            Respuesta formateada
        """
        fecha = result['fecha'].strftime("%Y-%m-%d %H:%M") if hasattr(result['fecha'], 'strftime') else result['fecha']
        
        respuesta = "## 🏋️ Repeticiones en tu última sesión de dominadas\n\n"
        respuesta += f"En tu sesión del **{fecha}**, hiciste:\n\n"
        
        # Procesar series_json (NUEVO FORMATO)
        if 'series_json' in result and result['series_json']:
            try:
                # Convertir a JSON si es string
                if isinstance(result['series_json'], str):
                    series = json.loads(result['series_json'])
                else:
                    series = result['series_json']
                
                # Solo procesar si es una lista
                if isinstance(series, list):
                    # Calcular total de repeticiones
                    total_reps = sum(s.get('repeticiones', 0) for s in series if isinstance(s, dict))
                    respuesta += f"**Total: {total_reps} repeticiones**\n\n"
                    
                    # Detallar cada serie
                    respuesta += "**Desglose por series:**\n"
                    for i, serie in enumerate(series, 1):
                        if isinstance(serie, dict):
                            reps = serie.get('repeticiones', 0)
                            peso = serie.get('peso', 0)
                            rir = serie.get('rir', None)
                            
                            if peso > 0:
                                respuesta += f"• Serie {i}: **{reps} repeticiones** con {peso} kg de peso"
                            else:
                                respuesta += f"• Serie {i}: **{reps} repeticiones** con tu peso corporal"
                            
                            # Añadir RIR si está disponible
                            if rir is not None:
                                respuesta += f" (RIR: {rir})"
                            
                            respuesta += "\n"
                        else:
                            respuesta += f"• Serie {i}: {str(serie)}\n"
                else:
                    respuesta += f"**Datos:** {str(series)}\n"
            except Exception as e:
                logger.error(f"Error procesando series_json: {e}")
                respuesta += "No pude procesar el formato detallado de las repeticiones.\n"
        
        # Intentar con el formato antiguo si no hay series_json
        elif 'repeticiones' in result and result['repeticiones']:
            try:
                # Verificar si repeticiones es un número (nuevo formato) o JSON (antiguo formato)
                if isinstance(result['repeticiones'], int) or (isinstance(result['repeticiones'], str) and result['repeticiones'].isdigit()):
                    # En el nuevo formato, repeticiones es el total
                    respuesta += f"**Total: {result['repeticiones']} repeticiones**\n\n"
                    respuesta += "No tengo el detalle de cada serie.\n"
                else:
                    # Convertir a JSON si es string
                    if isinstance(result['repeticiones'], str):
                        series = json.loads(result['repeticiones'])
                    else:
                        series = result['repeticiones']
                    
                    # Solo procesar si es una lista
                    if isinstance(series, list):
                        # Calcular total de repeticiones
                        total_reps = sum(s.get('repeticiones', 0) for s in series if isinstance(s, dict))
                        respuesta += f"**Total: {total_reps} repeticiones**\n\n"
                        
                        # Detallar cada serie
                        respuesta += "**Desglose por series:**\n"
                        for i, serie in enumerate(series, 1):
                            if isinstance(serie, dict):
                                reps = serie.get('repeticiones', 0)
                                peso = serie.get('peso', 0)
                                
                                if peso > 0:
                                    respuesta += f"• Serie {i}: **{reps} repeticiones** con {peso} kg de peso\n"
                                else:
                                    respuesta += f"• Serie {i}: **{reps} repeticiones** con tu peso corporal\n"
                            else:
                                respuesta += f"• Serie {i}: {str(serie)}\n"
                    else:
                        respuesta += f"**Datos:** {str(series)}\n"
            except Exception as e:
                logger.error(f"Error procesando repeticiones (formato antiguo): {e}")
                # Si falla el parsing, podría ser que repeticiones ahora sea un número total
                try:
                    respuesta += f"**Total: {int(result['repeticiones'])} repeticiones**\n\n"
                    respuesta += "No tengo el detalle de cada serie.\n"
                except:
                    respuesta += "No pude procesar el formato detallado de las repeticiones.\n"
        
        # Añadir comentarios si están disponibles
        if 'comentarios' in result and result['comentarios']:
            respuesta += f"\n**Notas:** {result['comentarios']}\n"
        
        # Añadir RIR global si está disponible
        if 'rir' in result and result['rir'] is not None:
            respuesta += f"\n**RIR global:** {result['rir']}\n"
        
        return respuesta
    
    @staticmethod
    def _format_single_session(result: Dict, exercise_name: str) -> str:
        """
        Formatea una respuesta para una sola sesión de ejercicio.
        
        Args:
            result: Resultado de la consulta SQL
            exercise_name: Nombre del ejercicio
            
        Returns:
            Respuesta formateada
        """
        ejercicio = result.get('ejercicio', exercise_name) if result.get('ejercicio') else exercise_name
        fecha = result['fecha'].strftime("%Y-%m-%d %H:%M") if hasattr(result['fecha'], 'strftime') else result['fecha']
        
        respuesta = f"## 🏋️ Última sesión de {ejercicio}\n\n"
        respuesta += f"**Fecha:** {fecha}\n\n"
        
        # Añadir comentarios si están disponibles
        if 'comentarios' in result and result['comentarios']:
            respuesta += f"**Notas:** {result['comentarios']}\n\n"
        
        # Añadir RIR global si está disponible
        if 'rir' in result and result['rir'] is not None:
            respuesta += f"**RIR global:** {result['rir']}\n\n"
        
        # Procesar series_json (NUEVO FORMATO)
        if 'series_json' in result and result['series_json']:
            try:
                # Convertir a JSON si es string
                if isinstance(result['series_json'], str):
                    series = json.loads(result['series_json'])
                else:
                    series = result['series_json']
                
                # Solo procesar si es una lista
                if isinstance(series, list):
                    # Calcular totales
                    total_reps = sum(s.get('repeticiones', 0) for s in series if isinstance(s, dict))
                    max_peso = max((s.get('peso', 0) for s in series if isinstance(s, dict)), default=0)
                    volumen = sum(s.get('repeticiones', 0) * s.get('peso', 0) for s in series if isinstance(s, dict))
                    
                    respuesta += f"**Total repeticiones:** {total_reps}\n"
                    respuesta += f"**Peso máximo usado:** {max_peso} kg\n"
                    respuesta += f"**Volumen total:** {volumen} kg\n\n"
                    
                    # Detallar cada serie
                    respuesta += "**Series:**\n"
                    for i, serie in enumerate(series, 1):
                        if isinstance(serie, dict):
                            reps = serie.get('repeticiones', 0)
                            peso = serie.get('peso', 0)
                            rir = serie.get('rir', None)
                            
                            serie_texto = f"• Serie {i}: {reps} repeticiones × {peso} kg"
                            
                            # Añadir RIR si está disponible
                            if rir is not None:
                                serie_texto += f" (RIR: {rir})"
                            
                            respuesta += serie_texto + "\n"
                        else:
                            respuesta += f"• Serie {i}: {str(serie)}\n"
                else:
                    respuesta += f"**Datos:** {str(series)}\n"
            except Exception as e:
                logger.error(f"Error procesando series_json: {e}")
                respuesta += "No pude procesar el formato detallado de las repeticiones.\n"
        
        # Intentar con el formato antiguo si no hay series_json
        elif 'repeticiones' in result and result['repeticiones']:
            try:
                # Verificar si repeticiones es un número (nuevo formato) o JSON (antiguo formato)
                if isinstance(result['repeticiones'], int) or (isinstance(result['repeticiones'], str) and result['repeticiones'].isdigit()):
                    # En el nuevo formato, repeticiones es el total
                    respuesta += f"**Total repeticiones:** {result['repeticiones']}\n"
                    respuesta += "No tengo el detalle de cada serie.\n"
                else:
                    # Convertir a JSON si es string
                    if isinstance(result['repeticiones'], str):
                        series = json.loads(result['repeticiones'])
                    else:
                        series = result['repeticiones']
                    
                    # Solo procesar si es una lista
                    if isinstance(series, list):
                        # Calcular totales
                        total_reps = sum(s.get('repeticiones', 0) for s in series if isinstance(s, dict))
                        max_peso = max((s.get('peso', 0) for s in series if isinstance(s, dict)), default=0)
                        volumen = sum(s.get('repeticiones', 0) * s.get('peso', 0) for s in series if isinstance(s, dict))
                        
                        respuesta += f"**Total repeticiones:** {total_reps}\n"
                        respuesta += f"**Peso máximo usado:** {max_peso} kg\n"
                        respuesta += f"**Volumen total:** {volumen} kg\n\n"
                        
                        # Detallar cada serie
                        respuesta += "**Series:**\n"
                        for i, serie in enumerate(series, 1):
                            if isinstance(serie, dict):
                                reps = serie.get('repeticiones', 0)
                                peso = serie.get('peso', 0)
                                respuesta += f"• Serie {i}: {reps} repeticiones × {peso} kg\n"
                            else:
                                respuesta += f"• Serie {i}: {str(serie)}\n"
                    else:
                        respuesta += f"**Datos:** {str(series)}\n"
            except Exception as e:
                logger.error(f"Error procesando repeticiones (formato antiguo): {e}")
                # Si falla el parsing, podría ser que repeticiones ahora sea un número total
                try:
                    respuesta += f"**Total repeticiones:** {int(result['repeticiones'])}\n"
                    respuesta += "No tengo el detalle de cada serie.\n"
                except:
                    respuesta += "No pude procesar el formato detallado de las repeticiones.\n"
        
        return respuesta
    
    @staticmethod
    def _format_session_list(results: List, exercise_name: str) -> str:
        """
        Formatea una respuesta para múltiples sesiones de ejercicio.
        
        Args:
            results: Resultados de la consulta SQL
            exercise_name: Nombre del ejercicio
            
        Returns:
            Respuesta formateada
        """
        # Determinar el ejercicio (tomándolo del primer resultado o usando el proporcionado)
        ejercicio = results[0].get('ejercicio', exercise_name) if results and 'ejercicio' in results[0] else exercise_name
        
        respuesta = f"## 📊 Historial de {ejercicio}\n\n"
        respuesta += f"Encontré **{len(results)} sesiones** registradas.\n\n"
        
        # Mostrar cada sesión
        for i, row in enumerate(results):
            fecha = row['fecha'].strftime("%Y-%m-%d %H:%M") if hasattr(row['fecha'], 'strftime') else row['fecha']
            
            respuesta += f"### Sesión {i+1} - {fecha}\n"
            
            # Añadir comentarios si están disponibles
            if 'comentarios' in row and row['comentarios']:
                respuesta += f"**Notas:** {row['comentarios']}\n"
            
            # Añadir RIR global si está disponible
            if 'rir' in row and row['rir'] is not None:
                respuesta += f"**RIR global:** {row['rir']}\n"
            
            # Procesar series_json (NUEVO FORMATO)
            if 'series_json' in row and row['series_json']:
                try:
                    # Convertir a JSON si es string
                    if isinstance(row['series_json'], str):
                        series = json.loads(row['series_json'])
                    else:
                        series = row['series_json']
                    
                    # Solo procesar si es una lista
                    if isinstance(series, list):
                        # Calcular totales
                        total_reps = sum(s.get('repeticiones', 0) for s in series if isinstance(s, dict))
                        max_peso = max((s.get('peso', 0) for s in series if isinstance(s, dict)), default=0)
                        volumen = sum(s.get('repeticiones', 0) * s.get('peso', 0) for s in series if isinstance(s, dict))
                        
                        respuesta += f"**Total repeticiones:** {total_reps}\n"
                        respuesta += f"**Peso máximo:** {max_peso} kg\n"
                        respuesta += f"**Volumen total:** {volumen} kg\n"
                        
                        # Detallar cada serie
                        respuesta += "**Series:**\n"
                        for j, serie in enumerate(series, 1):
                            if isinstance(serie, dict):
                                reps = serie.get('repeticiones', 0)
                                peso = serie.get('peso', 0)
                                rir = serie.get('rir', None)
                                
                                serie_texto = f"• Serie {j}: {reps} repeticiones × {peso} kg"
                                
                                # Añadir RIR si está disponible
                                if rir is not None:
                                    serie_texto += f" (RIR: {rir})"
                                
                                respuesta += serie_texto + "\n"
                            else:
                                respuesta += f"• Serie {j}: {str(serie)}\n"
                    else:
                        respuesta += f"**Datos:** {str(series)}\n"
                except Exception as e:
                    logger.error(f"Error procesando series_json: {e}")
                    respuesta += "No pude procesar el formato detallado.\n"
            
            # Intentar con el formato antiguo si no hay series_json
            elif 'repeticiones' in row and row['repeticiones']:
                try:
                    # Verificar si repeticiones es un número (nuevo formato) o JSON (antiguo formato)
                    if isinstance(row['repeticiones'], int) or (isinstance(row['repeticiones'], str) and row['repeticiones'].isdigit()):
                        # En el nuevo formato, repeticiones es el total
                        respuesta += f"**Total repeticiones:** {row['repeticiones']}\n"
                        respuesta += "No tengo el detalle de cada serie.\n"
                    else:
                        # Convertir a JSON si es string
                        if isinstance(row['repeticiones'], str):
                            series = json.loads(row['repeticiones'])
                        else:
                            series = row['repeticiones']
                        
                        # Solo procesar si es una lista
                        if isinstance(series, list):
                            # Calcular totales
                            total_reps = sum(s.get('repeticiones', 0) for s in series if isinstance(s, dict))
                            max_peso = max((s.get('peso', 0) for s in series if isinstance(s, dict)), default=0)
                            volumen = sum(s.get('repeticiones', 0) * s.get('peso', 0) for s in series if isinstance(s, dict))
                            
                            respuesta += f"**Total repeticiones:** {total_reps}\n"
                            respuesta += f"**Peso máximo:** {max_peso} kg\n"
                            respuesta += f"**Volumen total:** {volumen} kg\n"
                            
                            # Detallar cada serie
                            respuesta += "**Series:**\n"
                            for j, serie in enumerate(series, 1):
                                if isinstance(serie, dict):
                                    reps = serie.get('repeticiones', 0)
                                    peso = serie.get('peso', 0)
                                    respuesta += f"• Serie {j}: {reps} repeticiones × {peso} kg\n"
                                else:
                                    respuesta += f"• Serie {j}: {str(serie)}\n"
                        else:
                            respuesta += f"**Datos:** {str(series)}\n"
                except Exception as e:
                    logger.error(f"Error procesando repeticiones (formato antiguo): {e}")
                    # Si falla el parsing, podría ser que repeticiones ahora sea un número total
                    try:
                        respuesta += f"**Total repeticiones:** {int(row['repeticiones'])}\n"
                        respuesta += "No tengo el detalle de cada serie.\n"
                    except:
                        respuesta += "No pude procesar el formato detallado.\n"
            
            respuesta += "\n"
        
        return respuesta
    
    @staticmethod
    def _format_exercise_summary(results: List) -> str:
        """
        Formatea un resumen de ejercicios con conteo y fechas.
        
        Args:
            results: Resultados de la consulta SQL
            
        Returns:
            Respuesta formateada
        """
        respuesta = "## 📊 Tu Historial de Ejercicios\n\n"
        respuesta += f"Has realizado **{len(results)} ejercicios diferentes** en tu historial.\n\n"
        
        # Mostrar cada ejercicio con su conteo y fecha
        for row in results:
            ejercicio = row.get('ejercicio', 'Desconocido')
            total = row.get('total', 0) or row.get('count', 0)
            
            if 'ultima_fecha' in row and row['ultima_fecha']:
                fecha = row['ultima_fecha'].strftime("%Y-%m-%d") if hasattr(row['ultima_fecha'], 'strftime') else row['ultima_fecha']
                respuesta += f"• **{ejercicio}** - {total} sesiones (última: {fecha})\n"
            else:
                respuesta += f"• **{ejercicio}** - {total} sesiones\n"
        
        respuesta += "\n¿Quieres ver detalles sobre algún ejercicio específico?"
        return respuesta