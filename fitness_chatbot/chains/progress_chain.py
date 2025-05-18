# fitness_chatbot/chains/progress_chain.py
import logging
import json
from typing import Dict, Any
import asyncio

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
        
        # Simplificar ejercicios para reducir tamaño
        simplified_exercises = []
        for ex in exercise_history:
            if isinstance(ex, dict):
                # Solo incluir campos esenciales
                simple_ex = {
                    "fecha": ex.get("fecha", ""),
                    "ejercicio": ex.get("ejercicio", ""),
                    "repeticiones": ex.get("repeticiones", 0)
                }
                simplified_exercises.append(simple_ex)
        
        # Reducir a máximo 7 ejercicios para evitar timeout
        MAX_EXERCISES = 50
        if len(simplified_exercises) > MAX_EXERCISES:
            simplified_exercises = simplified_exercises[:MAX_EXERCISES]
        
        # Formatear contexto muy simple
        context_string = f"EJERCICIOS REALIZADOS ({len(simplified_exercises)}):\n\n"
        
        # Añadir ejercicios simplificados
        for i, ex in enumerate(simplified_exercises):
            context_string += f"{i+1}. {ex['ejercicio']}: {ex['repeticiones']} reps ({ex['fecha']})\n"
        
        # Prompt del sistema ultrasimplificado
        system_prompt = """
        Analiza el progreso en ejercicios del usuario:
        1. Evalúa tendencias en repeticiones
        2. Identifica si hay mejora o no
        3. Da recomendaciones simples para mejorar
        
        Formato: breve y concreto, con recomendaciones prácticas.
        """
        
        # Crear mensaje para LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context_string}\n\n{query}"}
        ]
        
        # Obtener LLM con configuración mínima
        llm = get_llm()
        if not llm:
            return "Lo siento, no puedo analizar tu progreso en este momento."
        
        # Configurar para respuesta ultrarrápida
        if hasattr(llm, 'with_timeout'):
            llm = llm.with_timeout(150) # Solo 15 segundos
        
        if hasattr(llm, 'with_max_tokens'):
            llm = llm.with_max_tokens(300)  # Respuesta muy corta
        
        # Invocar con timeout estricto
        try:
            response = await asyncio.wait_for(llm.ainvoke(messages), timeout=20)
            content = response.content if hasattr(response, 'content') else str(response)
        except:
            return "No pude completar el análisis a tiempo. Simplifica tu consulta o intenta más tarde."
        
        return content
    
    except Exception as e:
        logger.exception(f"❌ Error en ProgressChain: {str(e)}")
        return "Lo siento, tuve un problema al analizar tu progreso."