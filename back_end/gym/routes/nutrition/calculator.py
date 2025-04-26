# back_end/gym/routes/nutrition/calculator.py
from fastapi import APIRouter, Depends, HTTPException
from enum import Enum
import logging
from typing import Dict, Optional
from datetime import datetime

from ...models.calculator_schemas import MacroCalculatorInput, NutritionProfile
from ...services.auth_service import get_current_user_id
from ...services.db_utils import execute_db_query

router = APIRouter()

# Enumeraciones para los cálculos
class Goal(Enum):
    MAINTAIN = "maintain"
    LOSE = "lose"
    GAIN = "gain"

class GoalIntensity(Enum):
    LIGHT = "light"
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"  # Añadido para soportar "Muy Agresivo"

class ActivityLevel(Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"

class Formula(Enum):
    MIFFLIN_ST_JEOR = "mifflin_st_jeor"
    HARRIS_BENEDICT = "harris_benedict"
    KATCH_MCARDLE = "katch_mcardle"
    WHO = "who"

class Unit(Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

# Función para calcular el BMR según diferentes fórmulas
def calculate_bmr(formula: str, gender: str, age: int, weight: float, height: float, body_fat_percentage: Optional[float] = None, units: str = "metric") -> float:
    # Convertir unidades imperiales a métricas si es necesario
    if units == "imperial":
        weight = weight * 0.453592  # libras a kg
        height = height * 2.54  # pulgadas a cm

    # Fórmula Mifflin-St Jeor (la más precisa para la mayoría de personas)
    if formula == Formula.MIFFLIN_ST_JEOR.value:
        if gender == "male":
            return (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:  # female
            return (10 * weight) + (6.25 * height) - (5 * age) - 161

    # Fórmula Harris-Benedict (versión revisada)
    elif formula == Formula.HARRIS_BENEDICT.value:
        if gender == "male":
            return 13.397 * weight + 4.799 * height - 5.677 * age + 88.362
        else:  # female
            return 9.247 * weight + 3.098 * height - 4.330 * age + 447.593

    # Fórmula Katch-McArdle (usa % de grasa corporal, mejor para atletas)
    elif formula == Formula.KATCH_MCARDLE.value and body_fat_percentage is not None:
        lean_mass = weight * (1 - (body_fat_percentage / 100))
        return 370 + (21.6 * lean_mass)

    # Fórmula OMS/WHO (basada en el peso)
    elif formula == Formula.WHO.value:
        if gender == "male":
            if age < 30:
                return 15.3 * weight + 679
            elif age < 60:
                return 11.6 * weight + 879
            else:
                return 13.5 * weight + 487
        else:  # female
            if age < 30:
                return 14.7 * weight + 496
            elif age < 60:
                return 8.7 * weight + 829
            else:
                return 10.5 * weight + 596

    # Si no coincide ninguna fórmula, usa Mifflin-St Jeor como fallback
    if gender == "male":
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:  # female
        return (10 * weight) + (6.25 * height) - (5 * age) - 161

# Función para calcular el BMI (Índice de Masa Corporal)
def calculate_bmi(weight: float, height: float, units: str = "metric") -> float:
    # Convertir unidades imperiales a métricas si es necesario
    if units == "imperial":
        weight = weight * 0.453592  # libras a kg
        height = height * 2.54  # pulgadas a cm

    # BMI = peso(kg) / altura(m)²
    height_m = height / 100  # convertir cm a m
    return round(weight / (height_m * height_m), 1)

# Función para calcular el TDEE (Gasto Energético Total Diario)
def calculate_tdee(bmr: float, activity_level: str) -> float:
    activity_multipliers = {
        ActivityLevel.SEDENTARY.value: 1.2,      # Poco o nada de ejercicio, trabajo de escritorio
        ActivityLevel.LIGHT.value: 1.375,        # Ejercicio ligero/deportes 1-3 días/semana
        ActivityLevel.MODERATE.value: 1.55,      # Ejercicio moderado 3-5 días/semana
        ActivityLevel.ACTIVE.value: 1.725,       # Ejercicio intenso 6-7 días/semana
        ActivityLevel.VERY_ACTIVE.value: 1.9     # Ejercicio muy intenso, trabajo físico, entrenamiento 2 veces/día
    }
    multiplier = activity_multipliers.get(activity_level, 1.2)  # Usa 1.2 como valor por defecto
    return bmr * multiplier

# Función para calcular las calorías objetivo según el objetivo y su intensidad
def calculate_goal_calories(tdee: float, goal: str, goal_intensity: str) -> int:
    if goal == Goal.MAINTAIN.value:
        return round(tdee)
    
    calorie_adjustments = {
        GoalIntensity.LIGHT.value: 250,
        GoalIntensity.NORMAL.value: 500,
        GoalIntensity.AGGRESSIVE.value: 750,
        GoalIntensity.VERY_AGGRESSIVE.value: 1000,
    }
    
    adjustment = calorie_adjustments.get(goal_intensity, 500)  # Valor por defecto: 500
    
    if goal == Goal.LOSE.value:
        return round(tdee - adjustment)
    else:  # GAIN
        return round(tdee + adjustment)

# Endpoint principal para calcular macros
@router.post("/calculate-macros", response_model=NutritionProfile)
async def calculate_macros(data: MacroCalculatorInput, user_id: int = Depends(get_current_user_id)):
    try:
        # Calcular BMR (Tasa Metabólica Basal)
        bmr = calculate_bmr(
            formula=data.formula,
            gender=data.gender,
            age=data.age,
            weight=data.weight,
            height=data.height,
            body_fat_percentage=data.body_fat_percentage,
            units=data.units
        )
        
        # Calcular TDEE (Gasto Energético Total Diario)
        tdee = calculate_tdee(bmr, data.activity_level)
        
        # Calcular BMI (Índice de Masa Corporal)
        bmi = calculate_bmi(data.weight, data.height, data.units)
        
        # Calcular calorías objetivo según el objetivo e intensidad
        goal_calories = calculate_goal_calories(tdee, data.goal, data.goal_intensity)
        
        # Obtener porcentajes de macros de la distribución enviada por el frontend
        protein_percentage = data.macro_distribution.protein
        carbs_percentage = data.macro_distribution.carbs
        fat_percentage = data.macro_distribution.fat
        
        # Validar que los porcentajes sumen 100%
        total_percentage = protein_percentage + carbs_percentage + fat_percentage
        if abs(total_percentage - 100) > 0.1:
            logging.warning(f"Los porcentajes de macros no suman 100%: P={protein_percentage}, C={carbs_percentage}, F={fat_percentage}, Total={total_percentage}")
        
        # Calcular gramos de cada macronutriente
        # 1g de proteína = 4 calorías
        # 1g de carbohidratos = 4 calorías
        # 1g de grasa = 9 calorías
        protein_grams = round((goal_calories * (protein_percentage / 100)) / 4)
        carbs_grams = round((goal_calories * (carbs_percentage / 100)) / 4)
        fat_grams = round((goal_calories * (fat_percentage / 100)) / 9)
        
        # Crear objeto de respuesta
        profile = {
            "user_id": str(user_id),
            "formula": data.formula,
            "sex": data.gender,
            "age": data.age,
            "height": data.height,
            "weight": data.weight,
            "body_fat_percentage": data.body_fat_percentage,
            "activity_level": data.activity_level,
            "goal": data.goal,
            "goal_intensity": data.goal_intensity,
            "units": data.units,
            "bmr": round(bmr),
            "tdee": round(tdee),
            "bmi": bmi,
            "daily_calories": goal_calories,
            "proteins_grams": protein_grams,
            "carbs_grams": carbs_grams,
            "fats_grams": fat_grams
        }
        
        # Si el usuario está autenticado, guardar o actualizar su perfil
        if user_id:
            try:
                logging.getLogger(__name__).debug(f"Intentando guardar perfil nutricional para user_id: {user_id}")
                
                # Verificar si ya existe un perfil para este usuario
                check_query = "SELECT id FROM nutrition.user_nutrition_profiles WHERE user_id = %s"
                profile_exists = execute_db_query(check_query, (str(user_id),), fetch_one=True)
                
                logging.getLogger(__name__).debug(f"Perfil existente: {profile_exists}")
                
                # Datos a guardar en la base de datos
                profile_data = {
                    "user_id": str(user_id),
                    "formula": data.formula,
                    "sex": data.gender,
                    "age": data.age, 
                    "height": data.height,
                    "weight": data.weight,
                    "body_fat_percentage": data.body_fat_percentage,
                    "activity_level": data.activity_level,
                    "goal": data.goal,
                    "goal_intensity": data.goal_intensity,
                    "units": data.units,
                    "bmr": round(bmr),
                    "tdee": round(tdee),
                    "bmi": bmi,
                    "daily_calories": goal_calories,
                    "proteins_grams": protein_grams,
                    "carbs_grams": carbs_grams,
                    "fats_grams": fat_grams
                }
                
                logging.getLogger(__name__).debug(f"Datos a guardar: {profile_data}")
                
                if profile_exists:
                    # Actualizar perfil existente
                    update_query = """
                    UPDATE nutrition.user_nutrition_profiles SET
                        formula = %(formula)s,
                        sex = %(sex)s,
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
                        daily_calories = %(daily_calories)s,
                        proteins_grams = %(proteins_grams)s,
                        carbs_grams = %(carbs_grams)s,
                        fats_grams = %(fats_grams)s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %(user_id)s
                    """
                    logging.getLogger(__name__).debug(f"Query de actualización: {update_query}")
                    execute_db_query(update_query, profile_data)
                    logging.getLogger(__name__).info(f"Perfil actualizado para usuario {user_id}")
                else:
                    # Crear nuevo perfil
                    insert_query = """
                    INSERT INTO nutrition.user_nutrition_profiles (
                        user_id, formula, sex, age, height, weight, body_fat_percentage, 
                        activity_level, goal, goal_intensity, units, bmr, tdee, bmi, 
                        daily_calories, proteins_grams, carbs_grams, fats_grams
                    ) VALUES (
                        %(user_id)s, %(formula)s, %(sex)s, %(age)s, %(height)s, %(weight)s, 
                        %(body_fat_percentage)s, %(activity_level)s, %(goal)s, %(goal_intensity)s, 
                        %(units)s, %(bmr)s, %(tdee)s, %(bmi)s, %(daily_calories)s, 
                        %(proteins_grams)s, %(carbs_grams)s, %(fats_grams)s
                    )
                    """
                    execute_db_query(insert_query, profile_data)
                    logging.getLogger(__name__).info(f"Nuevo perfil creado para usuario {user_id}")
                
                logging.getLogger(__name__).info(f"Perfil nutricional guardado para usuario {user_id}")
            except Exception as e:
                logging.getLogger(__name__).error(f"Error al guardar perfil nutricional: {e}")
                # No interrumpimos el flujo si falla el guardado, solo logueamos el error
        
        return NutritionProfile(**profile)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error en el cálculo de macros: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para obtener el perfil nutricional de un usuario
@router.get("/profile", response_model=Optional[NutritionProfile])
async def get_nutrition_profile(user_id: int = Depends(get_current_user_id)):
    try:
        query = """
        SELECT 
            user_id, formula, sex, age, height, weight, body_fat_percentage, 
            activity_level, goal, goal_intensity, units, bmr, tdee, bmi, 
            daily_calories, proteins_grams, carbs_grams, fats_grams,
            created_at, updated_at
        FROM nutrition.user_nutrition_profiles
        WHERE user_id = %s
        """
        result = execute_db_query(query, (str(user_id),), fetch_one=True)
        
        if not result:
            return None
        
        return NutritionProfile(**result)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error al obtener perfil nutricional: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para guardar el perfil nutricional de un usuario
@router.post("/profile", response_model=NutritionProfile)
async def save_nutrition_profile(data: NutritionProfile, user_id: int = Depends(get_current_user_id)):
    try:
        # Asignar el ID de usuario
        data.user_id = str(user_id)
        
        # Verificar si ya existe un perfil para este usuario
        check_query = "SELECT id FROM nutrition.user_nutrition_profiles WHERE user_id = %s"
        profile_exists = execute_db_query(check_query, (str(user_id),), fetch_one=True)
        
        # Preparar los datos para guardar
        profile_data = data.dict()
        profile_data["updated_at"] = datetime.now()
        
        if profile_exists:
            # Actualizar perfil existente
            update_query = """
            UPDATE nutrition.user_nutrition_profiles SET
                formula = %(formula)s,
                sex = %(sex)s,
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
                daily_calories = %(daily_calories)s,
                proteins_grams = %(proteins_grams)s,
                carbs_grams = %(carbs_grams)s,
                fats_grams = %(fats_grams)s,
                updated_at = %(updated_at)s
            WHERE user_id = %(user_id)s
            """
            execute_db_query(update_query, profile_data)
        else:
            # Crear nuevo perfil
            profile_data["created_at"] = datetime.now()
            insert_query = """
            INSERT INTO nutrition.user_nutrition_profiles (
                user_id, formula, sex, age, height, weight, body_fat_percentage, 
                activity_level, goal, goal_intensity, units, bmr, tdee, bmi, 
                daily_calories, proteins_grams, carbs_grams, fats_grams,
                created_at, updated_at
            ) VALUES (
                %(user_id)s, %(formula)s, %(sex)s, %(age)s, %(height)s, %(weight)s, 
                %(body_fat_percentage)s, %(activity_level)s, %(goal)s, %(goal_intensity)s, 
                %(units)s, %(bmr)s, %(tdee)s, %(bmi)s, %(daily_calories)s, 
                %(proteins_grams)s, %(carbs_grams)s, %(fats_grams)s,
                %(created_at)s, %(updated_at)s
            )
            """
            execute_db_query(insert_query, profile_data)
        
        return data
    except Exception as e:
        logging.getLogger(__name__).error(f"Error al guardar perfil nutricional: {e}")
        raise HTTPException(status_code=500, detail=str(e))