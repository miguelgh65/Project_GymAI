# fitness-agent/agent/nodes/exercise_node.py
import os
import langsmith
from typing import Dict, Any

from fitness_agent.agent.core.state import AgentState
from fitness_agent.agent.schemas import TraceMetadata, NodeType

def exercise_node(state: AgentState) -> Dict[str, Any]:
    """
    Nodo especializado en consultas relacionadas con ejercicios y entrenamiento.
    
    Args:
        state: Estado actual del agente
        
    Returns:
        Estado actualizado con la respuesta del nodo
    """
    try:
        # Preparar mensaje para el LLM
        messages = state["messages"]
        user_id = state["user_id"]
        
        # Configurar trazado LangSmith
        langsmith.set_project("gym")
        trace_metadata = TraceMetadata(
            project_name="gym",
            user_id=user_id,
            session_id=str(hash(frozenset(state.items()))),
            node_type=NodeType.EXERCISE
        )
        
        with langsmith.trace(
            name="exercise_node",
            metadata=trace_metadata.dict()
        ):
            # Añadir contexto específico de ejercicios
            system_message = {
                "role": "system",
                "content": """
                Eres un entrenador personal especializado en ejercicios y entrenamiento.
                
                Puedes ayudar con:
                - Programación de entrenamientos
                - Técnicas correctas de ejercicios
                - Progresión de fuerza y volumen
                - Recuperación muscular
                - Rutinas de entrenamiento
                
                Utiliza las herramientas disponibles para acceder a datos del usuario 
                cuando sea necesario. Si necesitas información específica sobre entrenamientos
                previos del usuario, usa la herramienta get_recent_exercises.
                
                Sé específico, claro y conciso en tus respuestas.
                """
            }
            
            # Si es el primer mensaje, agregar el mensaje de sistema
            if len(messages) <= 1:
                enriched_messages = [system_message] + messages
            else:
                enriched_messages = messages
            
            # Aquí usaríamos el LLM configurado con herramientas específicas de ejercicio
            from fitness_agent.agent.core.decisor import llm_exercise
            
            response = llm_exercise.invoke(enriched_messages)
            
            # Devolver la actualización del estado con la respuesta
            return {"messages": [response]}
    
    except Exception as e:
        # En caso de error, devolver un mensaje amigable
        error_message = {
            "role": "assistant",
            "content": f"Lo siento, ocurrió un error al procesar tu consulta sobre ejercicios. Por favor, inténtalo de nuevo con otra pregunta. Error: {str(e)}"
        }
        return {"messages": [error_message]}