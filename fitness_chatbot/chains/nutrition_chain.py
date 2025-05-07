# fitness_chatbot/chains/nutrition_chain.py
import logging
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.db_connector import DatabaseConnector

logger = logging.getLogger("fitness_chatbot")

class NutritionChain:
    """
    Cadena para procesar consultas sobre nutrición y planes alimenticios.
    Utiliza LLM para generar consultas SQL y formatear respuestas.
    """
    
    @staticmethod
    async def process_query(user_id: str, query: str) -> str:
        """
        Procesa una consulta sobre nutrición y devuelve una respuesta formateada.
        
        Args:
            user_id: ID del usuario (google_id)
            query: Consulta en lenguaje natural
            
        Returns:
            Respuesta formateada para el usuario
        """
        logger.info(f"NutritionChain procesando: '{query}' para usuario {user_id}")
        
        try:
            # Obtener LLM
            llm = get_llm()
            
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return "Lo siento, no puedo procesar tu consulta en este momento. Por favor, intenta más tarde."
            
            # Usar el LLM para generar la consulta SQL con el sistema de prompt
            messages = PromptManager.get_prompt_messages(
                "nutrition", 
                query=query,
                user_id=user_id
            )
            
            # Invocar el LLM
            logger.info("Generando consulta SQL mediante LLM")
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Log completo de la respuesta para diagnóstico
            logger.info(f"Respuesta completa del LLM: {content}")
            
            # Extraer el JSON de la respuesta
            sql_data = NutritionChain._extract_sql_from_response(content)
            
            # Obtener el día de la semana actual (1-7, donde 1 es lunes)
            current_day = str(datetime.now().isoweekday())
            
            # Si no se pudo extraer un SQL válido, usar uno predefinido
            if not sql_data:
                logger.warning("No se pudo extraer SQL válido, usando consulta predefinida")
                sql_data = {
                    "sql": """
                    SELECT mpi.meal_type, m.meal_name 
                    FROM nutrition.meal_plans mp
                    JOIN nutrition.meal_plan_items mpi ON mpi.meal_plan_id = mp.id
                    JOIN nutrition.meals m ON mpi.meal_id = m.id
                    WHERE mp.user_id = %s
                      AND mp.is_active = TRUE
                      AND mpi.day_of_week = %s
                    """,
                    "params": [user_id, current_day],
                    "tipo_consulta": "plan_diario"
                }
            else:
                # Corregir parámetros para asegurar valores correctos
                corrected_params = []
                for param in sql_data["params"]:
                    if param == "user_id_value" or param == "{user_id}":
                        corrected_params.append(user_id)
                    elif param in ["current_day_number", "día_actual", "{current_day}"]:
                        corrected_params.append(current_day)
                    else:
                        corrected_params.append(param)
                
                # Actualizar los parámetros
                sql_data["params"] = corrected_params
                
                # Verificar si la consulta tiene errores comunes y corregirlos
                sql_data["sql"] = NutritionChain._correct_common_sql_errors(sql_data["sql"])
            
            # Ejecutar la consulta SQL
            logger.info(f"Ejecutando SQL: {sql_data['sql']}")
            logger.info(f"Con parámetros: {sql_data['params']}")
            
            try:
                # Ejecutar la consulta
                results = await DatabaseConnector.execute_query(
                    sql_data["sql"], 
                    sql_data["params"],
                    fetch_all=True
                )
            except Exception as e:
                # Si falla, intentar con una consulta de fallback más simple
                logger.error(f"Error ejecutando la consulta: {str(e)}")
                logger.info("Intentando con consulta SQL de respaldo simplificada")
                
                # Utilizar la consulta de respaldo simplificada
                backup_sql = """
                SELECT mpi.meal_type, m.meal_name 
                FROM nutrition.meal_plans mp
                JOIN nutrition.meal_plan_items mpi ON mpi.meal_plan_id = mp.id
                JOIN nutrition.meals m ON mpi.meal_id = m.id
                WHERE mp.user_id = %s
                """
                backup_params = [user_id]
                
                try:
                    results = await DatabaseConnector.execute_query(
                        backup_sql, 
                        backup_params,
                        fetch_all=True
                    )
                    
                    # Filtrar los resultados manualmente por día si es posible
                    filtered_results = []
                    for row in results:
                        try:
                            if 'day_of_week' in row and str(row['day_of_week']) == current_day:
                                filtered_results.append(row)
                        except:
                            # Si hay error al filtrar, incluir la fila
                            filtered_results.append(row)
                    
                    results = filtered_results if filtered_results else results
                    
                except Exception as backup_error:
                    logger.error(f"Error ejecutando consulta de respaldo: {str(backup_error)}")
                    return "Lo siento, tuve un problema al obtener la información sobre tu plan nutricional. Por favor, intenta de nuevo más tarde."
            
            # Formatear los resultados
            tipo_consulta = sql_data.get("tipo_consulta", "plan_diario")
            return NutritionChain._format_results(results, tipo_consulta)
        
        except Exception as e:
            logger.exception(f"Error en NutritionChain: {str(e)}")
            return "Lo siento, tuve un problema al procesar tu consulta. Por favor, intenta de nuevo más tarde."
    
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
            
            # Intentar extraer SQL y params de manera más flexible
            sql_match = re.search(r'```sql\s*(.*?)\s*```', content, re.DOTALL)
            if sql_match:
                sql = sql_match.group(1).strip()
                logger.info(f"SQL extraído de la respuesta: {sql}")
                
                # Construir un objeto SQL manualmente
                return {
                    "sql": sql,
                    "params": [],  # Los parámetros serán corregidos después
                    "tipo_consulta": "plan_diario"
                }
            
            return None
        
        try:
            sql_data = json.loads(json_match.group(0))
            
            if "sql" not in sql_data:
                logger.warning("JSON encontrado pero sin campo sql")
                return None
            
            # Si no hay params, agregarlo vacío
            if "params" not in sql_data:
                sql_data["params"] = []
            
            # Si no hay tipo_consulta, establecer un valor por defecto
            if "tipo_consulta" not in sql_data:
                sql_data["tipo_consulta"] = "plan_diario"
            
            return sql_data
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON de la respuesta del LLM")
            return None
    
    @staticmethod
    def _correct_common_sql_errors(sql: str) -> str:
        """
        Corrige errores comunes en la consulta SQL generada.
        
        Args:
            sql: Consulta SQL a corregir
            
        Returns:
            Consulta SQL corregida
        """
        # Corregir error "mp.user_uuid" -> "mp.user_id"
        sql = sql.replace("mp.user_uuid", "mp.user_id")
        
        # Corregir error "u.id = mp.user_uuid" -> "u.google_id = mp.user_id"
        sql = sql.replace("u.id = mp.user_uuid", "u.google_id = mp.user_id")
        
        # Si hay un JOIN con la tabla users pero no es necesario, simplificarlo
        if "JOIN public.users u" in sql and "u.google_id = %s" in sql:
            # Reemplazar "u.google_id = %s" con "mp.user_id = %s"
            sql = sql.replace("u.google_id = %s", "mp.user_id = %s")
            
            # Eliminar el JOIN con users
            sql = re.sub(r'JOIN public\.users u[^\n]+\n', '', sql)
        
        # Asegurar que siempre incluya "AND mp.is_active = TRUE"
        if "mp.is_active" not in sql and "WHERE" in sql:
            # Agregar la condición después del primer WHERE
            sql = sql.replace("WHERE", "WHERE mp.is_active = TRUE AND ")
        
        return sql
    
    @staticmethod
    def _format_results(results: List[Dict[str, Any]], tipo_consulta: str) -> str:
        """
        Formatea los resultados de la consulta en una respuesta para el usuario.
        
        Args:
            results: Resultados de la consulta SQL
            tipo_consulta: Tipo de consulta (plan_diario, etc.)
            
        Returns:
            Respuesta formateada
        """
        # Obtener el día actual
        current_day = datetime.now().isoweekday()
        day_names = {
            1: "Lunes", 2: "Martes", 3: "Miércoles", 
            4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"
        }
        dia_nombre = day_names.get(current_day, f"Día {current_day}")
        
        if not results:
            return f"No encontré información sobre tu plan nutricional para {dia_nombre}. ¿Quieres que te ayude a crear un plan?"
        
        # Formatear el plan diario
        respuesta = f"## 🍽️ Tu menú para {dia_nombre}\n\n"
        
        # Agrupar por tipo de comida
        meals_by_type = {}
        for item in results:
            meal_type = item.get('meal_type', '').replace('MealTime.', '')
            if meal_type not in meals_by_type:
                meals_by_type[meal_type] = []
            meals_by_type[meal_type].append(item.get('meal_name', 'Comida sin nombre'))
        
        # Mostrar cada tipo de comida
        for meal_type, meals in meals_by_type.items():
            respuesta += f"### {meal_type}\n\n"
            for meal in meals:
                respuesta += f"- {meal}\n"
            respuesta += "\n"
        
        respuesta += "¿Necesitas más detalles sobre alguna comida en particular?"
        return respuesta