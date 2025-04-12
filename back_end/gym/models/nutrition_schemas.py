# back_end/gym/models/nutrition_schemas.py
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, List, Dict, Union, Any
from datetime import datetime, date

#############################################
# MODELOS DE CALCULADORA DE MACROS Y PERFILES
#############################################

class Units(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

class Formula(str, Enum):
    MIFFLIN_ST_JEOR = "mifflin_st_jeor"
    HARRIS_BENEDICT = "harris_benedict"
    WHO = "who"
    KATCH_MCARDLE = "katch_mcardle"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"  # 1.2
    LIGHT = "light"          # 1.375
    MODERATE = "moderate"    # 1.55
    ACTIVE = "active"        # 1.725
    VERY_ACTIVE = "very_active"  # 1.9

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class Goal(str, Enum):
    MAINTAIN = "maintain"
    LOSE = "lose"
    GAIN = "gain"

class GoalIntensity(str, Enum):
    NORMAL = "normal"    # ±300-500 kcal
    AGGRESSIVE = "aggressive"  # ±500-1000 kcal

class MacroCalculatorInput(BaseModel):
    units: Units
    formula: Formula
    gender: Gender
    age: int
    height: float  # cm or inches
    weight: float  # kg or pounds
    body_fat_percentage: Optional[float] = None
    activity_level: ActivityLevel
    goal: Goal
    goal_intensity: GoalIntensity

class MacroCalculatorResult(BaseModel):
    bmr: float
    tdee: float
    bmi: float
    goal_calories: int
    macros: Dict[str, Dict[str, Union[float, int]]]


#############################################
# MODELOS PARA GESTIÓN DE INGREDIENTES
#############################################

class IngredientBase(BaseModel):
    """Modelo base para ingredientes con los campos comunes."""
    ingredient_name: str
    calories: float
    proteins: float
    carbohydrates: float
    fats: float

class IngredientCreate(IngredientBase):
    """Modelo para crear un nuevo ingrediente."""
    pass

class IngredientUpdate(BaseModel):
    """Modelo para actualizar un ingrediente (todos los campos opcionales)."""
    ingredient_name: Optional[str] = None
    calories: Optional[float] = None
    proteins: Optional[float] = None
    carbohydrates: Optional[float] = None
    fats: Optional[float] = None

class IngredientResponse(IngredientBase):
    """Modelo para respuesta con un ingrediente completo."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


#############################################
# MODELOS PARA GESTIÓN DE COMIDAS (MEALS)
#############################################

class MealBase(BaseModel):
    """Modelo base para comidas con los campos comunes."""
    meal_name: str
    recipe: Optional[str] = None
    ingredients: Optional[str] = None
    calories: Optional[int] = None
    proteins: Optional[float] = None
    carbohydrates: Optional[float] = None
    fats: Optional[float] = None
    image_url: Optional[str] = None

class MealCreate(MealBase):
    """Modelo para crear una nueva comida."""
    pass

class MealUpdate(BaseModel):
    """Modelo para actualizar una comida (todos los campos opcionales)."""
    meal_name: Optional[str] = None
    recipe: Optional[str] = None
    ingredients: Optional[str] = None
    calories: Optional[int] = None
    proteins: Optional[float] = None
    carbohydrates: Optional[float] = None
    fats: Optional[float] = None
    image_url: Optional[str] = None

class MealResponse(MealBase):
    """Modelo para respuesta con una comida completa."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


#############################################
# MODELOS PARA RELACIÓN MEAL-INGREDIENT
#############################################

class MealIngredientBase(BaseModel):
    """Modelo base para la relación entre comidas e ingredientes."""
    meal_id: int
    ingredient_id: int
    quantity: float  # en gramos

class MealIngredientCreate(MealIngredientBase):
    """Modelo para crear una nueva relación comida-ingrediente."""
    pass

class MealIngredientUpdate(BaseModel):
    """Modelo para actualizar una relación comida-ingrediente."""
    meal_id: Optional[int] = None
    ingredient_id: Optional[int] = None
    quantity: Optional[float] = None

class MealIngredientResponse(MealIngredientBase):
    """Modelo para respuesta con una relación comida-ingrediente completa."""
    id: int
    ingredient_name: Optional[str] = None
    meal_name: Optional[str] = None


#############################################
# MODELOS PARA PLANES DE COMIDA
#############################################

class DayOfWeek(int, Enum):
    """Días de la semana representados como enteros (1=Lunes a 7=Domingo)."""
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

class MealTime(str, Enum):
    """Momentos del día para las comidas."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

class MealPlanBase(BaseModel):
    """Modelo base para planes de comida."""
    plan_name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_active: bool = True

class MealPlanCreate(MealPlanBase):
    """Modelo para crear un nuevo plan de comida."""
    pass

class MealPlanUpdate(BaseModel):
    """Modelo para actualizar un plan de comida."""
    plan_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class MealPlanResponse(MealPlanBase):
    """Modelo para respuesta con un plan de comida completo."""
    id: int
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


#############################################
# MODELOS PARA ELEMENTOS DE PLAN DE COMIDA
#############################################

class MealPlanItemBase(BaseModel):
    """Modelo base para elementos de un plan de comida."""
    meal_plan_id: int
    meal_id: int
    day_of_week: DayOfWeek
    meal_time: MealTime
    quantity: Optional[float] = 1.0
    notes: Optional[str] = None

class MealPlanItemCreate(MealPlanItemBase):
    """Modelo para crear un nuevo elemento en un plan de comida."""
    pass

class MealPlanItemUpdate(BaseModel):
    """Modelo para actualizar un elemento en un plan de comida."""
    meal_plan_id: Optional[int] = None
    meal_id: Optional[int] = None
    day_of_week: Optional[DayOfWeek] = None
    meal_time: Optional[MealTime] = None
    quantity: Optional[float] = None
    notes: Optional[str] = None

class MealPlanItemResponse(MealPlanItemBase):
    """Modelo para respuesta con un elemento de plan de comida completo."""
    id: int
    meal_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MealPlanWithItems(MealPlanResponse):
    """Modelo para plan de comida con todos sus elementos incluidos."""
    items: List[MealPlanItemResponse] = []