# Archivo: workflows/gym/services/langgraph_agent/state.py

from typing import Annotated, Dict, TypedDict
from langgraph.graph.message import add_messages

class ChatbotState(TypedDict):
    """Estado del agente chatbot de entrenamiento."""
    # Historial de mensajes (usando el reducer add_messages para mantener el historial)
    messages: Annotated[list, add_messages]
    
    # Información sobre el usuario actual
    user_id: str
    
    # Contexto del entrenamiento y nutrición
    context: Dict[str, any]
    
    # Información de la sesión actual
    session: Dict[str, any]