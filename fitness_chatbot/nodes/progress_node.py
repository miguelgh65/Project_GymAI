# fitness_chatbot/nodes/progress_node.py
import logging
from typing import Tuple, Dict, Any, List, Optional
import json

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
    logger.info("🔍🔍🔍 --- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO --- 🔍🔍🔍")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"📊 Procesando consulta de progreso: '{query}' para usuario {user_id}")
    
    try:
        # Revisar qué hay en el contexto del usuario
        user_context = agent_state.get("user_context", {})
        logger.info(f"💾 DATOS RECIBIDOS EN PROGRESS_NODE: {list(user_context.keys())}")
        
        # Verificar datos de historia
        if "exercise_history" in user_context:
            num_entries = len(user_context["exercise_history"])
            logger.info(f"📋 Encontrados {num_entries} registros de ejercicios en user_context")
            
            # Mostrar un ejemplo
            if num_entries > 0:
                example_data = json.dumps(user_context['exercise_history'][0], default=str)
                logger.info(f"📝 EJEMPLO DE DATO DE EJERCICIO: {example_data[:500]}")
                
                # Verificar tipos de campos
                for field, value in user_context['exercise_history'][0].items():
                    logger.info(f"🔎 Campo '{field}' es de tipo: {type(value).__name__}")
        else:
            logger.warning("⚠️ No hay datos de exercise_history en user_context!")
            user_context["exercise_history"] = []  # Inicializar como lista vacía
            
        # Verificar datos de Fitbit - son opcionales
        if "fitbit_data" in user_context and user_context["fitbit_data"].get("available", False):
            logger.info(f"⌚ Datos de Fitbit encontrados: {list(user_context['fitbit_data'].keys())}")
        else:
            logger.warning("⚠️ No hay datos de fitbit_data en user_context!")
            # Inicializar datos de Fitbit vacíos pero con estructura correcta
            user_context["fitbit_data"] = {"available": False}
        
        # Verificar si hay un ejercicio específico (history_node podría haberlo detectado)
        specific_exercise = user_context.get("specific_exercise", "")
        if specific_exercise:
            logger.info(f"🏋️ Ejercicio específico ya detectado: {specific_exercise}")
        else:
            # Intentar detectar el ejercicio específico desde la consulta
            from fitness_chatbot.chains.progress_chain import detect_exercise_in_query
            detected_exercise = detect_exercise_in_query(query)
            if detected_exercise:
                logger.info(f"🏋️ Ejercicio específico detectado de la consulta: {detected_exercise}")
                user_context["specific_exercise"] = detected_exercise
        
        # Si no hay datos de ejercicios, informar al usuario
        if not user_context.get("exercise_history"):
            logger.warning("⚠️ No hay datos de exercise_history para realizar análisis")
            respuesta = "No tengo suficientes datos para analizar tu progreso. Por favor, registra algunos ejercicios primero y vuelve a preguntar."
        else:
            # Pasar los datos a la chain para procesamiento
            logger.info("🔄 Enviando datos a progress_chain para análisis")
            respuesta = await progress_chain.process_query(
                user_id=user_id,
                query=query,
                user_context=user_context
            )
            
            logger.info(f"✅ progress_chain completado. Longitud de respuesta: {len(respuesta)} caracteres")
            logger.info(f"📊 Primeros 200 caracteres: {respuesta[:200]}")
    
    except Exception as e:
        logger.exception(f"❌ Error procesando consulta de progreso: {str(e)}")
        respuesta = "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("🏁🏁🏁 --- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO --- 🏁🏁🏁")
    return agent_state, memory_state