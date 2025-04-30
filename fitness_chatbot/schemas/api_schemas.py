from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Esquema para solicitudes de chat"""
    message: str = Field(..., description="Mensaje del usuario")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")

class ChatResponse(BaseModel):
    """Esquema para respuestas de chat"""
    response: str = Field(..., description="Respuesta generada por el chatbot")
    intent: str = Field(..., description="Intención detectada")