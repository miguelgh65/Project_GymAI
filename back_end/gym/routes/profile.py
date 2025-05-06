# back_end/gym/routes/profile.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import logging
from datetime import datetime

# Use absolute import instead of relative import
from back_end.gym.models.calculator_schemas import NutritionProfile
from back_end.gym.middlewares import get_current_user
from back_end.gym.services.db_utils import execute_db_query

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Helper function to extract user_id from user object
def get_user_id_from_current_user(user = Depends(get_current_user)):
    """Extrae el ID del usuario actual."""
    if not user:
        return None
    return user.get('id')

@router.get("/profile", response_model=Optional[NutritionProfile])
async def get_nutrition_profile(user_id = Depends(get_user_id_from_current_user)):
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
        logger.error(f"❌ Error al obtener perfil nutricional: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile", response_model=NutritionProfile)
async def save_nutrition_profile(data: NutritionProfile, user_id = Depends(get_user_id_from_current_user)):
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
        logger.error(f"❌ Error al guardar perfil nutricional: {e}")
        raise HTTPException(status_code=500, detail=str(e))