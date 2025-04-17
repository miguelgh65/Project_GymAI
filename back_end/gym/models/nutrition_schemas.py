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
    ingredients: Optional[str] = None # Campo texto general, si se usa
    calories: Optional[float] = None # Cambiado a float para consistencia
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
    calories: Optional[float] = None # Cambiado a float
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
# (Sin cambios aquí, asumiendo que está bien)
class MealIngredientBase(BaseModel):
    meal_id: int
    ingredient_id: int
    quantity: float  # en gramos

class MealIngredientCreate(MealIngredientBase):
    pass

class MealIngredientUpdate(BaseModel):
    meal_id: Optional[int] = None
    ingredient_id: Optional[int] = None
    quantity: Optional[float] = None

class MealIngredientResponse(MealIngredientBase):
    id: int
    ingredient_name: Optional[str] = None
    meal_name: Optional[str] = None


#############################################
# MODELOS PARA PLANES DE COMIDA
#############################################

class DayOfWeek(str, Enum): # CAMBIADO a str
    """Días de la semana como strings."""
    Lunes = "Lunes"
    Martes = "Martes"
    Miércoles = "Miércoles" # Ojo con acentos si vienen del frontend
    Jueves = "Jueves"
    Viernes = "Viernes"
    Sábado = "Sábado" # Ojo con acentos
    Domingo = "Domingo"

class MealTime(str, Enum): # CAMBIADO a str y valores
    """Momentos del día para las comidas."""
    Desayuno = "Desayuno"
    Almuerzo = "Almuerzo"
    Comida = "Comida"
    Merienda = "Merienda"
    Cena = "Cena"
    Otro = "Otro" # Añadir 'Otro' si tu frontend lo usa

class MealPlanBase(BaseModel):
    """Modelo base para planes de comida."""
    plan_name: str = Field(..., min_length=1) # Asegurar que no esté vacío
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    # *** AÑADIDO: Campos de targets y goal ***
    target_calories: Optional[int] = Field(default=None, ge=0)
    target_protein_g: Optional[float] = Field(default=None, ge=0)
    target_carbs_g: Optional[float] = Field(default=None, ge=0)
    target_fat_g: Optional[float] = Field(default=None, ge=0)
    goal: Optional[str] = None # Considerar usar el Enum Goal si aplica aquí

# --- NUEVO MODELO: Para los items que llegan en la petición ---
class MealPlanItemInput(BaseModel):
    """Modelo para un item dentro de la lista 'items' al crear/actualizar un plan."""
    meal_id: int
    # --- Decide cómo quieres que el frontend envíe el día ---
    # Opción 1: Fecha exacta (preferido si el plan tiene start/end date)
    plan_date: date # Hacerlo obligatorio si usas esta opción
    # Opción 2: Día de la semana (si el plan es genérico semanal)
    # day_of_week: DayOfWeek # Hacerlo obligatorio si usas esta opción
    # --- Fin opciones día ---
    meal_type: MealTime # Tipo de comida (Desayuno, etc.)
    quantity: float = Field(..., ge=0) # Cantidad obligatoria y >= 0
    unit: Optional[str] = 'g'
    notes: Optional[str] = None
    # No se incluye meal_plan_id ni id (del item) aquí

class MealPlanCreate(MealPlanBase):
    """Modelo para crear un nuevo plan de comida. Ahora incluye items."""
    # *** CORRECCIÓN: Añadir el campo items ***
    items: List[MealPlanItemInput] = Field(default_factory=list)

class MealPlanUpdate(BaseModel):
    """Modelo para actualizar un plan de comida."""
    plan_name: Optional[str] = Field(default=None, min_length=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    target_calories: Optional[int] = Field(default=None, ge=0)
    target_protein_g: Optional[float] = Field(default=None, ge=0)
    target_carbs_g: Optional[float] = Field(default=None, ge=0)
    target_fat_g: Optional[float] = Field(default=None, ge=0)
    goal: Optional[str] = None
    # *** AÑADIDO: Items opcionales para reemplazo total ***
    items: Optional[List[MealPlanItemInput]] = None # None significa no tocar items existentes

class MealPlanResponse(MealPlanBase):
    """Modelo para respuesta con un plan de comida completo."""
    id: int
    user_id: str # O int si user_id es numérico en tu DB/modelo User
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


#############################################
# MODELOS PARA ELEMENTOS DE PLAN DE COMIDA (RESPUESTAS/BASE DB)
#############################################

class MealPlanItemBase(BaseModel):
    """Modelo base para elementos de un plan de comida (DB/Respuesta)."""
    # Campos que existen en la tabla meal_plan_items
    meal_plan_id: int
    meal_id: int
    plan_date: Optional[date] = None # Si guardas fecha exacta en DB
    day_of_week: Optional[str] = None # Si guardas día como string en DB (ej 'Lunes')
    # CAMBIO: Renombrar meal_time a meal_type para consistencia con frontend/input
    meal_type: Optional[str] = None # El tipo/momento de comida ('Desayuno', etc.)
    quantity: float = 100.0
    unit: Optional[str] = 'g'
    notes: Optional[str] = None

class MealPlanItemCreate(MealPlanItemBase):
    """Modelo para crear un nuevo elemento directamente (si tuvieras un endpoint específico)."""
    # Este modelo probablemente NO se use si creas items junto con el plan
    pass

class MealPlanItemUpdate(BaseModel):
    """Modelo para actualizar un elemento específico (si tuvieras endpoint para ello)."""
    # Todos opcionales
    meal_plan_id: Optional[int] = None
    meal_id: Optional[int] = None
    plan_date: Optional[date] = None
    day_of_week: Optional[str] = None # O int si usas números
    meal_type: Optional[str] = None
    quantity: Optional[float] = Field(default=None, ge=0)
    unit: Optional[str] = None
    notes: Optional[str] = None

class MealPlanItemResponse(MealPlanItemBase):
    """Modelo para respuesta con un elemento de plan de comida completo."""
    id: int # El ID único de la tabla meal_plan_items
    # Campos adicionales que podrían venir de JOINs
    meal_name: Optional[str] = None
    calories: Optional[float] = None # Macros calculados para la cantidad dada
    protein_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    fat_g: Optional[float] = None
    # timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MealPlanWithItems(MealPlanResponse):
    """Modelo para plan de comida con todos sus elementos incluidos en la respuesta."""
    items: List[MealPlanItemResponse] = [] # Usa el modelo de respuesta para items