import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.services import FitnessDataService

logger = logging.getLogger("fitness_chatbot")

async def process_nutrition_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas relacionadas con nutrición.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE NUTRICIÓN INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    # Obtener datos nutricionales del usuario
    try:
        # Obtener historial nutricional reciente
        nutrition_history = await FitnessDataService.get_user_nutrition_data(user_id, days=7)
        if nutrition_history:
            agent_state["user_context"]["nutrition_history"] = nutrition_history
            logger.info(f"Obtenidos {len(nutrition_history)} registros nutricionales")
        
        # Formatear el contexto para el LLM
        context = format_nutrition_context(agent_state["user_context"])
        
        # Obtener mensajes de prompt para nutrición
        messages = PromptManager.get_prompt_messages("nutrition", query=query, user_context=context)
        
        # Obtener LLM
        llm = get_llm()
        
        # Invocar LLM
        response = await llm.ainvoke(messages)
        generation = response.content.strip()
        
        # Actualizar estado
        agent_state["generation"] = generation
        
        # Actualizar historial de mensajes
        memory_state["messages"].append({"role": "assistant", "content": generation})
        
        logger.info(f"Generada respuesta nutricional de {len(generation)} caracteres")
    
    except Exception as e:
        logger.error(f"Error procesando consulta nutricional: {str(e)}")
        agent_state["generation"] = "Lo siento, hubo un error al procesar tu consulta nutricional."
        memory_state["messages"].append({"role": "assistant", "content": agent_state["generation"]})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE NUTRICIÓN FINALIZADO ---")
    
    return agent_state, memory_state

def format_nutrition_context(user_context: Dict[str, Any]) -> str:
    """Formatea el contexto nutricional para el LLM."""
    context = []
    
    # Añadir historial nutricional
    if "nutrition_history" in user_context and user_context["nutrition_history"]:
        history = user_context["nutrition_history"]
        
        context.append("Historial nutricional reciente:")
        
        for i, entry in enumerate(history, 1):
            date = entry.get("tracking_date", "fecha desconocida")
            calories = entry.get("actual_calories", "N/A")
            protein = entry.get("actual_protein", "N/A")
            completed_meals = entry.get("completed_meals", {})
            
            context.append(f"  {i}. Fecha: {date}")
            context.append(f"     Calorías: {calories}")
            context.append(f"     Proteína: {protein} g")
            
            if completed_meals:
                context.append("     Comidas completadas:")
                for meal, completed in completed_meals.items():
                    status = "✅" if completed else "❌"
                    context.append(f"       - {meal}: {status}")
    
    # Si no hay datos
    if not context:
        context.append("No hay datos nutricionales disponibles para este usuario.")
    
    return "\n".join(context)