import logging
from typing import Tuple, Dict, Any, Optional

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.services import FitnessDataService

logger = logging.getLogger("fitness_chatbot")

async def process_exercise_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas relacionadas con ejercicios.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE EJERCICIO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    # Extraer nombre de ejercicio (si existe)
    exercise_name = extract_exercise_name(query)
    logger.info(f"Nombre de ejercicio extraído: {exercise_name}")
    
    # Obtener datos del ejercicio si se identificó uno
    if exercise_name:
        # Obtener historial del ejercicio
        exercise_history = await FitnessDataService.get_user_progress(user_id, exercise_name)
        if exercise_history:
            agent_state["user_context"]["exercise_history"] = exercise_history
            logger.info(f"Obtenidos {len(exercise_history)} registros históricos para {exercise_name}")
    
    # Si no hay ejercicio específico, obtener datos generales
    recent_exercises = await FitnessDataService.get_user_exercises(user_id, limit=5)
    agent_state["user_context"]["recent_exercises"] = recent_exercises
    logger.info(f"Obtenidos {len(recent_exercises)} ejercicios recientes")
    
    # Formatear el contexto para el LLM
    context = format_exercise_context(agent_state["user_context"])
    
    # Obtener mensajes de prompt para ejercicios
    messages = PromptManager.get_prompt_messages("exercise", query=query, user_context=context)
    
    # Obtener LLM
    llm = get_llm()
    
    # Invocar LLM
    try:
        response = await llm.ainvoke(messages)
        generation = response.content.strip()
        
        # Actualizar estado
        agent_state["generation"] = generation
        
        # Actualizar historial de mensajes
        memory_state["messages"].append({"role": "assistant", "content": generation})
        
        logger.info(f"Generada respuesta de {len(generation)} caracteres")
        
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        agent_state["generation"] = "Lo siento, hubo un error procesando tu consulta sobre ejercicios."
        memory_state["messages"].append({"role": "assistant", "content": agent_state["generation"]})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE EJERCICIO FINALIZADO ---")
    
    return agent_state, memory_state

def extract_exercise_name(query: str) -> Optional[str]:
    """Extrae el nombre del ejercicio de la consulta."""
    # Lista de ejercicios comunes para detectar
    common_exercises = [
        "press banca", "sentadilla", "peso muerto", "dominadas", 
        "press militar", "curl biceps", "fondos", "elevaciones laterales",
        "remo", "extensiones", "triceps"
    ]
    
    query_lower = query.lower()
    for exercise in common_exercises:
        if exercise in query_lower:
            return exercise
    
    return None

def format_exercise_context(user_context: Dict[str, Any]) -> str:
    """Formatea el contexto de ejercicio para el LLM."""
    context = []
    
    # Añadir información sobre ejercicio específico
    if "exercise_history" in user_context and user_context["exercise_history"]:
        history = user_context["exercise_history"]
        exercise_name = history[0].get("ejercicio", "desconocido") if history else "desconocido"
        
        context.append(f"Ejercicio consultado: {exercise_name}")
        context.append(f"\nHistorial del ejercicio (últimas {len(history)} sesiones):")
        
        for i, session in enumerate(history, 1):
            fecha = session.get("fecha", "fecha desconocida")
            repeticiones = session.get("repeticiones", "N/A")
            context.append(f"  {i}. Fecha: {fecha}")
            
            # Formatear repeticiones si es un objeto JSON
            if isinstance(repeticiones, dict) or isinstance(repeticiones, list):
                context.append("     Series:")
                for j, serie in enumerate(repeticiones if isinstance(repeticiones, list) else [repeticiones], 1):
                    reps = serie.get("repeticiones", "?")
                    peso = serie.get("peso", "?")
                    context.append(f"       - Serie {j}: {reps} repeticiones x {peso}kg")
    
    # Añadir ejercicios recientes
    if "recent_exercises" in user_context and user_context["recent_exercises"]:
        exercises = user_context["recent_exercises"]
        context.append("\nEjercicios recientes:")
        for i, ex in enumerate(exercises, 1):
            fecha = ex.get("fecha", "fecha desconocida")
            nombre = ex.get("ejercicio", "ejercicio desconocido")
            context.append(f"  {i}. {nombre} (Fecha: {fecha})")
    
    # Si no hay datos
    if not context:
        context.append("No hay datos disponibles sobre ejercicios para este usuario.")
    
    return "\n".join(context)