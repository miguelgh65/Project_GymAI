# back_end/gym/models/tracking_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime

class CompletedMeals(BaseModel):
    """Modelo para los estados de comidas completadas del día."""
    Desayuno: Optional[bool] = False
    Almuerzo: Optional[bool] = False
    Comida: Optional[bool] = False
    Merienda: Optional[bool] = False
    Cena: Optional[bool] = False
    Otro: Optional[bool] = False

class DailyTrackingCreate(BaseModel):
    """Modelo para crear/actualizar datos de seguimiento diario."""
    tracking_date: date
    completed_meals: CompletedMeals
    calorie_note: Optional[str] = None
    actual_calories: Optional[int] = None
    excess_deficit: Optional[int] = None

class DailyTrackingResponse(BaseModel):
    """Modelo para respuesta de seguimiento diario."""
    id: int
    user_id: str
    tracking_date: date
    completed_meals: Dict[str, bool]
    calorie_note: Optional[str] = None
    actual_calories: Optional[int] = None
    excess_deficit: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class WeeklyTrackingSummary(BaseModel):
    """Modelo para el resumen semanal de seguimiento."""
    total_days_tracked: int = 0
    average_calories: float = 0
    total_excess_deficit: int = 0
    meals_completion: Dict[str, int] = Field(
        default_factory=lambda: {
            "Desayuno": 0,
            "Almuerzo": 0,
            "Comida": 0,
            "Merienda": 0,
            "Cena": 0
        }
    )