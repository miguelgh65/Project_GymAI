# fitness_chatbot/nodes/history_node.py
import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.chains.history_chain import HistoryChain

logger = logging.getLogger("fitness_chatbot")

async def process_history_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas para ver el historial de ejercicios del usuario.
    Este nodo solo actúa como interfaz para la cadena HistoryChain.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE HISTORIAL INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de historial: '{query}' para usuario {user_id}")
    
    try:
        # Llamar a la cadena para el procesamiento real
        respuesta = await HistoryChain.process_query(user_id, query)
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de historial: {str(e)}")
        respuesta = "Lo siento, tuve un problema al procesar tu consulta sobre tu historial de ejercicios."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE HISTORIAL FINALIZADO ---")
    return agent_state, memory_state