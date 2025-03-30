import os
import json
import logging
from typing import Dict, Any
import datetime

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
from fitness_agent.agent.schemas.router_schemas import RouterResponse, IntentType
from fitness_agent.agent.utils.prompt_utils import get_formatted_prompt
from fitness_agent.agent.utils.llm_utils import get_llm

# Intentar importar los nodos especializados
try:
    from fitness_agent.agent.nodes.exercise_node import exercise_node
    from fitness_agent.agent.nodes.nutrition_node import nutrition_node
    # Importar otros nodos según sea necesario
    HAS_NODES = True
except ImportError as e:
    logger.warning(f"Could not import specialized nodes: {e}")
    HAS_NODES = False

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
        
        # Intentar parsear el JSON de la respuesta
        try:
            json_response = json.loads(content)
            
            # Validar con el esquema Pydantic
            router_response = RouterResponse(
                intent=json_response.get("intent", "general"),
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
            
            if "exercise" in content_lower:
                intent = "exercise"
            elif "nutrition" in content_lower:
                intent = "nutrition"
            elif "progress" in content_lower:
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
    
    # Configurar LangSmith si está disponible
    if HAS_LANGSMITH:
        try:
            project_name = os.getenv("LANGSMITH_PROJECT", "gym")
            langsmith.set_project(project_name)
            langsmith.set_tags([f"user:{user_id}"])
        except Exception as e:
            logger.error(f"Error configuring LangSmith: {e}")
    
    # Crear el estado inicial
    state = AgentState({
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id,
        "current_node": None,
        "context": {},
        "session": {}
    })
    
    # Determinar la intención del mensaje
    router_response = determine_intent(message)
    intent = router_response.intent
    logger.info(f"Detected intent: {intent} (confidence: {router_response.confidence})")
    
    # Actualizar el nodo actual en el estado
    state["current_node"] = intent
    
    # Añadir etiqueta de intención para LangSmith
    if HAS_LANGSMITH:
        try:
            langsmith.set_tags([intent])
        except Exception as e:
            logger.error(f"Error adding LangSmith tag: {e}")
    
    # Enrutar al nodo especializado según la intención
    try:
        if HAS_NODES:
            if intent == IntentType.EXERCISE:
                node_result = exercise_node(state)
                response_content = node_result.get("messages", [{}])[0].get("content", "")
            elif intent == IntentType.NUTRITION:
                node_result = nutrition_node(state)
                response_content = node_result.get("messages", [{}])[0].get("content", "")
            # Añadir otros nodos según sea necesario
            else:
                # Manejo general si no hay un nodo específico
                response_content = "No tengo un módulo especializado para responder a esa consulta. ¿Puedes preguntarme sobre ejercicios o nutrición?"
        else:
            # Fallback si fallan las importaciones
            response_content = "Lo siento, no puedo procesar tu consulta en este momento. El sistema está en mantenimiento."
    except Exception as e:
        logger.error(f"Error routing to node: {e}")
        response_content = "Ha ocurrido un error procesando tu mensaje. Por favor, inténtalo de nuevo."
    
    logger.info(f"Router generated response via {intent} node")
    
    return MessageResponse(response_content)