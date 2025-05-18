# fitness_chatbot/nodes/history_node.py
import logging
from typing import Tuple
import json

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
    logger.info("📚📚📚 --- PROCESAMIENTO DE CONSULTA DE HISTORIAL INICIADO --- 📚📚📚")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"🔍 Procesando consulta de historial: '{query}' para usuario {user_id}")
    
    try:
        # Verificar si estamos en un flujo de progreso
        is_progress = agent_state.get("is_progress", False)
        logger.info(f"🧩 Flujo de progreso detectado: {is_progress}")
        
        # Asegurar que existe user_context
        if "user_context" not in agent_state:
            agent_state["user_context"] = {}
        
        # Obtener historial de ejercicios (últimos 100)
        logger.info(f"📊 Consultando ejercicios para user_id={user_id}")
        exercise_data = await FitnessDataService.get_user_exercises(user_id, limit=100)
        
        if exercise_data:
            # Verificar la estructura para debugging
            logger.info(f"✅ Obtenidos {len(exercise_data)} registros de ejercicios")
            
            # Log detallado de la estructura de los datos
            if len(exercise_data) > 0:
                first_entry = exercise_data[0]
                logger.info(f"📝 Estructura del primer registro: {json.dumps(first_entry, default=str)[:300]}...")
                logger.info(f"📊 Campos disponibles: {list(first_entry.keys())}")
            
            # Guardar en user_context para que progress_node pueda acceder
            agent_state["user_context"]["exercise_history"] = exercise_data
            logger.info(f"💾 Datos de historial almacenados para progress: {len(exercise_data)} registros")
            
            # Si es un flujo de progreso, añadir información de logging
            if is_progress:
                logger.info("🔄 FLUJO DE PROGRESO: Preparando datos para el nodo process_progress")
                # Ya no necesitamos detectar ejercicio específico, simplemente recolectamos datos
        else:
            logger.warning("⚠️ No se encontraron datos de historial")
            agent_state["user_context"]["exercise_history"] = []
        
        # Si es consulta normal de historial (no progress), generar respuesta
        if not is_progress:
            # Llamar a la cadena para el procesamiento real
            respuesta = await HistoryChain.process_query(user_id, query)
            
            # Actualizar estado y memoria
            agent_state["generation"] = respuesta
            memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    except Exception as e:
        logger.exception(f"❌ Error procesando consulta de historial: {str(e)}")
        
        if not agent_state.get("is_progress", False):
            respuesta = "Lo siento, tuve un problema al procesar tu consulta sobre tu historial de ejercicios."
            agent_state["generation"] = respuesta
            memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("🏁🏁🏁 --- PROCESAMIENTO DE CONSULTA DE HISTORIAL FINALIZADO --- 🏁🏁🏁")
    return agent_state, memory_state