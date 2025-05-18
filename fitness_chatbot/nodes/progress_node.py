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
    que se ejecutaron previamente (history y fitbit).
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("🔍🔍🔍 --- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO --- 🔍🔍🔍")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"📊 Procesando consulta de progreso: '{query}' para usuario {user_id}")
    
    try:
        # Obtener el contexto del usuario (que ya debería tener los datos de history_node y fitbit_node)
        user_context = agent_state.get("user_context", {})
        
        # Verificar qué datos tenemos disponibles
        logger.info(f"💾 Datos disponibles: {list(user_context.keys())}")
        
        if "exercise_history" in user_context:
            logger.info(f"📋 Exercise history: {len(user_context['exercise_history'])} registros")
        
        if "fitbit_data" in user_context:
            logger.info(f"⌚ Fitbit data: {list(user_context['fitbit_data'].keys() if isinstance(user_context['fitbit_data'], dict) else ['datos no disponibles'])}")
        
        # Pasar los datos directamente a progress_chain sin procesar
        logger.info("🔄 Enviando datos a progress_chain para análisis")
        respuesta = await progress_chain.process_query(
            user_id=user_id,
            query=query,
            user_context=user_context
        )
        
        logger.info(f"✅ progress_chain completado. Longitud de respuesta: {len(respuesta)} caracteres")
    
    except Exception as e:
        logger.exception(f"❌ Error procesando consulta de progreso: {str(e)}")
        respuesta = "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("🏁🏁🏁 --- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO --- 🏁🏁🏁")
    return agent_state, memory_state