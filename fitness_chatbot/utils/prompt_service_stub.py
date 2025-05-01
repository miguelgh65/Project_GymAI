# fitness_chatbot/utils/prompt_service_stub.py
import logging
import json
import re
from typing import Dict, Any, Optional

logger = logging.getLogger("fitness_chatbot")

def format_for_postgres(exercise_text: str) -> Optional[Dict[str, Any]]:
    """
    Versión alternativa de format_for_postgres cuando no se puede importar
    la versión del backend. Extrae información de ejercicios de texto plano
    y la estructura en formato JSON para insertar en PostgreSQL.
    
    Args:
        exercise_text: Texto con descripción del ejercicio
        
    Returns:
        Dict con los datos estructurados o None si no se puede parsear
    """
    logger.info(f"Usando función stub format_for_postgres para: {exercise_text[:50]}...")
    
    try:
        # Crear un patrón básico para identificar ejercicios
        exercise_pattern = re.compile(r'([\w\s]+)(?::|,)\s*(?:(\d+)\s*(?:series|sets))?(?:\s*de\s*)?(\d+)?\s*(?:reps|repeticiones)?(?:\s*con\s*)?(?:(\d+(?:\.\d+)?)\s*(?:kg|kilos))?', re.IGNORECASE)
        
        # Extraer ejercicio, series, repeticiones y peso
        match = exercise_pattern.search(exercise_text)
        
        if not match:
            logger.warning(f"No se pudo extraer información de ejercicio de: {exercise_text}")
            return None
        
        # Extraer componentes
        exercise_name = match.group(1).strip().lower() if match.group(1) else "desconocido"
        sets_count = int(match.group(2)) if match.group(2) else 1
        reps_count = int(match.group(3)) if match.group(3) else 0
        weight = float(match.group(4)) if match.group(4) else 0
        
        # Crear estructura de series
        repetitions = []
        for _ in range(sets_count):
            repetitions.append({
                "repeticiones": reps_count,
                "peso": weight
            })
        
        # Formato JSON esperado por la base de datos
        formatted_json = {
            "ejercicio": exercise_name,
            "repeticiones": repetitions
        }
        
        return formatted_json
    
    except Exception as e:
        logger.error(f"Error en format_for_postgres stub: {str(e)}")
        return None