import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.db_connector import DatabaseConnector

logger = logging.getLogger("fitness_chatbot")

class FitnessDataService:
    """Servicios para acceder y manipular datos de fitness en la base de datos."""
    
    @staticmethod
    async def get_user_exercises(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los ejercicios recientes de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de ejercicios a devolver
                
        Returns:
            Lista de ejercicios recientes
        """
        try:
            # Mejorar el log para depuración
            logger.info(f"Consultando ejercicios para user_id={user_id}")
            
            # Usar IA para generar la consulta SQL
            llm = get_llm()
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return []
                
            # Preparar prompt para generar consulta SQL usando el sistema history existente
            messages = PromptManager.get_prompt_messages(
                "history",
                query=f"Obtener los últimos {limit} ejercicios del usuario con ID {user_id}",
                user_id=user_id
            )
            
            # Generar consulta SQL con LLM
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extraer SQL y parámetros
            import re
            import json
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No se pudo extraer JSON de la respuesta del LLM")
                return []
                
            try:
                sql_data = json.loads(json_match.group(0))
                if "sql" not in sql_data or "params" not in sql_data:
                    logger.error("JSON extraído no contiene campos sql o params")
                    return []
                    
                sql_query = sql_data["sql"]
                params = sql_data["params"]
            except json.JSONDecodeError:
                logger.error("Error decodificando JSON de la respuesta del LLM")
                return []
                
            # Validar que la consulta no contenga referencias a google_id
            if "google_id" in sql_query:
                logger.warning("La consulta generada contiene referencias a google_id, corrigiendo...")
                sql_query = sql_query.replace("OR google_id = %s", "")
                # Ajustar parámetros si es necesario
                params = [p for p in params if p != user_id]
                params.insert(0, user_id)  # Asegurar que user_id está en los parámetros
                
            logger.info(f"SQL generado: {sql_query}")
            logger.info(f"Parámetros: {params}")
            
            # Ejecutar la consulta generada
            results = await DatabaseConnector.execute_query(
                sql_query, 
                params,
                fetch_all=True
            )
            
            # Log para ver resultados
            if results:
                logger.info(f"Encontrados {len(results)} ejercicios")
            else:
                logger.warning(f"No se encontraron ejercicios para user_id={user_id}")
            
            # Formatear los resultados
            formatted_results = []
            for row in results:
                fecha = row.get('fecha')
                ejercicio = row.get('ejercicio')
                repeticiones = row.get('repeticiones')
                duracion = row.get('duracion')
                
                # Convertir repeticiones de JSON a objeto Python si es necesario
                if repeticiones and isinstance(repeticiones, str):
                    try:
                        repeticiones = json.loads(repeticiones)
                    except json.JSONDecodeError:
                        repeticiones = None
                
                formatted_results.append({
                    "fecha": fecha.isoformat() if isinstance(fecha, datetime) else fecha,
                    "ejercicio": ejercicio,
                    "repeticiones": repeticiones,
                    "duracion": duracion
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error obteniendo ejercicios: {str(e)}")
            return []
    
    @staticmethod
    async def get_user_progress(user_id: str, exercise_name: str) -> List[Dict[str, Any]]:
        """
        Obtiene el progreso de un usuario en un ejercicio específico.
        
        Args:
            user_id: ID del usuario
            exercise_name: Nombre del ejercicio
            
        Returns:
            Lista con historial del ejercicio
        """
        try:
            # Usar IA para generar la consulta SQL
            llm = get_llm()
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return []
                
            # Preparar prompt para generar consulta SQL
            messages = PromptManager.get_prompt_messages(
                "history",
                query=f"Obtener el historial de ejercicio '{exercise_name}' del usuario con ID {user_id} ordenado por fecha",
                user_id=user_id
            )
            
            # Generar consulta SQL con LLM
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extraer SQL y parámetros
            import re
            import json
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No se pudo extraer JSON de la respuesta del LLM")
                return []
                
            try:
                sql_data = json.loads(json_match.group(0))
                if "sql" not in sql_data or "params" not in sql_data:
                    logger.error("JSON extraído no contiene campos sql o params")
                    return []
                    
                sql_query = sql_data["sql"]
                params = sql_data["params"]
            except json.JSONDecodeError:
                logger.error("Error decodificando JSON de la respuesta del LLM")
                return []
                
            # Validar que la consulta no contenga referencias a google_id
            if "google_id" in sql_query:
                logger.warning("La consulta generada contiene referencias a google_id, corrigiendo...")
                sql_query = sql_query.replace("OR google_id = %s", "")
                # Ajustar parámetros para eliminar el parámetro extra
                clean_params = []
                added_user_id = False
                for p in params:
                    if p == user_id and not added_user_id:
                        clean_params.append(p)
                        added_user_id = True
                    elif p != user_id or added_user_id:
                        clean_params.append(p)
                params = clean_params
                
            logger.info(f"SQL generado: {sql_query}")
            logger.info(f"Parámetros: {params}")
            
            # Ejecutar la consulta generada
            results = await DatabaseConnector.execute_query(
                sql_query, 
                params,
                fetch_all=True
            )
            
            # Formatear los resultados
            formatted_results = []
            for row in results:
                fecha = row.get('fecha')
                repeticiones = row.get('repeticiones')
                
                # Convertir repeticiones de JSON a objeto Python
                if repeticiones and isinstance(repeticiones, str):
                    try:
                        repeticiones = json.loads(repeticiones)
                    except json.JSONDecodeError:
                        repeticiones = None
                
                formatted_results.append({
                    "fecha": fecha.isoformat() if isinstance(fecha, datetime) else fecha,
                    "ejercicio": exercise_name,
                    "repeticiones": repeticiones
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error obteniendo progreso: {str(e)}")
            return []
    
    @staticmethod
    async def log_exercise(user_id: str, exercise_name: str, repetitions: List[Dict[str, Any]]) -> bool:
        """
        Registra un ejercicio en la base de datos.
        
        Args:
            user_id: ID del usuario
            exercise_name: Nombre del ejercicio
            repetitions: Lista de series con repeticiones y peso
            
        Returns:
            True si se registró correctamente, False en caso contrario
        """
        try:
            # Usar IA para generar la consulta SQL
            llm = get_llm()
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return False
                
            # Convertir repeticiones a JSON
            repetitions_json = json.dumps(repetitions)
            
            # Preparar prompt para generar consulta SQL
            messages = PromptManager.get_prompt_messages(
                "history",
                query=f"Insertar un nuevo ejercicio '{exercise_name}' para el usuario con ID {user_id} con las siguientes repeticiones: {repetitions_json}",
                user_id=user_id
            )
            
            # Generar consulta SQL con LLM
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extraer SQL y parámetros
            import re
            import json
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No se pudo extraer JSON de la respuesta del LLM")
                return False
                
            try:
                sql_data = json.loads(json_match.group(0))
                if "sql" not in sql_data or "params" not in sql_data:
                    logger.error("JSON extraído no contiene campos sql o params")
                    return False
                    
                sql_query = sql_data["sql"]
                params = sql_data["params"]
            except json.JSONDecodeError:
                logger.error("Error decodificando JSON de la respuesta del LLM")
                return False
                
            # Validar que la consulta no contenga referencias a google_id
            if "google_id" in sql_query:
                logger.warning("La consulta generada contiene referencias a google_id, corrigiendo...")
                sql_query = sql_query.replace(", google_id", "")
                
                # Ajustar los placeholders %s
                count_values = sql_query.count("%s")
                if count_values > len(params):
                    # La consulta tiene más %s que parámetros, reducir un %s
                    pattern = r'\([%s, ]*%s\)'
                    replacement = lambda m: m.group(0).replace("%s, ", "%s, ", 1)
                    sql_query = re.sub(pattern, replacement, sql_query, 1)
                
            logger.info(f"SQL generado: {sql_query}")
            logger.info(f"Parámetros: {params}")
            
            # Sustituir el ejercicio y repeticiones en los parámetros con los valores proporcionados
            for i, param in enumerate(params):
                if param == '%exercise_name%':
                    params[i] = exercise_name
                elif param == '%repetitions_json%':
                    params[i] = repetitions_json
            
            logger.info(f"Parámetros procesados: {params}")
            
            # Ejecutar la consulta generada
            await DatabaseConnector.execute_query(
                sql_query,
                params
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error registrando ejercicio: {str(e)}")
            return False
    
    @staticmethod
    async def get_user_nutrition_data(user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Obtiene los datos nutricionales recientes de un usuario.
        
        Args:
            user_id: ID del usuario
            days: Número de días hacia atrás para buscar
            
        Returns:
            Lista de registros nutricionales
        """
        try:
            # Usar IA para generar la consulta SQL
            llm = get_llm()
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return []
                
            # Preparar prompt para generar consulta SQL
            messages = PromptManager.get_prompt_messages(
                "history",
                query=f"Obtener datos nutricionales de los últimos {days} días para el usuario con ID {user_id} de la tabla nutrition.daily_tracking",
                user_id=user_id
            )
            
            # Generar consulta SQL con LLM
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extraer SQL y parámetros
            import re
            import json
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No se pudo extraer JSON de la respuesta del LLM")
                return []
                
            try:
                sql_data = json.loads(json_match.group(0))
                if "sql" not in sql_data or "params" not in sql_data:
                    logger.error("JSON extraído no contiene campos sql o params")
                    return []
                    
                sql_query = sql_data["sql"]
                params = sql_data["params"]
            except json.JSONDecodeError:
                logger.error("Error decodificando JSON de la respuesta del LLM")
                return []
                
            # Validar que la consulta no contenga referencias a google_id
            if "google_id" in sql_query:
                logger.warning("La consulta generada contiene referencias a google_id, corrigiendo...")
                sql_query = sql_query.replace("OR google_id = %s", "")
                # Ajustar parámetros para eliminar el parámetro extra
                clean_params = []
                added_user_id = False
                for p in params:
                    if p == user_id and not added_user_id:
                        clean_params.append(p)
                        added_user_id = True
                    elif p != user_id or added_user_id:
                        clean_params.append(p)
                params = clean_params
                
            logger.info(f"SQL generado: {sql_query}")
            logger.info(f"Parámetros: {params}")
            
            # Ejecutar la consulta generada
            results = await DatabaseConnector.execute_query(
                sql_query, 
                params,
                fetch_all=True
            )
            
            # Formatear los resultados
            formatted_results = []
            for row in results:
                tracking_date = row.get('tracking_date')
                completed_meals = row.get('completed_meals')
                calorie_note = row.get('calorie_note')
                actual_calories = row.get('actual_calories')
                actual_protein = row.get('actual_protein')
                
                # Convertir completed_meals de JSON a objeto Python
                if completed_meals and isinstance(completed_meals, str):
                    try:
                        completed_meals = json.loads(completed_meals)
                    except json.JSONDecodeError:
                        completed_meals = {}
                
                formatted_results.append({
                    "tracking_date": tracking_date.isoformat() if isinstance(tracking_date, datetime) else tracking_date,
                    "completed_meals": completed_meals,
                    "calorie_note": calorie_note,
                    "actual_calories": actual_calories,
                    "actual_protein": actual_protein
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error obteniendo datos nutricionales: {str(e)}")
            return []
    
    @staticmethod
    async def log_nutrition(
        user_id: str, 
        meal_type: str, 
        foods: List[str], 
        calories: Optional[int] = None,
        protein: Optional[int] = None
    ) -> bool:
        """
        Registra información nutricional en la base de datos.
        
        Args:
            user_id: ID del usuario
            meal_type: Tipo de comida (desayuno, almuerzo, cena, etc.)
            foods: Lista de alimentos
            calories: Calorías totales (opcional)
            protein: Proteína en gramos (opcional)
            
        Returns:
            True si se registró correctamente, False en caso contrario
        """
        try:
            # Usar IA para generar la consulta SQL
            llm = get_llm()
            if not llm:
                logger.error("LLM no disponible para generar consulta SQL")
                return False
                
            # Crear objeto JSON con la información de la comida
            completed_meals_json = json.dumps({
                meal_type.lower(): True
            })
            
            # Crear nota con los alimentos
            calorie_note = ", ".join(foods) if foods else None
            
            # Preparar prompt para generar consulta SQL
            messages = PromptManager.get_prompt_messages(
                "history",
                query=f"Registrar comida de tipo '{meal_type}' para el usuario con ID {user_id} en la tabla nutrition.daily_tracking con la nota '{calorie_note}', calorías {calories} y proteínas {protein}",
                user_id=user_id
            )
            
            # Generar consulta SQL con LLM
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extraer SQL y parámetros
            import re
            import json
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No se pudo extraer JSON de la respuesta del LLM")
                return False
                
            try:
                sql_data = json.loads(json_match.group(0))
                if "sql" not in sql_data or "params" not in sql_data:
                    logger.error("JSON extraído no contiene campos sql o params")
                    return False
                    
                sql_query = sql_data["sql"]
                params = sql_data["params"]
            except json.JSONDecodeError:
                logger.error("Error decodificando JSON de la respuesta del LLM")
                return False
                
            # Validar que la consulta no contenga referencias a google_id
            if "google_id" in sql_query:
                logger.warning("La consulta generada contiene referencias a google_id, corrigiendo...")
                sql_query = sql_query.replace(", google_id", "")
                
                # Ajustar los placeholders %s
                count_values = sql_query.count("%s")
                if count_values > len(params):
                    # La consulta tiene más %s que parámetros, reducir un %s
                    pattern = r'\([%s, ]*%s\)'
                    replacement = lambda m: m.group(0).replace("%s, ", "%s, ", 1)
                    sql_query = re.sub(pattern, replacement, sql_query, 1)
                
            logger.info(f"SQL generado: {sql_query}")
            logger.info(f"Parámetros originales: {params}")
            
            # Sustituir valores en los parámetros
            processed_params = []
            for param in params:
                if param == '%user_id%':
                    processed_params.append(user_id)
                elif param == '%completed_meals%':
                    processed_params.append(completed_meals_json)
                elif param == '%calorie_note%':
                    processed_params.append(calorie_note)
                elif param == '%calories%':
                    processed_params.append(calories)
                elif param == '%protein%':
                    processed_params.append(protein)
                else:
                    processed_params.append(param)
            
            logger.info(f"Parámetros procesados: {processed_params}")
            
            # Ejecutar la consulta generada
            await DatabaseConnector.execute_query(
                sql_query,
                processed_params
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error registrando información nutricional: {str(e)}")
            return False