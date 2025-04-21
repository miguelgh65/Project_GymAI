# back_end/gym/models/calculator_schemas.py
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, List, Dict, Union, Any
from datetime import datetime, date

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