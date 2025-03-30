from pydantic import BaseModel, Field, model_validator
from enum import Enum
from typing import Optional, List, Dict, Any

class IntentType(str, Enum):
    """Tipos de intención que puede detectar el router."""
    EXERCISE = "exercise"
    NUTRITION = "nutrition"
    PROGRESS = "progress"
    GENERAL = "general"

class RouterResponse(BaseModel):
    """Esquema para la respuesta del router."""
    intent: IntentType = Field(..., description="Intención detectada en el mensaje del usuario")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza en la clasificación (0-1)")
    explanation: Optional[str] = Field(None, description="Explicación de por qué se eligió esta intención")

    @model_validator(mode='after')
    def check_confidence_threshold(self):
        """Verifica que la confianza sea suficiente para clasificar con seguridad."""
        if self.confidence < 0.7 and self.intent != IntentType.GENERAL:
            # Si la confianza es baja, defaultear a GENERAL
            self.intent = IntentType.GENERAL
            if not self.explanation:
                self.explanation = "Confianza demasiado baja para determinar la intención específica."
        return self

class RouterRequest(BaseModel):
    """Esquema para la solicitud al router."""
    message: str = Field(..., description="Mensaje del usuario")
    user_id: str = Field(..., description="ID del usuario")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")