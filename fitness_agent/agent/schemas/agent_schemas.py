# fitness-agent/agent/schemas/agent_schemas.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    DECISION = "decision"
    EXERCISE = "exercise"
    NUTRITION = "nutrition"
    FITBIT = "fitbit"

class Message(BaseModel):
    role: str
    content: str
    
    class Config:
        frozen = True

class AgentState(BaseModel):
    """Estado del agente durante la conversación."""
    messages: List[Message] = Field(default_factory=list)
    user_id: str
    current_node: NodeType = NodeType.DECISION
    context: Dict[str, Any] = Field(default_factory=dict)
    session: Dict[str, Any] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    """Respuesta formateada del agente."""
    content: str
    source_node: NodeType
    timestamp: datetime = Field(default_factory=datetime.now)
    additional_data: Optional[Dict[str, Any]] = None