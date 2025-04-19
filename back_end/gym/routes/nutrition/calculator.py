# back_end/gym/routes/nutrition/calculator.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
import math
import logging

# Importaciones
from back_end.gym.middlewares import get_current_user
from back_end.gym.config import DB_CONFIG
from back_end.gym.utils.json_utils import CustomJSONResponse
import psycopg2

# Importar esquemas desde el nuevo archivo de modelos
from back_end.gym.models.calculator_schemas import (
    MacroCalculatorInput,
    MacroCalculatorResult,
    Units,
    Formula,
    ActivityLevel,
    Gender,
    Goal,
    GoalIntensity
)

# Configurar logger específico para este módulo
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])

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
        success = await save_nutrition_profile(user['id'], data, result)
        if not success:
            logger.warning(f"No se pudo guardar el perfil nutricional para usuario {user['id']}")
        else:
            logger.info(f"Perfil nutricional guardado para usuario {user['id']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en el cálculo de macros: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en el cálculo de macros: {str(e)}")

# Función para guardar el perfil nutricional
async def save_nutrition_profile(user_id, input_data, result_data):
    conn = None
    cur = None
    try:
        logger.debug(f"Intentando guardar perfil nutricional para user_id: {user_id}")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Verificar si ya existe un perfil para este usuario
        cur.execute(
            """
            SELECT id FROM nutrition.user_nutrition_profiles 
            WHERE user_id = %s
            """, 
            (str(user_id),)
        )
        
        existing_profile = cur.fetchone()
        logger.debug(f"Perfil existente: {existing_profile}")
        
        # Preparar los datos con mapeo correcto a los nombres de columnas de la BD
        # IMPORTANTE: Aquí está la corrección de los nombres de columnas
        profile_data = {
            'user_id': str(user_id),
            'formula': input_data.formula.value,
            'sex': input_data.gender.value,                # gender -> sex
            'age': input_data.age,
            'height': int(input_data.height),              # Convertir a entero
            'weight': input_data.weight,
            'body_fat_percentage': input_data.body_fat_percentage,
            'activity_level': input_data.activity_level.value,
            'goal': input_data.goal.value,
            'goal_intensity': input_data.goal_intensity.value,
            'units': input_data.units.value,
            'bmr': result_data.bmr,
            'tdee': result_data.tdee,
            'bmi': result_data.bmi,
            'daily_calories': result_data.goal_calories,   # goal_calories -> daily_calories
            'proteins_grams': result_data.macros['protein']['grams'],  # protein_g -> proteins_grams
            'carbs_grams': result_data.macros['carbs']['grams'],       # carbs_g -> carbs_grams
            'fats_grams': result_data.macros['fat']['grams']           # fat_g -> fats_grams
        }
        
        logger.debug(f"Datos a guardar: {profile_data}")
        
        if existing_profile:
            # Actualizar el perfil existente
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
            
            logger.debug(f"Query de actualización: {update_query}")
            cur.execute(update_query, profile_data)
            logger.info(f"Perfil actualizado para usuario {user_id}")
        else:
            # Crear un nuevo perfil
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
            
            logger.debug(f"Query de inserción: {insert_query}")
            cur.execute(insert_query, profile_data)
            logger.info(f"Nuevo perfil creado para usuario {user_id}")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error al guardar perfil nutricional: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Endpoint para obtener el perfil nutricional del usuario
@router.get("/profile", response_class=CustomJSONResponse)
async def get_nutrition_profile(request: Request, user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Obtener el perfil nutricional del usuario
        cur.execute(
            """
            SELECT * FROM nutrition.user_nutrition_profiles 
            WHERE user_id = %s
            """, 
            (str(user['id']),)
        )
        
        profile_data = cur.fetchone()
        
        if not profile_data:
            return CustomJSONResponse(content={"success": True, "profile": None})
        
        # Obtener los nombres de las columnas
        column_names = [desc[0] for desc in cur.description]
        
        # Crear un diccionario con los datos
        profile = dict(zip(column_names, profile_data))
        
        # Reconstruir el objeto de macros para mantener consistencia con el endpoint de cálculo
        # CustomJSONResponse se encargará de convertir los decimales a flotantes
        macros = {
            "protein": {
                "grams": profile['proteins_grams'],  # Ajustado a los nombres reales de columnas
                "calories": profile['proteins_grams'] * 4,
                "percentage": round((profile['proteins_grams'] * 4 / profile['daily_calories']) * 100)  # Ajustado a nombres reales
            },
            "carbs": {
                "grams": profile['carbs_grams'],  # Ajustado a los nombres reales de columnas
                "calories": profile['carbs_grams'] * 4,
                "percentage": round((profile['carbs_grams'] * 4 / profile['daily_calories']) * 100)  # Ajustado a nombres reales
            },
            "fat": {
                "grams": profile['fats_grams'],  # Ajustado a los nombres reales de columnas
                "calories": profile['fats_grams'] * 9,
                "percentage": round((profile['fats_grams'] * 9 / profile['daily_calories']) * 100)  # Ajustado a nombres reales
            }
        }
        
        # Construir respuesta final con mapeo de nombres
        response_data = {
            "id": profile['id'],
            "user_id": profile['user_id'],
            "formula": profile['formula'],
            "gender": profile['sex'],  # Mapeo sex -> gender para la respuesta
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
            "goal_calories": profile['daily_calories'],  # Mapeo daily_calories -> goal_calories para la respuesta
            "macros": macros,
            "created_at": profile['created_at'],
            "updated_at": profile['updated_at']
        }
        
        # CustomJSONResponse se encargará de transformar los tipos problemáticos automáticamente
        return CustomJSONResponse(content={"success": True, "profile": response_data})
        
    except Exception as e:
        logger.error(f"Error al obtener el perfil nutricional: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener el perfil nutricional: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()