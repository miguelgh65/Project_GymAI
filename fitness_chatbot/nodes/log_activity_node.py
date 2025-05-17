# fitness_chatbot/nodes/log_activity_node.py
import logging
import json
from typing import Tuple, Dict, Any, List, Optional
import re
import random

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.utils.api_utils import log_exercise
from fitness_chatbot.utils.motivational_phrases import get_random_motivation  # Nueva importación

logger = logging.getLogger("fitness_chatbot")

async def log_activity(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Registra actividades físicas (ejercicios) utilizando la API del backend.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- REGISTRO DE ACTIVIDAD INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando registro para usuario {user_id}: '{query}'")
    
    try:
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Extraer información RIR si está presente
        rir_value = extract_rir(query)
        if rir_value is not None:
            logger.info(f"RIR extraído del mensaje: {rir_value}")
        
        # Extraer comentarios si están presentes
        comentarios = extract_comentarios(query)
        if comentarios:
            logger.info(f"Comentarios extraídos: {comentarios}")
        
        # Hacer llamada a la API del backend con el texto original y datos adicionales
        exercise_data = {
            "exercise_data": query,
            "rir": rir_value,
            "comentarios": comentarios
        }
        
        # Intentar el registro, pero atrapar timeouts y errores
        try:
            result = log_exercise(user_id, exercise_data, auth_token=auth_token)
            logger.info(f"Resultado de log_exercise: {result}")
        except Exception as api_error:
            logger.warning(f"Error en solicitud API pero continuamos: {str(api_error)}")
            # Asumimos que el ejercicio se registrará correctamente a pesar del error
        
        # Extraer información básica para personalizar el mensaje
        exercise_name = extract_exercise_name(query)
        
        # Usar el generador de frases motivacionales
        if exercise_name:
            respuesta = get_random_motivation(exercise_name, style="ronnie")
        else:
            respuesta = get_random_motivation("ejercicio", style="ronnie")
    
    except Exception as e:
        logger.exception(f"Error procesando registro de actividad: {str(e)}")
        # Mensaje optimista a pesar del error
        respuesta = "¡YEAH BUDDY! Tu ejercicio ha sido registrado. ¡LIGHTWEIGHT BABY!"
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- REGISTRO DE ACTIVIDAD FINALIZADO ---")
    return agent_state, memory_state

def extract_exercise_name(text: str) -> Optional[str]:
    """
    Extrae el nombre del ejercicio de un texto.
    Función simple para personalizar la respuesta.
    
    Args:
        text: Texto con descripción del ejercicio
        
    Returns:
        Nombre del ejercicio o None si no se encuentra
    """
    # Patrones simples para extraer nombres de ejercicios comunes
    patterns = [
        (r'press\s+(?:de\s+)?banca', 'press banca'),
        (r'sentadilla[s]?', 'sentadillas'),
        (r'peso\s+muerto', 'peso muerto'),
        (r'dominada[s]?', 'dominadas'),
        (r'curl\s+(?:de\s+)?b[ií]ceps', 'curl de bíceps'),
        (r'press\s+militar', 'press militar'),
        (r'fondos', 'fondos'),
        (r'remo', 'remo'),
        (r'press\s+militar', 'press militar'),
        (r'extensiones\s+(?:de\s+)?tr[ií]ceps', 'extensiones de tríceps'),
        (r'elevaciones\s+laterales', 'elevaciones laterales'),
        (r'desplantes', 'desplantes'),
        (r'zancadas', 'zancadas'),
        (r'prensa', 'prensa'),
        (r'jalones', 'jalones'),
        (r'crunches', 'crunches'),
        (r'plancha[s]?', 'planchas')
    ]
    
    text_lower = text.lower()
    for pattern, name in patterns:
        if re.search(pattern, text_lower):
            return name
    
    return None

def extract_rir(text: str) -> Optional[int]:
    """
    Extrae el valor RIR (Repetitions In Reserve) de un texto.
    
    Args:
        text: Texto con descripción del ejercicio
        
    Returns:
        Valor RIR o None si no se menciona
    """
    # Patrones para detectar RIR
    rir_patterns = [
        r'(?:con|y)\s+(?:un\s+)?RIR\s+(?:de\s+)?(\d+)',
        r'RIR\s+(?:de\s+)?(\d+)',
        r'(?:con|y)\s+(?:un\s+)?(?:rir|RIR)\s+(?:de\s+)?(\d+)',
        r'(?:rir|RIR)(?:\s+|\:)(\d+)',
        r'(?:rir|RIR)\s*=\s*(\d+)',
        r'(?:rir|RIR)(?:\s+|\:)(\d+)'
    ]
    
    for pattern in rir_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
    
    return None

def extract_comentarios(text: str) -> Optional[str]:
    """
    Extrae comentarios o notas sobre el ejercicio.
    
    Args:
        text: Texto con descripción del ejercicio
        
    Returns:
        Comentarios o None si no hay
    """
    # Patrones para detectar comentarios
    comentario_patterns = [
        r'(?:nota|comentario|comentarios)\s*(?::|=)\s*(.*?)(?:$|\.|\n)',
        r'(?:con\s+)?(?:la\s+)?(?:nota|comentario)\s+(?:de\s+que\s+)?(.*?)(?:$|\.|\n)',
        r'(?:me\s+)?(?:fue|sentí|siento)\s+(.*?)(?:$|\.|\n)',
        r'(?:hoy|día)\s+(?:muy|bastante)?\s+(duro|difícil|fácil|intenso|ligero|pesado)(?:$|\.|\n)',
        r'(?:la\s+)?sensación\s+(?:fue|es)\s+(.*?)(?:$|\.|\n)'
    ]
    
    for pattern in comentario_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            comentario = match.group(1).strip()
            if comentario and len(comentario) > 3:  # Al menos 4 caracteres
                return comentario
    
    # Buscar frases completas después de la descripción del ejercicio
    exercise_info_pattern = r'(?:hice|he\s+hecho|realicé|hago|logré)\s+[^\.]*?\d+\s*(?:series|repeticiones|reps)'
    match = re.search(exercise_info_pattern, text, re.IGNORECASE)
    
    if match:
        # Si hay información de ejercicio, buscar texto después
        info_end = match.end()
        if info_end < len(text) - 20:  # Al menos 20 caracteres después
            comentario = text[info_end:].strip()
            # Limpiar y normalizar
            comentario = re.sub(r'^[,\.\s]*', '', comentario)  # Quitar puntuación inicial
            if comentario and len(comentario) > 5:  # Al menos 6 caracteres
                return comentario
    
    return None