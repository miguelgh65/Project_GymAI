# fitness_chatbot/nodes/nutrition_node.py
import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.chains.nutrition_chain import NutritionChain

logger = logging.getLogger("fitness_chatbot")

async def process_nutrition_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas sobre nutrición y muestra la dieta para el día actual.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- CONSULTA DE DIETA DIARIA INICIADA ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de nutrición para usuario {user_id}: '{query}'")
    
    try:
        # Usar la chain de nutrición para procesar la consulta
        respuesta = await NutritionChain.process_query(user_id, query)
    except Exception as e:
        logger.exception(f"Error procesando consulta de nutrición: {str(e)}")
        respuesta = "Lo siento, tuve un problema al procesar tu consulta sobre nutrición."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- CONSULTA DE DIETA DIARIA FINALIZADA ---")
    return agent_state, memory_state