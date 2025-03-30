import datetime
import json
import logging
import os
import re
from typing import Any, Dict

# Configuración de logging
logger = logging.getLogger("fitness_agent")

# Importar configuración de LangSmith
try:
    import langsmith

    # Check if the required methods are available
    HAS_LANGSMITH_PROJECT = hasattr(langsmith, 'set_project')
    HAS_LANGSMITH_TAGS = hasattr(langsmith, 'set_tags')
    HAS_LANGSMITH = HAS_LANGSMITH_PROJECT and HAS_LANGSMITH_TAGS
    
    if HAS_LANGSMITH:
        logger.info("Successfully imported LangSmith with all required methods")
    else:
        logger.warning("LangSmith imported but some required methods are not available")
        
    # Create dummy methods if needed
    if not HAS_LANGSMITH_PROJECT:
        def set_project(name):
            logger.debug(f"Dummy set_project called with: {name}")
        langsmith.set_project = set_project
        
    if not HAS_LANGSMITH_TAGS:
        def set_tags(tags):
            logger.debug(f"Dummy set_tags called with: {tags}")
        langsmith.set_tags = set_tags
        
except ImportError:
    HAS_LANGSMITH = False
    logger.warning("LangSmith not installed, tracing disabled")
    
    # Create a dummy langsmith module with dummy methods
    class DummyLangsmith:
        @staticmethod
        def set_project(name):
            logger.debug(f"Dummy set_project called with: {name}")
            
        @staticmethod
        def set_tags(tags):
            logger.debug(f"Dummy set_tags called with: {tags}")
    
    langsmith = DummyLangsmith()
    
# Function decorator for traceability
def traceable(run_type="chain"):
    """
    Decorator that mimics the LangSmith traceable decorator.
    If LangSmith is available, it will use it, otherwise it will just execute the function.
    
    Args:
        run_type: Type of run to trace
        
    Returns:
        Function decorator
    """
    def decorator(func):
        # If LangSmith is available and has the traceable decorator
        if HAS_LANGSMITH and hasattr(langsmith, 'traceable'):
            return langsmith.traceable(run_type=run_type)(func)
        else:
            # Otherwise just return the original function
            return func
    return decorator

from fitness_agent.agent.schemas.router_schemas import (IntentType,
                                                        RouterResponse)
from fitness_agent.agent.utils.llm_utils import format_llm_response, get_llm
# Importaciones específicas del proyecto
from fitness_agent.agent.utils.prompt_utils import get_formatted_prompt

# Intentar importar los nodos especializados
try:
    from fitness_agent.agent.nodes.exercise_node import exercise_node
    HAS_EXERCISE_NODE = True
    logger.info("Successfully imported exercise_node")
except ImportError as e:
    HAS_EXERCISE_NODE = False
    logger.warning(f"Could not import exercise_node: {e}")

try:
    from fitness_agent.agent.nodes.nutrition_node import nutrition_node
    HAS_NUTRITION_NODE = True
    logger.info("Successfully imported nutrition_node")
except ImportError as e:
    HAS_NUTRITION_NODE = False
    logger.warning(f"Could not import nutrition_node: {e}")

try:
    from fitness_agent.agent.nodes.progress_node import progress_node
    HAS_PROGRESS_NODE = True
    logger.info("Successfully imported progress_node")
except ImportError as e:
    HAS_PROGRESS_NODE = False
    logger.warning(f"Could not import progress_node: {e}")

# Importar herramientas
try:
    from fitness_agent.agent.tools.exercise_tools import get_recent_exercises
    HAS_TOOLS = True
    logger.info("Successfully imported exercise tools")
except ImportError as e:
    HAS_TOOLS = False
    logger.warning(f"Could not import exercise tools: {e}")

class MessageResponse:
    """Clase para contener la respuesta del agente."""
    def __init__(self, content: str):
        self.content = content

