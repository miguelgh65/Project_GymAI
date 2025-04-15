# back_end/gym/routes/nutrition/calculator.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List, Dict, Union
import math

# Cambiar importaciones relativas a absolutas
from back_end.gym.middlewares import get_current_user
from back_end.gym.config import DB_CONFIG
import psycopg2

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])

# Enums para las diferentes opciones
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

# Modelos de datos
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

# Función de cálculo de BMR según diferentes fórmulas
def calculate_bmr(data: MacroCalculatorInput) -> float:
    # Convertir unidades imperiales a métricas si es necesario
    height_cm = data.height if data.units == Units.METRIC else data.height * 2.54
    weight_kg = data.weight if data.units == Units.METRIC else data.weight * 0.453592
    
    # Calcular BMR según la fórmula seleccionada
    if data.formula == Formula.MIFFLIN_ST_JEOR:
        if data.gender == Gender.MALE:
            return (10 * weight_kg) + (6.25 * height_cm) - (5 * data.age) + 5
        else:
            return (10 * weight_kg) + (6.25 * height_cm) - (5 * data.age) - 161
    
    elif data.formula == Formula.HARRIS_BENEDICT:
        if data.gender == Gender.MALE:
            return 66.5 + (13.75 * weight_kg) + (5.003 * height_cm) - (6.75 * data.age)
        else:
            return 655.1 + (9.563 * weight_kg) + (1.850 * height_cm) - (4.676 * data.age)
    
    elif data.formula == Formula.WHO:
        if data.gender == Gender.MALE:
            if data.age < 18:
                return 15.3 * weight_kg + 679
            elif data.age < 30:
                return 15.3 * weight_kg + 679
            elif data.age < 60:
                return 11.6 * weight_kg + 879
            else:
                return 13.5 * weight_kg + 487
        else:
            if data.age < 18:
                return 13.3 * weight_kg + 496
            elif data.age < 30:
                return 14.7 * weight_kg + 496
            elif data.age < 60:
                return 8.7 * weight_kg + 829
            else:
                return 10.5 * weight_kg + 596
    
    elif data.formula == Formula.KATCH_MCARDLE and data.body_fat_percentage is not None:
        # Calcular masa magra en kg
        lean_mass = weight_kg * (1 - data.body_fat_percentage / 100)
        return 370 + (21.6 * lean_mass)
    
    # Fallback a Mifflin-St Jeor si algo falla
    if data.gender == Gender.MALE:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * data.age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * data.age) - 161

