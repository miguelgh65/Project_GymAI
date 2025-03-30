# fitness_agent/agent/nodes/progress_node.py
import json
import logging
from typing import Dict, Any, List

from fitness_agent.agent.core.state import AgentState
from fitness_agent.agent.tools.exercise_tools import get_recent_exercises
from fitness_agent.agent.utils.llm_utils import get_llm, format_llm_response
from fitness_agent.agent.utils.prompt_utils import get_formatted_prompt

logger = logging.getLogger(__name__)

def progress_node(state: AgentState) -> Dict[str, Any]:
    """
    Nodo para procesar consultas de progreso con formato LLM.
    
    Args:
        state: Estado actual del agente
    
    Returns:
        Estado actualizado con respuesta de progreso
    """
    try:
        # Extraer mensaje del usuario
        messages = state["messages"]
        user_id = state["user_id"]
        user_message = messages[-1]["content"]
        
        # Obtener prompt específico para análisis de progreso
        system_prompt = get_formatted_prompt("progress", "system")
        
        # Preparar instancia de LLM
        llm = get_llm()
        
        # Preparar los mensajes para el LLM
        messages_for_llm = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Generar comando estructurado
        response = llm.invoke(messages_for_llm)
        formatted_command = format_llm_response(response.content)
        
        # Parsear el comando
        try:
            command_data = json.loads(formatted_command)
        except json.JSONDecodeError:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "Lo siento, no pude procesar tu solicitud. Por favor, sé más específico."
                }]
            }
        
        # Extraer detalles del comando
        exercise = command_data.get('exercise', None)
        days = command_data.get('days', 90)
        analysis_type = command_data.get('analysis_type', 'basic')
        
        # Obtener ejercicios recientes
        try:
            recent_exercises_json = get_recent_exercises(
                user_id, 
                days=days, 
                exercise_name=exercise
            )
            recent_exercises = json.loads(recent_exercises_json)
        except Exception as e:
            logger.error(f"Error obteniendo ejercicios recientes: {e}")
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "Hubo un problema al recuperar tus entrenamientos."
                }]
            }
        
        # Preparar contexto para análisis final
        context = {
            "user_id": user_id,
            "exercises": recent_exercises,
            "analysis_type": analysis_type,
            "exercise": exercise
        }
        
        # Generar respuesta final basada en el análisis
        final_prompt = get_formatted_prompt(
            "progress", 
            "analysis", 
            context=json.dumps(context, ensure_ascii=False)
        )
        
        # Generar respuesta final usando LLM
        final_response = llm.invoke([
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": user_message}
        ])
        
        # Formatear y devolver respuesta
        final_content = format_llm_response(final_response.content)
        
        return {
            "messages": [{
                "role": "assistant",
                "content": final_content
            }]
        }
    
    except Exception as e:
        logger.error(f"Error en progress_node: {e}")
        
        return {
            "messages": [{
                "role": "assistant",
                "content": "Lo siento, ocurrió un error al procesar tu consulta de progreso. Por favor, inténtalo de nuevo.\n\n¡Sigue esforzándote! 💪"
            }]
        }