import logging
from typing import Tuple, Dict, Any, List, Optional

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.services import FitnessDataService

logger = logging.getLogger("fitness_chatbot")

async def process_progress_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas relacionadas con progreso y estadísticas.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    # Extraer ejercicio específico si lo hay
    exercise_name = extract_exercise_name(query)
    
    try:
        # Obtener datos de progreso
        if exercise_name:
            # Progreso específico del ejercicio
            progress_data = await FitnessDataService.get_user_progress(user_id, exercise_name)
            if progress_data:
                agent_state["user_context"]["progress_data"] = progress_data
                agent_state["user_context"]["exercise_name"] = exercise_name
                logger.info(f"Obtenidos datos de progreso para {exercise_name}: {len(progress_data)} registros")
        else:
            # Progreso general
            progress_data = await FitnessDataService.get_user_exercises(user_id, limit=30)
            agent_state["user_context"]["progress_data"] = progress_data
            logger.info(f"Obtenidos datos de progreso general: {len(progress_data)} registros")
        
        # Realizar análisis de progreso
        context = format_progress_context(agent_state["user_context"])
        
        # Obtener mensajes de prompt para progreso
        messages = PromptManager.get_prompt_messages("progress", query=query, user_context=context)
        
        # Obtener LLM
        llm = get_llm()
        
        # Invocar LLM
        response = await llm.ainvoke(messages)
        generation = response.content.strip()
        
        # Actualizar estado
        agent_state["generation"] = generation
        
        # Actualizar historial de mensajes
        memory_state["messages"].append({"role": "assistant", "content": generation})
        
        logger.info(f"Generado análisis de progreso de {len(generation)} caracteres")
    
    except Exception as e:
        logger.error(f"Error procesando análisis de progreso: {str(e)}")
        agent_state["generation"] = "Lo siento, hubo un error al analizar tu progreso."
        memory_state["messages"].append({"role": "assistant", "content": agent_state["generation"]})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO ---")
    
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

def format_progress_context(user_context: Dict[str, Any]) -> str:
    """Formatea el contexto de progreso para el LLM."""
    context = []
    
    # Determinar si es progreso específico o general
    if "exercise_name" in user_context:
        exercise_name = user_context["exercise_name"]
        context.append(f"Ejercicio: {exercise_name}")
    else:
        context.append("Progreso general de entrenamiento")
    
    # Añadir datos de progreso
    if "progress_data" in user_context and user_context["progress_data"]:
        progress_data = user_context["progress_data"]
        
        if "exercise_name" in user_context:
            # Progreso específico de un ejercicio
            context.append(f"Sesiones registradas (últimos {len(progress_data)} registros):")
            
            for i, session in enumerate(progress_data, 1):
                fecha = session.get("fecha", "fecha desconocida")
                repeticiones = session.get("repeticiones", [])
                
                context.append(f"  {i}. Fecha: {fecha}")
                if repeticiones:
                    context.append("     Series:")
                    if isinstance(repeticiones, list):
                        for j, serie in enumerate(repeticiones, 1):
                            reps = serie.get("repeticiones", "?")
                            peso = serie.get("peso", "?")
                            context.append(f"       - {reps} repeticiones x {peso}kg")
                    elif isinstance(repeticiones, dict):
                        reps = repeticiones.get("repeticiones", "?")
                        peso = repeticiones.get("peso", "?")
                        context.append(f"       - {reps} repeticiones x {peso}kg")
        else:
            # Progreso general
            exercise_counts = {}
            for session in progress_data:
                exercise = session.get("ejercicio", "desconocido")
                if exercise in exercise_counts:
                    exercise_counts[exercise] += 1
                else:
                    exercise_counts[exercise] = 1
            
            context.append("Resumen de actividad:")
            for exercise, count in sorted(exercise_counts.items(), key=lambda x: x[1], reverse=True):
                context.append(f"  - {exercise}: {count} sesiones")
    
    # Si no hay datos
    if len(context) <= 1:  # Solo tiene la línea de encabezado
        context.append("No hay datos de progreso disponibles para este usuario.")
    
    return "\n".join(context)