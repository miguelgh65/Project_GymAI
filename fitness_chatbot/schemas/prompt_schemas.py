from pydantic import BaseModel, Field
from typing import List, Optional

class IntentClassification(BaseModel):
    """Esquema para la clasificación de intención"""
    intent: str = Field(..., description="Intención detectada (exercise, nutrition, progress, log_activity, general)")
    explanation: Optional[str] = Field(None, description="Explicación de la clasificación")

class ExerciseSet(BaseModel):
    """Esquema para conjuntos de ejercicios"""
    reps: int = Field(..., description="Número de repeticiones", ge=0)
    weight: float = Field(..., description="Peso en kg", ge=0)

class LoggedExercise(BaseModel):
    """Esquema para ejercicios registrados"""
    type: str = Field("exercise", description="Tipo de actividad")
    exercise_name: str = Field(..., description="Nombre del ejercicio")
    sets: List[ExerciseSet] = Field(..., description="Series realizadas")
    date: Optional[str] = Field(None, description="Fecha (YYYY-MM-DD)")

class LoggedNutrition(BaseModel):
    """Esquema para registros de nutrición"""
    type: str = Field("nutrition", description="Tipo de actividad")
    meal_type: str = Field(..., description="Tipo de comida (desayuno, almuerzo, cena, etc.)")
    foods: List[str] = Field(default_factory=list, description="Alimentos consumidos")
    calories: Optional[int] = Field(None, description="Calorías totales")
    protein: Optional[int] = Field(None, description="Gramos de proteína")