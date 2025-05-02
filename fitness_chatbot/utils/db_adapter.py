# fitness_chatbot/utils/db_adapter.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("fitness_chatbot")

class ExerciseDBAdapter:
    """
    Adaptador para convertir los datos del chatbot al formato esperado por la base de datos.
    """
    
    @staticmethod
    def format_for_db(exercise_name: str, sets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convierte los datos de ejercicio al formato esperado por la tabla 'ejercicios'.
        
        Args:
            exercise_name: Nombre del ejercicio
            sets: Lista de series con repeticiones y pesos
            
        Returns:
            Dict con el formato correcto para la BD
        """
        # Asegurarse de que todos los conjuntos tienen el formato esperado
        formatted_sets = []
        for s in sets:
            formatted_sets.append({
                "repeticiones": int(s.get("reps", 0)),
                "peso": float(s.get("weight", 0))
            })
        
        # Crear el formato JSON esperado por la tabla ejercicios
        return {
            "ejercicio": exercise_name,
            "repeticiones": formatted_sets,
            "fecha": datetime.now().isoformat()
        }
    
    @staticmethod
    def adapt_sets_from_llm(sets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adapta el formato de conjuntos (sets) del LLM al formato esperado por la BD.
        
        Args:
            sets_data: Lista de conjuntos en formato LLM
            
        Returns:
            Lista de conjuntos en formato BD
        """
        adapted_sets = []
        for s in sets_data:
            try:
                # Asegurar que tenemos valores numéricos válidos
                reps = int(s.get("reps", 0))
                weight = float(s.get("weight", 0))
                
                # Convertir al formato esperado por la BD
                adapted_sets.append({
                    "repeticiones": reps,
                    "peso": weight
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error adaptando conjunto: {e}. Datos: {s}")
                # Usar valores por defecto en caso de error
                adapted_sets.append({
                    "repeticiones": 0,
                    "peso": 0
                })
        
        return adapted_sets
    
    @staticmethod
    def extract_exercise_details(text: str) -> Optional[Dict[str, Any]]:
        """
        Extrae detalles de ejercicio de texto plano usando reglas simples.
        Función alternativa a format_for_postgres.
        
        Args:
            text: Texto con descripción del ejercicio
            
        Returns:
            Dict con ejercicio y repeticiones formateados para BD
        """
        from fitness_chatbot.nodes.log_activity_node import extract_exercise_info
        
        try:
            # Usar la función extract_exercise_info del nodo de log_activity
            exercise_info = extract_exercise_info(text)
            
            if not exercise_info or not exercise_info["exercise_name"]:
                logger.warning(f"No se pudo extraer nombre de ejercicio de: {text}")
                return None
            
            # Adaptar los conjuntos al formato esperado
            formatted_sets = ExerciseDBAdapter.adapt_sets_from_llm(exercise_info["sets"])
            
            if not formatted_sets:
                logger.warning(f"No se pudieron extraer series del ejercicio: {text}")
                # Usar un conjunto por defecto si no se detectaron
                formatted_sets = [{"repeticiones": 10, "peso": 0}]
            
            # Crear estructura final
            return {
                "ejercicio": exercise_info["exercise_name"],
                "repeticiones": formatted_sets,
                "fecha": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error extrayendo detalles del ejercicio: {e}")
            return None
    
    @staticmethod
    def normalize_exercise_name(name: str) -> str:
        """
        Normaliza el nombre del ejercicio para consistencia en la BD.
        
        Args:
            name: Nombre del ejercicio
            
        Returns:
            Nombre normalizado
        """
        if not name:
            return "desconocido"
        
        # Mapa de normalización - añade aquí más términos según necesites
        normalization_map = {
            "press de banca": "press banca",
            "press banco": "press banca",
            "bench press": "press banca",
            "sentadilla": "sentadillas",
            "squad": "sentadillas",
            "squat": "sentadillas",
            "peso muerto": "peso muerto",
            "deadlift": "peso muerto",
            "dominada": "dominadas",
            "chin up": "dominadas",
            "pull up": "dominadas",
            "press militar": "press militar",
            "military press": "press militar",
            "curl biceps": "curl de bíceps",
            "bicep curl": "curl de bíceps",
            "curl de biceps": "curl de bíceps",
            "extensiones de triceps": "extensiones de tríceps",
            "tricep extension": "extensiones de tríceps",
            "fondos": "fondos",
            "dips": "fondos",
            "elevaciones laterales": "elevaciones laterales",
            "lateral raise": "elevaciones laterales"
        }
        
        # Buscar coincidencias exactas primero
        if name.lower() in normalization_map:
            return normalization_map[name.lower()]
        
        # Buscar coincidencias parciales
        for key, normalized in normalization_map.items():
            if key in name.lower():
                return normalized
        
        # Si no hay coincidencias, devolver el nombre original
        return name.lower()