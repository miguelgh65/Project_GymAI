# fitness_agent/agent/nodes/fitbit_node.py
import logging
from typing import Any, Dict

from fitness_agent.agent.core.state import AgentState
from fitness_agent.agent.utils.llm_utils import format_llm_response, get_llm
from fitness_agent.agent.utils.prompt_utils import get_formatted_prompt

logger = logging.getLogger(__name__)

def fitbit_node(state: AgentState) -> Dict[str, Any]:
    """
    Nodo genérico para consultas de Fitbit.
    
    Args:
        state: Estado actual del agente
    
    Returns:
        Estado actualizado con respuesta de Fitbit
    """
    try:
        # Extraer mensaje del usuario
        messages = state["messages"]
        user_id = state["user_id"]
        user_message = messages[-1]["content"]
        
        # Cargar prompt de sistema con contexto genérico
        system_prompt = get_formatted_prompt(
            "fitbit", 
            "system", 
            user_context="Sin datos de Fitbit específicos"
        )
        
        # Generar respuesta usando LLM
        llm = get_llm()
        
        # Preparar mensajes para el LLM
        messages_for_llm = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Llamar al LLM
        response = llm.invoke(messages_for_llm)
        content = format_llm_response(response.content)
        
        # Crear mensaje de respuesta
        response_message = {
            "role": "assistant",
            "content": content
        }
        
        # Registrar actividad
        logger.info(f"Fitbit node generated response: {content[:100]}...")
        
        # Devolver estado actualizado
        return {"messages": [response_message]}
    
    except Exception as e:
        logger.error(f"Error in fitbit_node: {e}")
        
        # Mensaje de error
        error_message = {
            "role": "assistant",
            "content": "Lo siento, ocurrió un error al procesar tu consulta de Fitbit. Por favor, inténtalo de nuevo."
        }
        
        return {"messages": [error_message]}