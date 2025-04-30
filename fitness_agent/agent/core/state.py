# fitness-agent/agent/core/state.py
from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Estado del agente de fitness."""
    # Historial de mensajes (usando el reducer add_messages para mantener el historial)
    messages: Annotated[list, add_messages]
    
    # Información sobre el usuario actual
    user_id: str
    
    # Nodo actual en el grafo de decisión
    current_node: str
    
    # Contexto compartido entre nodos (datos de usuario, preferencias, etc)
    context: Dict[str, Any]
    
    # Información de la sesión actual
    session: Dict[str, Any]