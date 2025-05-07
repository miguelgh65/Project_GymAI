# fitness_chatbot/chains/nutrition_chain.py
import logging
import json
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
            user_id: ID del usuario
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
            
            # Extraer el JSON de la respuesta
            sql_data = NutritionChain._extract_sql_from_response(content)
            
            if not sql_data:
                logger.error("No se pudo generar una consulta SQL válida")
                return "Lo siento, no pude entender completamente tu consulta. ¿Podrías reformularla?"
            
            # Ejecutar la consulta SQL
            logger.info(f"Ejecutando SQL: {sql_data['sql']}")
            logger.info(f"Con parámetros: {sql_data['params']}")
            
            # Ejecutar la consulta
            results = await DatabaseConnector.execute_query(
                sql_data["sql"], 
                sql_data["params"],
                fetch_all=True
            )
            
            # Verificar si tenemos resultados
            if not results:
                logger.info("No se encontraron resultados para la consulta")
                return "No encontré información sobre tu plan nutricional para hoy. ¿Quieres crear un nuevo plan?"
            
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
        import re
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
                    # Agregar más parámetros para completar
                    sql_data["params"].extend([None] * (placeholder_count - param_count))
                elif placeholder_count < param_count:
                    # Recortar los parámetros excedentes
                    sql_data["params"] = sql_data["params"][:placeholder_count]
            
            return sql_data
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON de la respuesta del LLM")
            return None
    
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
        
        if tipo_consulta == "plan_diario":
            # Formato para plan alimenticio del día
            return NutritionChain._format_daily_plan(results, dia_nombre)
        elif tipo_consulta == "resumen_plan":
            # Formato para resumen general de un plan
            return NutritionChain._format_plan_summary(results)
        else:
            # Formateo genérico
            return NutritionChain._format_generic_results(results, dia_nombre)
    
    @staticmethod
    def _format_daily_plan(results: List[Dict[str, Any]], dia_nombre: str) -> str:
        """
        Formatea los resultados como un plan diario.
        
        Args:
            results: Resultados de la consulta SQL
            dia_nombre: Nombre del día
            
        Returns:
            Respuesta formateada
        """
        respuesta = f"## 🍽️ Tu plan nutricional para {dia_nombre}\n\n"
        
        # Agrupar por tipo de comida
        meals_by_type = {}
        for item in results:
            meal_type = item.get('meal_type', '').replace('MealTime.', '')
            if meal_type not in meals_by_type:
                meals_by_type[meal_type] = []
            meals_by_type[meal_type].append(item)
        
        # Mostrar cada tipo de comida
        for meal_type, items in meals_by_type.items():
            respuesta += f"### {meal_type}\n\n"
            
            for item in items:
                meal_name = item.get('meal_name', 'Comida sin nombre')
                respuesta += f"- {meal_name}\n"
            
            respuesta += "\n"
        
        return respuesta
    
    @staticmethod
    def _format_plan_summary(results: List[Dict[str, Any]]) -> str:
        """
        Formatea los resultados como un resumen de plan.
        
        Args:
            results: Resultados de la consulta SQL
            
        Returns:
            Respuesta formateada
        """
        respuesta = "## 📊 Resumen de tu plan nutricional\n\n"
        
        if not results:
            return "No tienes ningún plan nutricional configurado actualmente."
        
        # Obtener información del plan
        plan = results[0]
        plan_name = plan.get('plan_name', 'Plan sin nombre')
        is_active = plan.get('is_active', False)
        target_calories = plan.get('target_calories', 0)
        
        respuesta += f"**Plan**: {plan_name}\n"
        respuesta += f"**Estado**: {'Activo' if is_active else 'Inactivo'}\n"
        
        if target_calories:
            respuesta += f"**Calorías objetivo**: {target_calories} kcal\n"
        
        # Si hay macros
        target_protein = plan.get('target_protein_g', 0)
        target_carbs = plan.get('target_carbs_g', 0)
        target_fat = plan.get('target_fat_g', 0)
        
        if any([target_protein, target_carbs, target_fat]):
            respuesta += "\n**Distribución de macronutrientes**:\n"
            if target_protein:
                respuesta += f"- Proteínas: {target_protein}g\n"
            if target_carbs:
                respuesta += f"- Carbohidratos: {target_carbs}g\n"
            if target_fat:
                respuesta += f"- Grasas: {target_fat}g\n"
        
        return respuesta
    
    @staticmethod
    def _format_generic_results(results: List[Dict[str, Any]], dia_nombre: str) -> str:
        """
        Formatea los resultados de manera genérica.
        
        Args:
            results: Resultados de la consulta SQL
            dia_nombre: Nombre del día
            
        Returns:
            Respuesta formateada
        """
        respuesta = f"## 🍽️ Resultados de tu consulta nutricional\n\n"
        
        # Si no hay resultados
        if not results:
            return "No encontré información nutricional para tu consulta."
        
        # Ver qué campos tenemos disponibles en los resultados
        sample = results[0]
        fields = list(sample.keys())
        
        # Mostrar cada registro
        for i, row in enumerate(results, 1):
            respuesta += f"### Resultado {i}\n\n"
            
            for field in fields:
                if field in ['id', 'user_id', 'user_uuid']:
                    continue  # Omitir campos técnicos
                
                value = row.get(field)
                field_name = field.replace('_', ' ').capitalize()
                
                respuesta += f"**{field_name}**: {value}\n"
            
            respuesta += "\n"
        
        return respuesta