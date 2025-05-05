# fitness_chatbot/nodes/progress_node.py
import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.chains import progress_chain

logger = logging.getLogger("fitness_chatbot")

async def process_progress_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas sobre progreso, utilizando los datos recolectados por otros nodos
    que se ejecutaron en paralelo (history y fitbit).
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de progreso: '{query}' para usuario {user_id}")
    
    try:
        # Simplemente pasar los datos del contexto a la chain para que procese
        # La chain se encargará de extraer los datos necesarios
        respuesta = await progress_chain.process_query(
            user_id=user_id,
            query=query,
            user_context=agent_state.get("user_context", {})
        )
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de progreso: {str(e)}")
        respuesta = "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO ---")
    return agent_state, memory_state