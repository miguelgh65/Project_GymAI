# fitness_chatbot/nodes/history_node.py
import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.chains.history_chain import HistoryChain
from fitness_chatbot.core.services import FitnessDataService

logger = logging.getLogger("fitness_chatbot")

async def process_history_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas para ver el historial de ejercicios del usuario.
    Este nodo también guarda datos en user_context para ser utilizados por el nodo de progreso.
    
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
        
        # Colectar datos para el nodo de progreso (cuando se usa en paralelo)
        try:
            # Asegurar que existe user_context
            if "user_context" not in agent_state:
                agent_state["user_context"] = {}
                
            # Obtener historial de ejercicios (últimos 100)
            exercise_data = await FitnessDataService.get_user_exercises(user_id, limit=100)
            if exercise_data:
                # Guardar en user_context para que progress_node pueda acceder
                agent_state["user_context"]["exercise_history"] = exercise_data
                logger.info(f"Datos de historial almacenados para progress: {len(exercise_data)} registros")
        except Exception as e:
            logger.warning(f"No se pudieron almacenar datos para progress: {str(e)}")
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de historial: {str(e)}")
        respuesta = "Lo siento, tuve un problema al procesar tu consulta sobre tu historial de ejercicios."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE HISTORIAL FINALIZADO ---")
    return agent_state, memory_state