# back_end/gym/models/calculator_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Distribución de macronutrientes
class MacroDistribution(BaseModel):
    protein: float = Field(..., description="Porcentaje de proteínas")
    carbs: float = Field(..., description="Porcentaje de carbohidratos")
    fat: float = Field(..., description="Porcentaje de grasas")

# Modelo para los datos de entrada de la calculadora de macros
class MacroCalculatorInput(BaseModel):
    units: str
    formula: str
    gender: str
    age: int
    height: float
    weight: float
    body_fat_percentage: Optional[float] = None
    activity_level: str
    goal: str
    goal_intensity: str
    macro_distribution: MacroDistribution

# Modelo para el perfil nutricional
class NutritionProfile(BaseModel):
    user_id: Optional[str] = None
    formula: str
    sex: str
    age: int
    height: float
    weight: float
    body_fat_percentage: Optional[float] = None
    activity_level: str
    goal: str
    goal_intensity: str
    units: str
    bmr: float
    tdee: float
    bmi: float
    daily_calories: int
    proteins_grams: int
    carbs_grams: int
    fats_grams: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Respuesta de perfil nutricional con extras
class NutritionProfileResponse(BaseModel):
    profile: NutritionProfile
    has_tracking_today: bool
    active_plan: Optional[Dict[str, Any]] = None