# fitness_chatbot/nodes/edit_routine_node.py
import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.chains.edit_routine_chain import EditRoutineChain

logger = logging.getLogger("fitness_chatbot")

async def process_edit_routine(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa solicitudes para editar rutinas de entrenamiento.
    Este nodo solo actúa como interfaz para la cadena EditRoutineChain.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE EDICIÓN DE RUTINA INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando solicitud de edición de rutina: '{query}' para usuario {user_id}")
    
    try:
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Llamar a la cadena para el procesamiento real
        respuesta = await EditRoutineChain.process_query(user_id, query, auth_token)
    
    except Exception as e:
        logger.exception(f"Error procesando edición de rutina: {str(e)}")
        respuesta = "Lo siento, tuve un problema al procesar tu solicitud para modificar la rutina. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE EDICIÓN DE RUTINA FINALIZADO ---")
    return agent_state, memory_state