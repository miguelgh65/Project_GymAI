# fitness-agent/agent/schemas/__init__.py
from .agent_schemas import *
from .exercise_schemas import *
from .nutrition_schemas import *
from .fitbit_schemas import *

# fitness-agent/agent/schemas/agent_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class UserQuery(BaseModel):
    user_id: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
class NodeType(str, Enum):
    DECISION = "decision"
    EXERCISE = "exercise" 
    NUTRITION = "nutrition"
    FITBIT = "fitbit"
    
class AgentResponse(BaseModel):
    user_id: str
    content: str
    source_node: NodeType
    confidence: float = Field(..., ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None

class TraceMetadata(BaseModel):
    """Metadatos para el trazado en LangSmith."""
    project_name: str = "gym"
    user_id: str
    session_id: str
    node_type: Optional[NodeType] = None