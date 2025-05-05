# fitness_chatbot/schemas/progress_schemas.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ExerciseSet(BaseModel):
    """Representación de una serie de un ejercicio"""
    repeticiones: int = Field(..., description="Número de repeticiones")
    peso: float = Field(..., description="Peso en kg")

class ExerciseSession(BaseModel):
    """Representación de una sesión de entrenamiento para un ejercicio específico"""
    fecha: datetime = Field(..., description="Fecha y hora del ejercicio")
    ejercicio: str = Field(..., description="Nombre del ejercicio")
    repeticiones: List[ExerciseSet] = Field(default_factory=list, description="Series realizadas")
    
    class Config:
        arbitrary_types_allowed = True

class ProgressMetrics(BaseModel):
    """Métricas de progreso calculadas para un ejercicio"""
    ejercicio: str = Field(..., description="Nombre del ejercicio")
    primera_sesion: datetime = Field(..., description="Fecha primera sesión registrada")
    ultima_sesion: datetime = Field(..., description="Fecha última sesión registrada")
    sesiones_totales: int = Field(..., description="Número total de sesiones")
    peso_maximo_historico: float = Field(..., description="Peso máximo histórico")
    rm_estimado_primera: Optional[float] = Field(None, description="1RM estimado en primera sesión")
    rm_estimado_ultima: Optional[float] = Field(None, description="1RM estimado en última sesión")
    variacion_porcentual: Optional[float] = Field(None, description="Variación porcentual en rendimiento")
    
    class Config:
        arbitrary_types_allowed = True

class MuscleGroupBalance(BaseModel):
    """Balance entre grupos musculares"""
    grupo_muscular: str = Field(..., description="Nombre del grupo muscular")
    ejercicios: List[str] = Field(default_factory=list, description="Ejercicios para este grupo")
    volumen_semanal: Optional[float] = Field(None, description="Volumen semanal estimado")
    sets_semanales: Optional[int] = Field(None, description="Sets semanales estimados")
    nivel_equilibrio: Optional[str] = Field(None, description="Nivel de equilibrio (Bajo/Adecuado/Alto)")

class ProgressAnalysis(BaseModel):
    """Análisis completo de progreso con métricas y recomendaciones"""
    metricas_principales: List[ProgressMetrics] = Field(default_factory=list, description="Métricas para ejercicios principales")
    equilibrio_muscular: List[MuscleGroupBalance] = Field(default_factory=list, description="Balance entre grupos musculares")
    estado_general: str = Field(..., description="Estado general de progreso")
    recomendaciones: List[str] = Field(default_factory=list, description="Recomendaciones específicas")
    
    class Config:
        schema_extra = {
            "example": {
                "metricas_principales": [
                    {
                        "ejercicio": "press banca",
                        "primera_sesion": "2023-01-15T10:30:00",
                        "ultima_sesion": "2023-04-15T11:15:00",
                        "sesiones_totales": 12,
                        "peso_maximo_historico": 100.0,
                        "rm_estimado_primera": 80.5,
                        "rm_estimado_ultima": 112.5,
                        "variacion_porcentual": 39.8
                    }
                ],
                "equilibrio_muscular": [
                    {
                        "grupo_muscular": "pecho",
                        "ejercicios": ["press banca", "aperturas"],
                        "volumen_semanal": 7500.0,
                        "sets_semanales": 12,
                        "nivel_equilibrio": "Adecuado"
                    }
                ],
                "estado_general": "Positivo con oportunidades de mejora",
                "recomendaciones": [
                    "Incrementar volumen en espalda para equilibrar con pecho",
                    "Aumentar frecuencia de entrenamiento de piernas a 2x semana",
                    "Implementar periodización para romper meseta en press militar"
                ]
            }
        }