# fitness_chatbot/nodes/router_node.py
import logging
import json
from typing import Tuple, Dict, Any, Optional

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
    
    # Comprobar si hay una intención ya definida (para llamadas directas a nodos específicos)
    if agent_state.get("intent"):
        logger.info(f"Intención ya definida: {agent_state['intent']}")
        
        # Actualizar historial de mensajes
        if "messages" not in memory_state:
            memory_state["messages"] = []
        
        memory_state["messages"].append({"role": "user", "content": query})
        
        return agent_state, memory_state
    
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

# Función auxiliar para procesar mensajes directamente (API)
async def process_message(user_id: str, message: str) -> Any:
    """
    Procesa un mensaje del usuario y devuelve una respuesta usando el grafo de fitness.
    Función auxiliar para compatibilidad con APIs antiguas.
    
    Args:
        user_id: ID del usuario
        message: Mensaje del usuario
        
    Returns:
        Objeto con la respuesta del chatbot
    """
    # Importar el grafo aquí para evitar importaciones circulares
    from fitness_chatbot.graphs.fitness_graph import create_fitness_graph
    
    try:
        # Crear estado inicial
        agent_state = AgentState(
            query=message,
            intent="",
            user_id=user_id,
            user_context={},
            intermediate_steps=[],
            retrieved_data=[],
            generation=""
        )
        
        memory_state = MemoryState(
            messages=[]
        )
        
        # Obtener el grafo de fitness
        fitness_graph = create_fitness_graph()
        
        # Invocar el grafo
        final_state = await fitness_graph.ainvoke((agent_state, memory_state))
        final_agent_state, final_memory_state = final_state
        
        # Obtener respuesta generada
        response = final_agent_state.get("generation", "")
        
        # Crear objeto de respuesta similar a MessageResponse
        class MessageResponse:
            def __init__(self, content):
                self.content = content
        
        return MessageResponse(response)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
        return MessageResponse(f"Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo más tarde.")

# Función para procesar peticiones de registro de actividad
async def process_log_request(user_id: str, activity_data: str, activity_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Procesa una solicitud de registro de actividad y devuelve el resultado.
    
    Args:
        user_id: ID del usuario
        activity_data: Datos de la actividad a registrar
        activity_type: Tipo de actividad (exercise, nutrition) si se conoce
        
    Returns:
        Dict con el resultado del registro
    """
    # Importar el grafo aquí para evitar importaciones circulares
    from fitness_chatbot.graphs.fitness_graph import create_fitness_graph
    
    try:
        # Modificar el mensaje para aclarar la intención si tenemos el tipo
        message = activity_data
        if activity_type:
            if activity_type == "exercise":
                message = f"Registra este ejercicio: {activity_data}"
            elif activity_type == "nutrition":
                message = f"Registra esta comida: {activity_data}"
        
        # Crear estado inicial con intención forzada a LOG_ACTIVITY
        agent_state = AgentState(
            query=message,
            intent=IntentType.LOG_ACTIVITY,
            user_id=user_id,
            user_context={},
            intermediate_steps=[],
            retrieved_data=[],
            generation=""
        )
        
        memory_state = MemoryState(
            messages=[]
        )
        
        # Obtener el grafo de fitness
        fitness_graph = create_fitness_graph()
        
        # Invocar el grafo
        final_state = await fitness_graph.ainvoke((agent_state, memory_state))
        final_agent_state, final_memory_state = final_state
        
        # Obtener respuesta generada
        response = final_agent_state.get("generation", "")
        
        # Detectar si el registro fue exitoso en base al texto
        success = "registrado" in response.lower() and "correctamente" in response.lower()
        
        return {
            "success": success,
            "message": response
        }
    except Exception as e:
        logger.error(f"Error procesando solicitud de registro: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Error al procesar la solicitud de registro: {str(e)}"
        }