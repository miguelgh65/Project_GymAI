# fitness_chatbot/chains/progress_chain.py
import logging
import json
from typing import Dict, Any

from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

async def process_query(user_id: str, query: str, user_context: Dict[str, Any] = None) -> str:
    """
    Procesa una consulta sobre progreso y genera un análisis utilizando LLM.
    
    Args:
        user_id: ID del usuario
        query: Consulta en lenguaje natural
        user_context: Contexto con datos recolectados por otros nodos
        
    Returns:
        Respuesta formateada con análisis de progreso
    """
    logger.info(f"🚀 ProgressChain procesando: '{query}' para usuario {user_id}")
    
    if not user_context:
        user_context = {}
    
    try:
        # Obtener datos de history_node y fitbit_node
        exercise_history = user_context.get("exercise_history", [])
        fitbit_data = user_context.get("fitbit_data", {})
        
        # Formatear los datos para el LLM
        context_string = "=== HISTORIAL DE EJERCICIOS ===\n\n"
        context_string += f"Total de ejercicios registrados: {len(exercise_history)}\n\n"
        
        # Añadir cada ejercicio
        for i, session in enumerate(exercise_history):
            context_string += f"Ejercicio {i+1}: {json.dumps(session, default=str)}\n\n"
        
        # Añadir datos de Fitbit
        context_string += "=== DATOS DE FITBIT ===\n\n"
        context_string += f"Datos: {json.dumps(fitbit_data, default=str)[:1000]}\n\n"
        
        # Obtener LLM
        llm = get_llm()
        if not llm:
            logger.error("LLM no disponible para generar análisis de progreso")
            return "Lo siento, no puedo analizar tu progreso en este momento debido a un problema técnico."
        
        # Obtener prompts para análisis de progreso
        messages = PromptManager.get_prompt_messages(
            "progress",
            query=query,
            user_context=context_string
        )
        
        # Invocar el LLM
        response = await llm.ainvoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        return content
    
    except Exception as e:
        logger.exception(f"❌ Error en ProgressChain: {str(e)}")
        return "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."