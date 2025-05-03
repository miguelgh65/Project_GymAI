# fitness_chatbot/nodes/response_node.py
import logging
import os
import json
import requests
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

async def generate_final_response(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Genera la respuesta final utilizando el sistema de prompts.
    Versión optimizada para evitar timeouts.
    """
    logger.info("--- GENERACIÓN DE RESPUESTA FINAL OPTIMIZADA ---")
    
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
    
    # Si no hay generación previa, crear una respuesta
    query = agent_state["query"]
    
    try:
        # Cargar el prompt adecuado - usar 'general' para respuestas generales
        logger.info("Cargando prompt 'general' para respuesta")
        messages = PromptManager.get_prompt_messages("general", query=query)
        
        # Obtener configuración LLM
        llm = get_llm()
        
        if llm is None:
            logger.error("LLM no disponible. Usando respuesta genérica")
            generation = "Lo siento, no puedo responder a tu pregunta en este momento debido a problemas técnicos. Por favor, intenta más tarde."
        else:
            logger.info("Configurando LLM para respuesta rápida")
            
            # Configurar para respuestas más cortas y rápidas
            if hasattr(llm, 'with_max_tokens'):
                llm = llm.with_max_tokens(250)  # Limitar a 250 tokens (~175 palabras)
            
            if hasattr(llm, 'with_temperature'):
                llm = llm.with_temperature(0.3)  # Temperatura más baja para respuestas más determinísticas
                
            if hasattr(llm, 'with_timeout'):
                llm = llm.with_timeout(10)  # Timeout reducido a 10 segundos
            
            logger.info("Generando respuesta con LLM optimizado")
            response = await llm.ainvoke(messages)
            generation = response.content.strip() if hasattr(response, 'content') else str(response)
            logger.info(f"Respuesta generada con éxito: {len(generation)} caracteres")
        
        # Actualizar estado
        agent_state["generation"] = generation
        memory_state["messages"].append({
            "role": "assistant", 
            "content": generation
        })
    
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        fallback_message = "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo con una pregunta más sencilla."
        
        agent_state["generation"] = fallback_message
        memory_state["messages"].append({
            "role": "assistant", 
            "content": fallback_message
        })
    
    logger.info("--- FIN GENERACIÓN DE RESPUESTA ---")
    return agent_state, memory_state