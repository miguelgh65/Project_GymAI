from typing import Annotated, List, Dict, TypedDict
from langgraph.graph import add_messages

# Estado para mantener conversación
class MemoryState(TypedDict):
    """Estado para el historial de conversación"""
    messages: Annotated[List[Dict[str, str]], add_messages]