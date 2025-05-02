# fitness_chatbot/nodes/log_activity_node.py
import logging
import json
from typing import Tuple, Dict, Any, List, Optional
import re

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.utils.prompt_service_stub import format_for_postgres
from fitness_chatbot.utils.api_utils import log_exercise
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.configs.llm_config import get_llm

logger = logging.getLogger("fitness_chatbot")

def extract_exercise_info(text: str) -> Dict[str, Any]:
    """
    Extrae información de ejercicio desde texto plano.
    
    Args:
        text: Texto con descripción del ejercicio
        
    Returns:
        Dict con información extraída (exercise_name, sets)
    """
    exercise_info = {
        "exercise_name": "",
        "sets": []
    }
    
    # Patrones para detectar nombres de ejercicios comunes
    exercise_patterns = [
        r'(press\s+(?:de\s+)?banca|sentadilla[s]?|peso\s+muerto|dominada[s]?|curl\s+(?:de\s+)?b[ií]ceps|press\s+militar|fondos|elevaciones|remo|extensiones)',
        r'(squat|bench\s+press|deadlift|pull[- ]up|chin[- ]up|bicep[s]?\s+curl|dips|lateral\s+raise|row)',
    ]
    
    # Detectar ejercicio
    for pattern in exercise_patterns:
        match = re.search(pattern, text.lower())
        if match:
            exercise_info["exercise_name"] = match.group(1)
            break
    
    # Si no se detectó ejercicio, intentar extraer cualquier sustantivo antes de números
    if not exercise_info["exercise_name"]:
        noun_match = re.search(r'([a-zñáéíóúü]+(?:\s+[a-zñáéíóúü]+){0,3})\s+(?:\d|series|repeticiones)', text.lower())
        if noun_match:
            exercise_info["exercise_name"] = noun_match.group(1).strip()
    
    # Patrones para detectar series y repeticiones
    set_patterns = [
        # 3x10 (3 series de 10 repeticiones)
        r'(\d+)\s*[xX]\s*(\d+)(?:\s*[xX]\s*(\d+))?',
        # 3 series de 10 repeticiones
        r'(\d+)\s+series\s+(?:de\s+)?(\d+)\s+repeticiones',
        # 10 repeticiones con 60kg
        r'(\d+)\s+repeticiones\s+(?:con\s+)?(\d+(?:\.\d+)?)',
        # series individuales: 10, 8, 6 repeticiones
        r'(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+))?\s+repeticiones',
        # 60kg x 10 repeticiones
        r'(\d+(?:\.\d+)?)\s*kg\s*[xX]\s*(\d+)',
    ]
    
    # Detectar todas las ocurrencias de pesos
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', text.lower())
    weight = float(weight_match.group(1)) if weight_match else 0
    
    # Buscar patrones de series
    for pattern in set_patterns:
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            if "series" in pattern and match.group(1) and match.group(2):
                # Patrón: 3 series de 10 repeticiones
                num_sets = int(match.group(1))
                reps = int(match.group(2))
                
                for _ in range(num_sets):
                    exercise_info["sets"].append({"reps": reps, "weight": weight})
                break
                
            elif "x" in pattern.lower() and match.group(1) and match.group(2):
                # Patrón: 3x10 o 3x10x60
                if match.group(3):  # Tiene 3 valores (series x reps x peso)
                    num_sets = int(match.group(1))
                    reps = int(match.group(2))
                    weight = float(match.group(3))
                    
                    for _ in range(num_sets):
                        exercise_info["sets"].append({"reps": reps, "weight": weight})
                else:  # Tiene 2 valores (series x reps)
                    num_sets = int(match.group(1))
                    reps = int(match.group(2))
                    
                    for _ in range(num_sets):
                        exercise_info["sets"].append({"reps": reps, "weight": weight})
                break
            
            elif "repeticiones" in pattern and match.group(1):
                # Varios patrones con repeticiones
                if "," in pattern:
                    # Series individuales: 10, 8, 6 repeticiones
                    for i in range(1, 5):
                        if match.group(i):
                            reps = int(match.group(i))
                            exercise_info["sets"].append({"reps": reps, "weight": weight})
                else:
                    # 10 repeticiones con 60kg o similar
                    reps = int(match.group(1))
                    if match.group(2) and "con" in text.lower():
                        weight = float(match.group(2))
                    
                    exercise_info["sets"].append({"reps": reps, "weight": weight})
                break
    
    # Si no se detectaron series pero sí un ejercicio, añadir serie por defecto
    if exercise_info["exercise_name"] and not exercise_info["sets"]:
        exercise_info["sets"].append({"reps": 10, "weight": 0})  # Serie por defecto
    
    # Normalizar nombre del ejercicio
    exercise_name_map = {
        "press banca": ["press de banca", "bench press", "press banco"],
        "sentadillas": ["sentadilla", "squat", "squats"],
        "peso muerto": ["deadlift"],
        "dominadas": ["dominada", "pull up", "pull-up", "chin up"],
        "curl de bíceps": ["curl biceps", "curl de biceps", "bicep curl", "biceps curl"],
        "press militar": ["military press", "press de hombro"],
        "fondos": ["dips", "fondos de triceps", "triceps dips"],
        "remo": ["row", "remo con barra"]
    }
    
    for standard_name, variations in exercise_name_map.items():
        if exercise_info["exercise_name"] in variations:
            exercise_info["exercise_name"] = standard_name
            break
    
    return exercise_info

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
        # Para obtener información estructurada, podemos usar el LLM con el prompt de log_activity
        messages = PromptManager.get_prompt_messages("log_activity", query=query)
        
        # Invocar el LLM para extraer información estructurada
        llm = get_llm()
        
        # Extraer información del ejercicio como fallback si el LLM falla
        exercise_info = extract_exercise_info(query)
        exercise_name = exercise_info.get("exercise_name", "")
        
        if not exercise_name:
            logger.warning(f"No se pudo extraer nombre de ejercicio de: {query}")
            respuesta = "No pude entender qué ejercicio quieres registrar. Por favor, sé más específico. Por ejemplo: 'Registra press banca 3 series de 10 repeticiones con 60kg'."
            agent_state["generation"] = respuesta
            memory_state["messages"].append({"role": "assistant", "content": respuesta})
            return agent_state, memory_state
        
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Registrar ejercicio a través de la API con el token
        result = log_exercise(user_id, query, auth_token=auth_token)
        
        if result.get("success", False):
            # Registro exitoso
            logger.info(f"Ejercicio '{exercise_name}' registrado con éxito")
            
            # Obtener detalles del ejercicio
            sets_info = []
            for s in exercise_info.get("sets", []):
                reps = s.get("reps", 0)
                weight = s.get("weight", 0)
                sets_info.append(f"{reps} repeticiones con {weight}kg")
            
            # Construir mensaje de éxito
            if sets_info:
                sets_text = ", ".join(sets_info)
                respuesta = f"✅ He registrado tu ejercicio de **{exercise_name}** con {sets_text}. ¿Quieres registrar algo más?"
            else:
                respuesta = f"✅ He registrado tu ejercicio de **{exercise_name}**. ¿Quieres registrar algo más?"
        else:
            # Error al registrar
            error_message = result.get("detail", "Error desconocido")
            logger.error(f"Error al registrar ejercicio: {error_message}")
            
            if result.get("status_code") == 422:
                respuesta = "No pude entender correctamente el ejercicio. Por favor, intenta ser más específico con las series, repeticiones y peso."
            else:
                respuesta = f"Lo siento, tuve un problema al registrar tu ejercicio. Error: {error_message}"
    
    except Exception as e:
        logger.exception(f"Error procesando registro de actividad: {str(e)}")
        respuesta = "Ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo con un formato más claro."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- REGISTRO DE ACTIVIDAD FINALIZADO ---")
    return agent_state, memory_state