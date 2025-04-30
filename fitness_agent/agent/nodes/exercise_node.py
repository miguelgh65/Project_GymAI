import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

# Configuración de logging
logger = logging.getLogger("fitness_agent")

# Importar configuración de LangSmith
try:
    import langsmith
    from langsmith import traceable
    HAS_LANGSMITH = True
except ImportError:
    logger.warning("LangSmith not installed, tracing disabled")
    HAS_LANGSMITH = False
    # Decorador dummy si no está disponible
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Importaciones específicas del proyecto
from fitness_agent.agent.core.state import AgentState
from fitness_agent.agent.schemas import ExerciseResponseSchema
from fitness_agent.agent.utils.llm_utils import format_llm_response, get_llm
from fitness_agent.agent.utils.prompt_utils import get_formatted_prompt

# Importar herramientas
try:
    from fitness_agent.agent.tools.exercise_tools import (
        get_exercise_stats, get_recent_exercises,
        recommend_exercise_progression)
    HAS_TOOLS = True
except ImportError as e:
    logger.warning(f"Could not import exercise tools: {e}")
    HAS_TOOLS = False

# Frases motivacionales para añadir al final de las respuestas
MOTIVATIONAL_PHRASES = [
    "¡A por ello! 💪",
    "¡No hay excusas! 🏋️‍♂️",
    "¡Cada día más fuerte! 💯",
    "¡Tú puedes lograrlo! 🔥",
    "¡Supera tus límites! 🚀"
]

@traceable(run_type="tool")
def get_user_exercise_context(user_id: str) -> str:
    """
    Obtiene el contexto de ejercicios del usuario para enriquecer las respuestas.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        String con el contexto de ejercicios del usuario
    """
    if not HAS_TOOLS:
        return "No hay información de ejercicios disponible."
    
    try:
        # Obtener ejercicios recientes
        recent_exercises_json = get_recent_exercises(user_id)
        recent_exercises = json.loads(recent_exercises_json)
        
        if not recent_exercises:
            return "El usuario no tiene ejercicios registrados aún."
        
        # Formatear el contexto
        context = "Ejercicios recientes del usuario:\n"
        
        for exercise in recent_exercises[:3]:  # Mostrar solo los 3 más recientes
            context += f"- {exercise.get('ejercicio', 'Desconocido')} ({exercise.get('fecha', 'fecha desconocida')})\n"
            
            # Añadir detalles de series si están disponibles
            if 'series' in exercise:
                series_info = ", ".join([f"{s.get('repeticiones', 'x')}x{s.get('peso', 'x')}kg" for s in exercise['series']])
                context += f"  Series: {series_info}\n"
        
        # Intentar obtener estadísticas de algún ejercicio clave
        try:
            if recent_exercises and 'ejercicio' in recent_exercises[0]:
                stats_json = get_exercise_stats(user_id, recent_exercises[0]['ejercicio'])
                stats = json.loads(stats_json)
                
                context += "\nEstadísticas de ejercicios destacados:\n"
                context += f"- {stats.get('nombre_ejercicio', 'Desconocido')}: Peso máximo: {stats.get('max_peso', 'N/A')}kg, "
                context += f"Progresión último mes: {stats.get('progresion_ultimo_mes', 'N/A')}\n"
        except Exception as e:
            logger.warning(f"Error getting exercise stats: {e}")
        
        return context
    
    except Exception as e:
        logger.error(f"Error getting user exercise context: {e}")
        return "Error obteniendo contexto de ejercicios."

@traceable(run_type="chain")
def exercise_node(state: AgentState) -> Dict[str, Any]:
    """
    Nodo especializado en consultas relacionadas con ejercicios y entrenamiento.
    
    Args:
        state: Estado actual del agente
        
    Returns:
        Estado actualizado con la respuesta del nodo
    """
    try:
        # Preparar datos del mensaje
        messages = state["messages"]
        user_id = state["user_id"]
        user_message = messages[-1]["content"]  # Último mensaje del usuario
        
        # Configurar LangSmith si está disponible
        if HAS_LANGSMITH:
            try:
                project_name = os.getenv("LANGSMITH_PROJECT", "gym")
                langsmith.set_project(project_name)
                langsmith.set_tags(["exercise_node", f"user:{user_id}"])
            except Exception as e:
                logger.error(f"Error configuring LangSmith: {e}")
        
        # Obtener contexto de ejercicios del usuario
        user_context = get_user_exercise_context(user_id)
        
        # Cargar el prompt de sistema desde el archivo
        system_prompt = get_formatted_prompt("exercise", "system", user_context=user_context)
        
        # Determinar si se necesita un prompt específico
        message_lower = user_message.lower()
        prompt_type = "system"  # Prompt por defecto
        
        if any(word in message_lower for word in ["registrar", "anotar", "añadir"]):
            prompt_type = "registration"
        elif any(word in message_lower for word in ["rutina", "programa", "plan"]):
            prompt_type = "routine"
        
        # Cargar prompt específico si es necesario
        if prompt_type != "system":
            specific_prompt = get_formatted_prompt("exercise", prompt_type)
            system_prompt = f"{system_prompt}\n\n{specific_prompt}"
        
        # Generar respuesta usando el LLM
        llm = get_llm()
        
        # Preparar los mensajes para el LLM
        messages_for_llm = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Llamar al LLM
        response = llm.invoke(messages_for_llm)
        content = format_llm_response(response.content)
        
        # Añadir frase motivacional al final si no tiene una
        if not any(phrase in content for phrase in MOTIVATIONAL_PHRASES):
            content += f"\n\n{random.choice(MOTIVATIONAL_PHRASES)}"
        
        # Validar la respuesta con el esquema Pydantic (si está disponible)
        try:
            # La validación iría aquí, pero vamos a omitirla por simplicidad
            pass
        except Exception as validation_error:
            logger.warning(f"Response validation failed: {validation_error}")
            # En caso de error de validación, podríamos reintentar o dejar pasar
        
        # Crear mensaje de respuesta
        response_message = {
            "role": "assistant",
            "content": content
        }
        
        # Registrar actividad
        logger.info(f"Exercise node generated response: {content[:100]}...")
        
        # Devolver estado actualizado con la respuesta
        return {"messages": [response_message]}
    
    except Exception as e:
        logger.error(f"Error in exercise_node: {e}")
        
        # Mensaje de error
        error_message = {
            "role": "assistant",
            "content": f"Lo siento, ocurrió un error al procesar tu consulta sobre ejercicios. Por favor, inténtalo de nuevo.\n\n¡No te rindas! 💪"
        }
        
        return {"messages": [error_message]}