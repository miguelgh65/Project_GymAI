import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from fitness_chatbot.core.db_connector import DatabaseConnector

logger = logging.getLogger("fitness_chatbot")

class FitnessDataService:
    """Servicios para acceder y manipular datos de fitness en la base de datos."""
    
    @staticmethod
    async def get_user_exercises(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los ejercicios recientes de un usuario.
        
        Args:
            user_id: ID del usuario (debería ser Google ID principalmente)
            limit: Número máximo de ejercicios a devolver
                
        Returns:
            Lista de ejercicios recientes
        """
        try:
            # Mejorar el log para depuración
            logger.info(f"Consultando ejercicios para user_id={user_id}")
            
            # Consulta original con una cláusula adicional para buscar en google_id
            query = """
            SELECT fecha, ejercicio, repeticiones, duracion
            FROM gym.ejercicios
            WHERE user_id = %s OR user_uuid = %s OR google_id = %s
            ORDER BY fecha DESC
            LIMIT %s
            """
            
            # Intentar convertir user_id a int por si es un ID interno
            user_uuid = None
            try:
                user_uuid = int(user_id)
            except (ValueError, TypeError):
                pass
            
            # Log para ver los parámetros de búsqueda
            logger.info(f"Parámetros de búsqueda: user_id={user_id}, user_uuid={user_uuid}, google_id={user_id}")
            
            results = await DatabaseConnector.execute_query(
                query, 
                (user_id, user_uuid, user_id, limit),  # user_id se usa también como google_id
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
            query = """
            SELECT fecha, repeticiones
            FROM gym.ejercicios
            WHERE (user_id = %s OR user_uuid = %s OR google_id = %s) AND LOWER(ejercicio) = LOWER(%s)
            ORDER BY fecha
            """
            
            # Intentar convertir user_id a int por si es un ID interno
            user_uuid = None
            try:
                user_uuid = int(user_id)
            except (ValueError, TypeError):
                pass
            
            results = await DatabaseConnector.execute_query(
                query, 
                (user_id, user_uuid, user_id, exercise_name),  # Añadido google_id
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
            # Convertir repeticiones a JSON
            repetitions_json = json.dumps(repetitions)
            
            # Intentar convertir user_id a int para user_uuid
            user_uuid = None
            try:
                user_uuid = int(user_id)
            except (ValueError, TypeError):
                pass
            
            query = """
            INSERT INTO gym.ejercicios (fecha, ejercicio, repeticiones, user_id, user_uuid, google_id)
            VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
            """
            
            await DatabaseConnector.execute_query(
                query,
                (exercise_name, repetitions_json, user_id, user_uuid, user_id)  # Añadido google_id
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
            query = """
            SELECT tracking_date, completed_meals, calorie_note, actual_calories, actual_protein
            FROM nutrition.daily_tracking
            WHERE user_id = %s OR google_id = %s
              AND tracking_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY tracking_date DESC
            """
            
            results = await DatabaseConnector.execute_query(
                query, 
                (user_id, user_id, days),  # Añadido google_id
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
            # Crear objeto JSON con la información de la comida
            completed_meals = {
                meal_type.lower(): True
            }
            
            query = """
            INSERT INTO nutrition.daily_tracking 
            (user_id, google_id, tracking_date, completed_meals, calorie_note, actual_calories, actual_protein)
            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s)
            ON CONFLICT (user_id, tracking_date) 
            DO UPDATE SET 
                completed_meals = nutrition.daily_tracking.completed_meals || %s,
                calorie_note = CASE WHEN %s IS NOT NULL THEN %s ELSE nutrition.daily_tracking.calorie_note END,
                actual_calories = CASE WHEN %s IS NOT NULL THEN %s ELSE nutrition.daily_tracking.actual_calories END,
                actual_protein = CASE WHEN %s IS NOT NULL THEN %s ELSE nutrition.daily_tracking.actual_protein END,
                updated_at = CURRENT_TIMESTAMP
            """
            
            # Crear nota con los alimentos
            calorie_note = ", ".join(foods) if foods else None
            
            await DatabaseConnector.execute_query(
                query,
                (
                    user_id, user_id, json.dumps(completed_meals), calorie_note, calories, protein,
                    json.dumps(completed_meals), calorie_note, calorie_note, calories, calories, protein, protein
                )  # Añadido google_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error registrando información nutricional: {str(e)}")
            return False