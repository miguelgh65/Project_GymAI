# fitness_chatbot/chains/nutrition_chain.py
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.db_connector import DatabaseConnector

logger = logging.getLogger("fitness_chatbot")

class NutritionChain:
    """Cadena para procesar consultas sobre nutrición y planes alimenticios."""
    
    @staticmethod
    async def process_query(user_id: str, query: str) -> str:
        """Procesa una consulta sobre nutrición y devuelve una respuesta formateada."""
        logger.info(f"NutritionChain procesando: '{query}' para usuario {user_id}")
        
        try:
            # Obtener LLM
            llm = get_llm()
            
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return "Lo siento, no puedo procesar tu consulta en este momento. Por favor, intenta más tarde."
            
            # Calcular el día correctamente
            query_lower = query.lower()
            if "mañana" in query_lower:
                # Mañana = día actual + 1
                current_day = (datetime.now() + timedelta(days=1)).isoweekday()
                query_type = "mañana"
            else:
                # Hoy = día actual
                current_day = datetime.now().isoweekday()
                query_type = "hoy"
            
            # Ajustar día 8 a día 1 (si es domingo+1=lunes)
            if current_day > 7:
                current_day = 1
            
            # Mapear días
            day_names = {
                1: "Lunes", 2: "Martes", 3: "Miércoles", 
                4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"
            }
            day_name = day_names.get(current_day, f"Día {current_day}")
            
            # Preparar user_context y variables para el prompt
            user_context = f"El usuario {user_id} quiere consultar su plan nutricional para {query_type}"
            
            # Usar el LLM para generar la consulta SQL
            messages = PromptManager.get_prompt_messages(
                "nutrition", 
                query=query,
                user_context=user_context,
                user_id=user_id,
                current_day=current_day,  # Pasamos el día actual
                day_name=day_name         # Pasamos el nombre del día
            )
            
            # Invocar el LLM
            logger.info("Generando consulta SQL mediante LLM")
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Log completo para debug
            logger.info(f"Respuesta completa del LLM: {content}")
            
            # Extraer el JSON de la respuesta
            sql_data = NutritionChain._extract_sql_from_response(content)
            
            # Si no se pudo extraer SQL válido, usar uno predefinido
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
                    "params": [user_id, current_day],  # Usar como INTEGER directamente
                    "tipo_consulta": "plan_diario"
                }
            else:
                # Asegurar que los parámetros usan el día actual y el user_id correcto
                corrected_params = []
                for param in sql_data["params"]:
                    if param == "user_id_value" or param == "{user_id}":
                        corrected_params.append(user_id)
                    else:
                        # Usar el parámetro tal cual, el LLM debería generar el día correcto ahora
                        corrected_params.append(param)
                
                sql_data["params"] = corrected_params
                
                # Corregir errores comunes en SQL
                sql_data["sql"] = NutritionChain._correct_common_sql_errors(sql_data["sql"])
            
            # Ejecutar la consulta SQL
            logger.info(f"Ejecutando SQL: {sql_data['sql']}")
            logger.info(f"Con parámetros: {sql_data['params']}")
            
            try:
                results = await DatabaseConnector.execute_query(
                    sql_data["sql"], 
                    sql_data["params"],
                    fetch_all=True
                )
                
                # Log de resultados para debug
                logger.info(f"Resultados obtenidos: {len(results)} filas")
                if results:
                    for i, row in enumerate(results):
                        logger.info(f"Fila {i+1}: {row}")
                
            except Exception as e:
                # Fallback con consulta simplificada
                logger.error(f"Error ejecutando la consulta: {str(e)}")
                logger.info("Intentando con consulta SQL de respaldo")
                
                # Consulta básica
                backup_sql = """
                SELECT mpi.meal_type, m.meal_name, mpi.day_of_week
                FROM nutrition.meal_plans mp
                JOIN nutrition.meal_plan_items mpi ON mpi.meal_plan_id = mp.id
                JOIN nutrition.meals m ON mpi.meal_id = m.id
                WHERE mp.user_id = %s AND mp.is_active = TRUE
                  AND mpi.day_of_week = %s
                """
                backup_params = [user_id, current_day]
                
                try:
                    results = await DatabaseConnector.execute_query(
                        backup_sql, 
                        backup_params,
                        fetch_all=True
                    )
                except Exception as backup_error:
                    logger.error(f"Error ejecutando consulta de respaldo: {str(backup_error)}")
                    return "Lo siento, tuve un problema al obtener la información sobre tu plan nutricional. Por favor, intenta de nuevo más tarde."
            
            # Formatear los resultados con el día correcto
            return NutritionChain._format_results(results, day_name, query_type)
        
        except Exception as e:
            logger.exception(f"Error en NutritionChain: {str(e)}")
            return "Lo siento, tuve un problema al procesar tu consulta. Por favor, intenta de nuevo más tarde."
    
    @staticmethod
    def _extract_sql_from_response(content: str) -> Optional[Dict[str, Any]]:
        """Extrae la consulta SQL y los parámetros del contenido generado por el LLM."""
        # Buscar un objeto JSON en la respuesta
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if not json_match:
            logger.warning("No se encontró JSON en la respuesta del LLM")
            
            # Intentar extraer SQL y params de manera más flexible
            sql_match = re.search(r'```sql\s*(.*?)\s*```', content, re.DOTALL)
            if sql_match:
                sql = sql_match.group(1).strip()
                logger.info(f"SQL extraído de la respuesta: {sql}")
                
                # Crear objeto SQL manualmente
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
        """Corrige errores comunes en la consulta SQL generada."""
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
        
        # Asegurar que siempre incluye "AND mp.is_active = TRUE"
        if "mp.is_active" not in sql and "WHERE" in sql:
            # Agregar la condición después del primer WHERE
            sql = sql.replace("WHERE", "WHERE mp.is_active = TRUE AND ")
        
        return sql
    
    @staticmethod
    def _format_results(results: List[Dict[str, Any]], day_name: str, query_type: str) -> str:
        """Formatea los resultados de la consulta en una respuesta para el usuario."""
        
        # LOG: Mostrar resultados recibidos
        logger.info(f"Formateando {len(results)} resultados para {day_name}")
        for i, result in enumerate(results):
            logger.info(f"Resultado {i+1}: {result}")
        
        if not results:
            # Respuesta mejorada cuando no hay datos
            tiempo = "mañana" if query_type == "mañana" else "hoy"
            respuesta = f"🍽️ **No encuentro tu plan nutricional para {tiempo} ({day_name})**\n\n"
            respuesta += "Esto puede deberse a:\n"
            respuesta += f"• No tienes comidas programadas para {tiempo}\n"
            respuesta += "• Tu plan no está activo\n\n"
            respuesta += "**¿Te gustaría que...**\n"
            respuesta += f"1. ✨ Te sugiera comidas saludables para {tiempo}\n"
            respuesta += "2. 📋 Te muestre un plan de comidas ejemplo\n"
            respuesta += "3. 📝 Configure un plan nutricional personalizado\n\n"
            respuesta += "Solo dime qué prefieres y te ayudo 😊"
            return respuesta
        
        # Formatear el plan diario
        respuesta = f"## 🍽️ Tu menú para {day_name}\n\n"
        
        # Agrupar por tipo de comida
        meals_by_type = {}
        for item in results:
            meal_type = item.get('meal_type', '').replace('MealTime.', '')
            meal_name = item.get('meal_name', 'Comida sin nombre')
            
            if meal_type not in meals_by_type:
                meals_by_type[meal_type] = []
            
            # Evitar duplicados
            if meal_name not in meals_by_type[meal_type]:
                meals_by_type[meal_type].append(meal_name)
        
        # LOG: Mostrar agrupamiento
        logger.info(f"Comidas agrupadas por tipo: {meals_by_type}")
        
        # Agregar emojis para cada tipo de comida
        meal_type_emojis = {
            'Desayuno': '🌅',
            'Almuerzo': '🌞',
            'Merienda': '☕',
            'Cena': '🌜',
            'Snack': '🍎'
        }
        
        # Ordenar los tipos de comida en orden lógico
        meal_order = ['Desayuno', 'Almuerzo', 'Merienda', 'Cena', 'Snack']
        
        # Mostrar cada tipo de comida en orden
        for meal_type in meal_order:
            if meal_type in meals_by_type:
                emoji = meal_type_emojis.get(meal_type, '🍴')
                respuesta += f"### {emoji} {meal_type}\n\n"
                for meal in meals_by_type[meal_type]:
                    respuesta += f"• **{meal}**\n"
                respuesta += "\n"
        
        # Agregar sugerencias adicionales
        respuesta += "💡 **Consejos:**\n"
        respuesta += "• Mantente hidratado durante el día\n"
        respuesta += "• Puedes sustituir si necesitas\n"
        respuesta += "• ¿Quieres ver las calorías?\n\n"
        respuesta += "¿Necesitas más detalles?"
        return respuesta