# Endpoint para calcular macros y calorías
@router.post("/calculate-macros", response_model=MacroCalculatorResult)
async def calculate_macros(
    request: Request,
    data: MacroCalculatorInput,
    user = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Calcular BMR según la fórmula seleccionada
        bmr = calculate_bmr(data)
        
        # Calcular TDEE (Total Daily Energy Expenditure)
        activity_multipliers = {
            ActivityLevel.SEDENTARY: 1.2,
            ActivityLevel.LIGHT: 1.375,
            ActivityLevel.MODERATE: 1.55,
            ActivityLevel.ACTIVE: 1.725,
            ActivityLevel.VERY_ACTIVE: 1.9
        }
        tdee = bmr * activity_multipliers[data.activity_level]
        
        # Calcular BMI
        height_m = (data.height / 100) if data.units == Units.METRIC else (data.height * 0.0254)
        weight_kg = data.weight if data.units == Units.METRIC else (data.weight * 0.453592)
        bmi = weight_kg / (height_m * height_m)
        
        # Calcular calorías objetivo según la meta
        goal_calories = tdee  # Por defecto, mantener peso
        if data.goal == Goal.LOSE:
            deficit = 500 if data.goal_intensity == GoalIntensity.NORMAL else 1000
            goal_calories = max(1200, tdee - deficit)  # Mínimo seguro
        elif data.goal == Goal.GAIN:
            surplus = 500 if data.goal_intensity == GoalIntensity.NORMAL else 1000
            goal_calories = tdee + surplus
        
        # Calcular macros en gramos y porcentajes
        # Distribución estándar: 30% proteína, 35% carbohidratos, 35% grasas
        protein_cals = goal_calories * 0.30
        carbs_cals = goal_calories * 0.35
        fat_cals = goal_calories * 0.35
        
        protein_g = protein_cals / 4  # 4 calorías por gramo de proteína
        carbs_g = carbs_cals / 4      # 4 calorías por gramo de carbohidratos
        fat_g = fat_cals / 9          # 9 calorías por gramo de grasa
        
        # Preparar respuesta
        macros = {
            "protein": {
                "grams": round(protein_g),
                "calories": round(protein_cals),
                "percentage": 30
            },
            "carbs": {
                "grams": round(carbs_g),
                "calories": round(carbs_cals),
                "percentage": 35
            },
            "fat": {
                "grams": round(fat_g),
                "calories": round(fat_cals),
                "percentage": 35
            }
        }
        
        result = MacroCalculatorResult(
            bmr=round(bmr),
            tdee=round(tdee),
            bmi=round(bmi, 1),
            goal_calories=round(goal_calories),
            macros=macros
        )
        
        # Guardar resultado en la base de datos
        await save_nutrition_profile(user['id'], data, result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el cálculo de macros: {str(e)}")

# Función para guardar el perfil nutricional
async def save_nutrition_profile(user_id, input_data, result_data):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Asegúrate de que estamos en el esquema correcto
        cur.execute("SET search_path TO nutrition, public")
        
        # Verificar si ya existe un perfil para este usuario
        cur.execute(
            """
            SELECT id FROM user_nutrition_profiles 
            WHERE user_id = %s
            """, 
            (str(user_id),)
        )
        
        existing_profile = cur.fetchone()
        
        # Preparar los datos para guardar
        profile_data = {
            'user_id': str(user_id),
            'formula': input_data.formula.value,
            'gender': input_data.gender.value,
            'age': input_data.age,
            'height': input_data.height,
            'weight': input_data.weight,
            'body_fat_percentage': input_data.body_fat_percentage,
            'activity_level': input_data.activity_level.value,
            'goal': input_data.goal.value,
            'goal_intensity': input_data.goal_intensity.value,
            'units': input_data.units.value,
            'bmr': result_data.bmr,
            'tdee': result_data.tdee,
            'bmi': result_data.bmi,
            'goal_calories': result_data.goal_calories,
            'protein_g': result_data.macros['protein']['grams'],
            'carbs_g': result_data.macros['carbs']['grams'],
            'fat_g': result_data.macros['fat']['grams']
        }
        
        if existing_profile:
            # Actualizar el perfil existente
            update_query = """
            UPDATE user_nutrition_profiles SET
                formula = %(formula)s,
                gender = %(gender)s,
                age = %(age)s,
                height = %(height)s,
                weight = %(weight)s,
                body_fat_percentage = %(body_fat_percentage)s,
                activity_level = %(activity_level)s,
                goal = %(goal)s,
                goal_intensity = %(goal_intensity)s,
                units = %(units)s,
                bmr = %(bmr)s,
                tdee = %(tdee)s,
                bmi = %(bmi)s,
                goal_calories = %(goal_calories)s,
                protein_g = %(protein_g)s,
                carbs_g = %(carbs_g)s,
                fat_g = %(fat_g)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %(user_id)s
            """
            cur.execute(update_query, profile_data)
        else:
            # Crear un nuevo perfil
            insert_query = """
            INSERT INTO user_nutrition_profiles (
                user_id, formula, gender, age, height, weight, body_fat_percentage,
                activity_level, goal, goal_intensity, units, bmr, tdee, bmi,
                goal_calories, protein_g, carbs_g, fat_g
            ) VALUES (
                %(user_id)s, %(formula)s, %(gender)s, %(age)s, %(height)s, %(weight)s, 
                %(body_fat_percentage)s, %(activity_level)s, %(goal)s, %(goal_intensity)s, 
                %(units)s, %(bmr)s, %(tdee)s, %(bmi)s, %(goal_calories)s, 
                %(protein_g)s, %(carbs_g)s, %(fat_g)s
            )
            """
            cur.execute(insert_query, profile_data)
        
        conn.commit()
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Endpoint para obtener el perfil nutricional del usuario
@router.get("/profile", response_class=JSONResponse)
async def get_nutrition_profile(request: Request, user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Asegúrate de que estamos en el esquema correcto
        cur.execute("SET search_path TO nutrition, public")
        
        # Obtener el perfil nutricional del usuario
        cur.execute(
            """
            SELECT * FROM user_nutrition_profiles 
            WHERE user_id = %s
            """, 
            (str(user['id']),)
        )
        
        profile_data = cur.fetchone()
        
        if not profile_data:
            return JSONResponse(content={"success": True, "profile": None})
        
        # Obtener los nombres de las columnas
        column_names = [desc[0] for desc in cur.description]
        
        # Crear un diccionario con los datos
        profile = dict(zip(column_names, profile_data))
        
        # Reconstruir el objeto de macros para mantener consistencia con el endpoint de cálculo
        macros = {
            "protein": {
                "grams": profile['protein_g'],
                "calories": profile['protein_g'] * 4,
                "percentage": round((profile['protein_g'] * 4 / profile['goal_calories']) * 100)
            },
            "carbs": {
                "grams": profile['carbs_g'],
                "calories": profile['carbs_g'] * 4,
                "percentage": round((profile['carbs_g'] * 4 / profile['goal_calories']) * 100)
            },
            "fat": {
                "grams": profile['fat_g'],
                "calories": profile['fat_g'] * 9,
                "percentage": round((profile['fat_g'] * 9 / profile['goal_calories']) * 100)
            }
        }
        
        # Construir respuesta final
        response_data = {
            "id": profile['id'],
            "user_id": profile['user_id'],
            "formula": profile['formula'],
            "gender": profile['gender'],
            "age": profile['age'],
            "height": profile['height'],
            "weight": profile['weight'],
            "body_fat_percentage": profile['body_fat_percentage'],
            "activity_level": profile['activity_level'],
            "goal": profile['goal'],
            "goal_intensity": profile['goal_intensity'],
            "units": profile['units'],
            "bmr": profile['bmr'],
            "tdee": profile['tdee'],
            "bmi": profile['bmi'],
            "goal_calories": profile['goal_calories'],
            "macros": macros,
            "created_at": profile['created_at'],
            "updated_at": profile['updated_at']
        }
        
        return JSONResponse(content={"success": True, "profile": response_data})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el perfil nutricional: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()