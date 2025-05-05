# fitness_chatbot/nodes/today_routine_node.py
import logging
import json
from typing import Tuple, Dict, Any, List

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.utils.api_utils import make_api_request

logger = logging.getLogger("fitness_chatbot")

async def process_today_routine(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Obtiene la rutina de ejercicios del día actual utilizando la API del backend.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- CONSULTA DE RUTINA DIARIA INICIADA ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de rutina para usuario {user_id}: '{query}'")
    
    try:
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Hacer llamada a la API del backend para obtener la rutina del día
        response_data = make_api_request(
            endpoint="rutina_hoy", 
            method="GET",
            params={"format": "json"},
            auth_token=auth_token,
            timeout=30
        )
        
        # Registrar la respuesta completa para depuración
        logger.info("Respuesta completa de la API:")
        logger.info(json.dumps(response_data, indent=2))
        
        # Procesar el resultado
        if response_data.get('success', False):
            rutina = response_data.get('rutina', [])
            dia_nombre = response_data.get('dia_nombre', 'hoy')
            
            # Formatear la respuesta
            respuesta = f"## 📅 Tu rutina para {dia_nombre}\n\n"
            
            for idx, ejercicio in enumerate(rutina, 1):
                # Intentar mostrar todos los detalles posibles del diccionario
                respuesta += f"### {idx}. Ejercicio:\n"
                for key, value in ejercicio.items():
                    respuesta += f"- **{key.capitalize()}:** {value}\n"
                respuesta += "\n"
            
            respuesta += "¿Necesitas más detalles sobre estos ejercicios?"
        else:
            # Si la solicitud no fue exitosa
            respuesta = "No pude obtener tu rutina de hoy. ¿Quieres planificar tu entrenamiento?"
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de rutina: {str(e)}")
        respuesta = "Tuve un problema al obtener tu rutina. ¿Quieres planificar tu entrenamiento?"
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- CONSULTA DE RUTINA DIARIA FINALIZADA ---")
    return agent_state, memory_state