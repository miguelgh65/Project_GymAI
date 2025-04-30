import logging
import json
from typing import Tuple

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.schemas.prompt_schemas import IntentClassification
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

async def classify_intent(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Clasifica la intención del usuario basándose en su consulta.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- CLASIFICACIÓN DE INTENCIÓN INICIADA ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener la consulta del usuario
    query = agent_state["query"]
    logger.info(f"Consulta a clasificar: '{query}'")
    
    # Obtener mensajes de prompt para el router
    messages = PromptManager.get_prompt_messages("router", query=query)
    
    # Obtener el modelo LLM configurado con salida estructurada
    llm = get_llm().with_structured_output(IntentClassification)
    
    # Llamar al LLM para clasificar
    try:
        classification = await llm.ainvoke(messages)
        
        # Extraer la intención
        intent = classification.intent.lower()
        
        # Normalizar la intención
        if "ejercicio" in intent or "entrenamiento" in intent or intent == "exercise":
            normalized_intent = IntentType.EXERCISE
        elif "nutri" in intent or "comida" in intent or "dieta" in intent or intent == "nutrition":
            normalized_intent = IntentType.NUTRITION
        elif "progreso" in intent or "estadística" in intent or intent == "progress":
            normalized_intent = IntentType.PROGRESS
        elif any(kw in intent for kw in ["registrar", "anotar", "log"]) or intent == "log_activity":
            normalized_intent = IntentType.LOG_ACTIVITY
        else:
            normalized_intent = IntentType.GENERAL
            
    except Exception as e:
        logger.error(f"Error en la clasificación: {str(e)}")
        normalized_intent = IntentType.GENERAL
    
    # Actualizar estado con la intención detectada
    agent_state["intent"] = normalized_intent
    
    # Actualizar historial de mensajes
    if "messages" not in memory_state:
        memory_state["messages"] = []
    
    memory_state["messages"].append({"role": "user", "content": query})
    
    logger.info(f"Intención normalizada: {normalized_intent}")
    logger.info("--- CLASIFICACIÓN DE INTENCIÓN FINALIZADA ---")
    
    return agent_state, memory_state