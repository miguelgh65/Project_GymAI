# Archivo: workflows/gym/services/langgraph_agent/nodes.py

from typing import Dict, Any
from config import llm
from services.langgraph_agent.state import ChatbotState

def chatbot_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Nodo principal del chatbot que procesa los mensajes del usuario.
    
    Args:
        state: Estado actual del chatbot
        
    Returns:
        Actualización del estado con la respuesta del LLM
    """
    try:
        # Preparar mensajes para el LLM
        messages = state["messages"]
        
        # Agregar contexto si es necesario
        if state["context"] and len(messages) <= 1:
            user_id = state["user_id"]
            context_message = {
                "role": "system",
                "content": f"""
                Eres un asistente de entrenamiento personal inteligente. 
                ID de usuario actual: {user_id}
                
                Puedes ayudar al usuario con las siguientes tareas:
                - Ver su rutina de entrenamiento
                - Obtener estadísticas sobre su progreso
                - Recibir sugerencias de comidas según sus objetivos
                - Recibir sugerencias para progresar en sus ejercicios
                
                Usa las herramientas disponibles para acceder a la información del usuario.
                """
            }
            messages = [context_message] + messages
        
        # Invocar el LLM con herramientas
        response = llm.invoke(messages)
        
        # Devolver la actualización del estado
        return {"messages": [response]}
    except Exception as e:
        # En caso de error, devolver un mensaje amigable
        error_message = {
            "role": "assistant",
            "content": f"Lo siento, ocurrió un error al procesar tu mensaje. Por favor, inténtalo de nuevo. Error: {str(e)}"
        }
        return {"messages": [error_message]}