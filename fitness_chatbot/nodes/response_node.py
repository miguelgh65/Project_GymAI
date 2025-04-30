import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

async def generate_final_response(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Genera la respuesta final para el usuario.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- GENERACIÓN DE RESPUESTA FINAL INICIADA ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Si ya existe una generación de un nodo previo, usarla directamente
    if agent_state.get("generation"):
        logger.info("Usando respuesta generada previamente")
        
        # Verificar si la respuesta ya se añadió al historial de mensajes
        last_message = memory_state["messages"][-1] if memory_state["messages"] else None
        if not last_message or last_message.get("role") != "assistant" or last_message.get("content") != agent_state["generation"]:
            # Añadir al historial solo si no está ya añadida
            memory_state["messages"].append({
                "role": "assistant", 
                "content": agent_state["generation"]
            })
            logger.info("Respuesta añadida al historial de mensajes")
        
        logger.info("--- GENERACIÓN DE RESPUESTA FINAL FINALIZADA ---")
        return agent_state, memory_state
    
    # Si llegamos aquí, es porque no hay generación previa (caso general/fallback)
    query = agent_state["query"]
    
    try:
        # Obtener prompt para respuesta general
        messages = [
            {"role": "system", "content": "Eres un asistente de fitness amigable. Proporciona información general sobre fitness y bienestar."},
            {"role": "user", "content": query}
        ]
        
        # Obtener LLM
        llm = get_llm()
        
        # Generar respuesta
        response = await llm.ainvoke(messages)
        generation = response.content.strip()
        
        # Actualizar estado
        agent_state["generation"] = generation
        
        # Añadir al historial
        memory_state["messages"].append({
            "role": "assistant", 
            "content": generation
        })
        
        logger.info(f"Respuesta general generada: {len(generation)} caracteres")
    
    except Exception as e:
        logger.error(f"Error generando respuesta general: {str(e)}")
        fallback_message = "Lo siento, no puedo procesar tu consulta en este momento. ¿Puedes intentarlo de nuevo o formularla de otra manera?"
        
        agent_state["generation"] = fallback_message
        memory_state["messages"].append({
            "role": "assistant", 
            "content": fallback_message
        })
    
    logger.info("--- GENERACIÓN DE RESPUESTA FINAL FINALIZADA ---")
    return agent_state, memory_state