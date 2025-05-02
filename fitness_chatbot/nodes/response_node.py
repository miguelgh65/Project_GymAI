# fitness_chatbot/nodes/response_node.py - VERSIÓN SIMPLE
import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm

logger = logging.getLogger("fitness_chatbot")

async def generate_final_response(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """Genera la respuesta final si no existe una generación previa."""
    logger.info("--- GENERACIÓN DE RESPUESTA FINAL ---")
    
    agent_state, memory_state = states
    
    # Si ya hay una generación previa, usarla directamente
    if agent_state.get("generation"):
        logger.info("Usando respuesta generada previamente")
        
        # Verificar si ya está en el historial
        last_message = memory_state["messages"][-1] if memory_state["messages"] else None
        if not last_message or last_message.get("role") != "assistant" or last_message.get("content") != agent_state["generation"]:
            memory_state["messages"].append({
                "role": "assistant", 
                "content": agent_state["generation"]
            })
        
        logger.info("--- FIN GENERACIÓN DE RESPUESTA ---")
        return agent_state, memory_state
    
    # Si no hay generación previa, crear una respuesta genérica
    query = agent_state["query"]
    
    try:
        # Generar respuesta con el LLM
        messages = [
            {"role": "system", "content": "Eres un asistente de fitness amigable."},
            {"role": "user", "content": query}
        ]
        
        llm = get_llm()
        response = await llm.ainvoke(messages)
        generation = response.content.strip()
        
        # Actualizar estado
        agent_state["generation"] = generation
        memory_state["messages"].append({
            "role": "assistant", 
            "content": generation
        })
        
        logger.info(f"Respuesta general generada: {len(generation)} caracteres")
    
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        fallback_message = "Lo siento, no puedo procesar tu consulta en este momento."
        
        agent_state["generation"] = fallback_message
        memory_state["messages"].append({
            "role": "assistant", 
            "content": fallback_message
        })
    
    logger.info("--- FIN GENERACIÓN DE RESPUESTA ---")
    return agent_state, memory_state