@traceable(run_type="tool")
def determine_intent(message: str) -> RouterResponse:
    """
    Determina la intención del mensaje del usuario usando el LLM
    y valida el resultado con el esquema Pydantic.
    
    Args:
        message: Texto del mensaje del usuario
        
    Returns:
        RouterResponse: Objeto con la intención detectada y metadatos
    """
    logger.info(f"Determining intent for message: '{message[:50]}...'")
    
    # Cargar el prompt desde el archivo .txt
    system_prompt = get_formatted_prompt("router", "system")
    
    try:
        # Obtener instancia del LLM
        llm = get_llm()
        
        # Preparar los mensajes para el LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Llamar al LLM
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Try to extract JSON if it's wrapped in markdown code blocks
        if "```json" in content and "```" in content.split("```json", 1)[1]:
            # Extract the JSON between the code blocks
            json_str = content.split("```json", 1)[1].split("```", 1)[0].strip()
            logger.info(f"Extracted JSON from code blocks: {json_str}")
            content = json_str
            
        # Handle JSON with or without code blocks
        try:
            json_response = json.loads(content)
            
            # Validar la intención
            intent_value = json_response.get("intent", "general")
            # Normalize the intent value
            if intent_value.lower() in ["exercise", "ejercicio", "entrenamiento"]:
                intent_value = "exercise"
            elif intent_value.lower() in ["nutrition", "nutrición", "nutricion", "alimentación", "alimentacion"]:
                intent_value = "nutrition"
            elif intent_value.lower() in ["progress", "progreso", "estadísticas", "estadisticas"]:
                intent_value = "progress"
            else:
                intent_value = "general"
                
            # Create response object
            router_response = RouterResponse(
                intent=intent_value,
                confidence=float(json_response.get("confidence", 0.0)),
                explanation=json_response.get("explanation")
            )
            
            logger.info(f"Intent determined: {router_response.intent} (confidence: {router_response.confidence})")
            return router_response
            
        except json.JSONDecodeError:
            logger.error(f"LLM did not return valid JSON: {content}")
            # Fallback para manejar respuestas mal formateadas
            # Intentar extraer la intención del texto plano
            content_lower = content.lower()
            
            if "exercise" in content_lower or "ejercicio" in content_lower:
                intent = "exercise"
            elif "nutrition" in content_lower or "nutricion" in content_lower or "nutrición" in content_lower:
                intent = "nutrition"
            elif "progress" in content_lower or "progreso" in content_lower:
                intent = "progress"
            else:
                intent = "general"
                
            return RouterResponse(
                intent=intent,
                confidence=0.5,
                explanation="Fallback: JSON mal formateado, extracción simple de palabras clave."
            )
    
    except Exception as e:
        logger.error(f"Error determining intent: {e}")
        # Fallback en caso de error
        return RouterResponse(
            intent="general",
            confidence=0.0,
            explanation=f"Error en la clasificación: {str(e)}"
        )

@traceable(run_type="chain")
def process_message(user_id: str, message: str) -> MessageResponse:
    """
    Router central: procesa un mensaje del usuario, determina la intención
    y lo dirige al nodo especializado correspondiente.
    
    Args:
        user_id: ID del usuario
        message: Mensaje del usuario
        
    Returns:
        MessageResponse: Objeto con la respuesta del nodo especializado
    """
    logger.info(f"Router processing message from user {user_id}: '{message[:50]}...'")
    
    # Configurar LangSmith
    try:
        project_name = os.getenv("LANGSMITH_PROJECT", "gym")
        langsmith.set_project(project_name)
        langsmith.set_tags([f"user:{user_id}"])
    except Exception as e:
        logger.error(f"Error configuring LangSmith: {e}")
    
    # Determinar la intención del mensaje
    router_response = determine_intent(message)
    intent = router_response.intent
    logger.info(f"Detected intent: {intent} (confidence: {router_response.confidence})")
    
    # Añadir etiqueta de intención para LangSmith
    try:
        langsmith.set_tags([intent])
    except Exception as e:
        logger.error(f"Error adding LangSmith tag: {e}")
    
    # Enrutar al nodo especializado según la intención
    try:
        # Create a generic state object that all nodes can use
        state = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "current_node": intent,
            "context": {},
            "session": {}
        }
        
        if intent == "exercise" and HAS_EXERCISE_NODE:
            result = exercise_node(state)
            response_content = result.get("messages", [{}])[0].get("content", "")
        elif intent == "nutrition" and HAS_NUTRITION_NODE:
            result = nutrition_node(state)
            response_content = result.get("messages", [{}])[0].get("content", "")
        elif intent == "progress" and HAS_PROGRESS_NODE:
            result = progress_node(state)
            response_content = result.get("messages", [{}])[0].get("content", "")
        else:
            # If intent is progress but we don't have the node, see if we can extract exercise name
            if intent == "progress" and not HAS_PROGRESS_NODE:
                try:
                    from fitness_agent.agent.nodes.progress_node import \
                        extract_exercise_name
                    exercise_name = extract_exercise_name(message)
                    
                    if exercise_name and HAS_TOOLS:
                        try:
                            recent_data = get_recent_exercises(user_id, days=60, exercise_name=exercise_name)
                            
                            system_prompt = (
                                f"Eres un asistente de fitness especializado en análisis de progreso. "
                                f"El usuario está preguntando sobre su historial de {exercise_name}. "
                                f"Datos disponibles: {recent_data}"
                            )
                        except ImportError:
                            system_prompt = get_formatted_prompt("general", "system")
                    else:
                        system_prompt = get_formatted_prompt("general", "system")
                except ImportError:
                    system_prompt = get_formatted_prompt("general", "system")
            else:
                # Manejo general si no hay un nodo específico o no está disponible
                system_prompt = get_formatted_prompt("general", "system")
            
            # Get LLM instance
            llm = get_llm()
            
            # Create messages for the LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Call the LLM
            response = llm.invoke(messages)
            response_content = response.content
            
            # If it's a fallback response, provide a more specific message
            if "fallback mode" in response_content:
                response_content = (
                    "Lo siento, no puedo procesar tu consulta en este momento. "
                    "El sistema está en mantenimiento."
                )
    except Exception as e:
        logger.error(f"Error routing to node: {e}")
        response_content = "Ha ocurrido un error procesando tu mensaje. Por favor, inténtalo de nuevo."
    
    logger.info(f"Router generated response via {intent} node")
    
    return MessageResponse(response_content)