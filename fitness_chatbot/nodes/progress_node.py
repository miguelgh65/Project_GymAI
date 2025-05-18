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
                try:
                    sample_entry = user_context['exercise_history'][0]
                    logger.info(f"📝 EJEMPLO DE DATO DE EJERCICIO: {str(sample_entry)}")
                    
                    # Verificar campos disponibles
                    fields = list(sample_entry.keys())
                    logger.info(f"📊 Campos disponibles: {fields}")
                    
                    # Verificar tipos de campos
                    for field, value in sample_entry.items():
                        logger.info(f"🔎 Campo '{field}' es de tipo: {type(value).__name__}")
                except Exception as e:
                    logger.error(f"Error mostrando ejemplo de ejercicio: {e}")
        else:
            logger.warning("⚠️ No hay datos de exercise_history en user_context!")
            
        # Verificar datos de Fitbit
        if "fitbit_data" in user_context:
            logger.info(f"⌚ Datos de Fitbit encontrados: {list(user_context['fitbit_data'].keys())}")
        else:
            logger.warning("⚠️ No hay datos de fitbit_data en user_context!")
            
        # Detectar ejercicio específico de la consulta
        from fitness_chatbot.chains.progress_chain import detect_exercise_in_query
        
        # Primero verificar si ya existe en el contexto
        specific_exercise = user_context.get("specific_exercise", "")
        
        # Si no existe, intentar detectarlo de la consulta
        if not specific_exercise:
            specific_exercise = detect_exercise_in_query(query)
            if specific_exercise:
                logger.info(f"🏋️ Ejercicio específico detectado: {specific_exercise}")
                user_context["specific_exercise"] = specific_exercise
                
                # Caso especial para detectar press banca con diferentes escrituras
                if specific_exercise.lower() == "press banca":
                    # Filtrar y contar cuántos registros corresponden
                    filtered = [e for e in user_context.get("exercise_history", []) 
                              if "press" in e.get('ejercicio', '').lower() and 
                                 "banc" in e.get('ejercicio', '').lower()]
                    
                    logger.info(f"📊 Se encontraron {len(filtered)} registros para press banca")
        
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