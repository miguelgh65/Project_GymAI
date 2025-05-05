# fitness_chatbot/schemas/routine_schemas.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ExerciseSchema(BaseModel):
    """Esquema para un ejercicio en una rutina"""
    nombre: str = Field(..., description="Nombre del ejercicio")
    series: Optional[int] = Field(None, description="Número de series")
    repeticiones: Optional[int] = Field(None, description="Número de repeticiones")
    peso: Optional[float] = Field(None, description="Peso en kg")
    notas: Optional[str] = Field(None, description="Notas adicionales")

class RoutineSchema(BaseModel):
    """Esquema para una rutina de entrenamiento"""
    dia_semana: int = Field(..., description="Día de la semana (1=lunes, 7=domingo)")
    ejercicios: List[str] = Field(default_factory=list, description="Lista de ejercicios")
    nombre: Optional[str] = Field(None, description="Nombre de la rutina")

class RoutineResponseSchema(BaseModel):
    """Esquema para la respuesta de la API de rutina"""
    success: bool = Field(..., description="Indica si la solicitud fue exitosa")
    rutina: Optional[RoutineSchema] = Field(None, description="Datos de la rutina")
    message: Optional[str] = Field(None, description="Mensaje informativo")