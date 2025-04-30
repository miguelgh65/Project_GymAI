# back_end/gym/services/nutrition/tracking_service.py
import logging
from typing import Optional, List, Dict, Any
import datetime
import decimal
from json import dumps

# Use absolute import path
from back_end.gym.services.db_utils import execute_db_query

# Configure logger
logger = logging.getLogger(__name__)

def save_daily_tracking(user_id: str, tracking_date: str, completed_meals: Dict, calorie_note: Optional[str] = None, 
                        actual_calories: Optional[int] = None, excess_deficit: Optional[int] = None, 
                        actual_protein: Optional[int] = None) -> Optional[Dict]:
    """
    Save or update daily tracking information.
    
    Args:
        user_id: The user ID
        tracking_date: Date in YYYY-MM-DD format
        completed_meals: Dictionary mapping meal names to boolean completion status
        calorie_note: Optional note about calories
        actual_calories: Optional actual calories consumed
        excess_deficit: Optional calculated excess/deficit
        actual_protein: Optional actual protein consumed
        
    Returns:
        Dict with the saved tracking info or None if error
    """
    try:
        # Check if entry already exists for this user and date
        check_query = """
        SELECT id FROM nutrition.daily_tracking 
        WHERE user_id = %s AND tracking_date = %s
        """
        
        existing = execute_db_query(check_query, (str(user_id), tracking_date), fetch_one=True)
        
        # Convert completed_meals dict to JSON string
        completed_meals_json = dumps(completed_meals)
        
        if existing:
            # Update existing record
            query = """
            UPDATE nutrition.daily_tracking
            SET 
                completed_meals = %s,
                calorie_note = %s,
                actual_calories = %s,
                excess_deficit = %s,
                actual_protein = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND tracking_date = %s
            RETURNING id, user_id, tracking_date, completed_meals, calorie_note, 
                      actual_calories, excess_deficit, actual_protein, created_at, updated_at
            """
            
            params = (
                completed_meals_json,
                calorie_note,
                actual_calories,
                excess_deficit,
                actual_protein,
                str(user_id),
                tracking_date
            )
            
            logger.info(f"Updating tracking for user {user_id} on {tracking_date}")
            
        else:
            # Insert new record
            query = """
            INSERT INTO nutrition.daily_tracking
                (user_id, tracking_date, completed_meals, calorie_note, actual_calories, excess_deficit, actual_protein)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, tracking_date, completed_meals, calorie_note, 
                      actual_calories, excess_deficit, actual_protein, created_at, updated_at
            """
            
            params = (
                str(user_id),
                tracking_date,
                completed_meals_json,
                calorie_note,
                actual_calories,
                excess_deficit,
                actual_protein
            )
            
            logger.info(f"Creating new tracking for user {user_id} on {tracking_date}")
        
        result = execute_db_query(query, params, fetch_one=True, commit=True)
        
        if not result:
            logger.error(f"Failed to save tracking for user {user_id} on {tracking_date}")
            return None
        
        # Format the result
        tracking = {
            "id": result[0],
            "user_id": result[1],
            "tracking_date": result[2].isoformat() if isinstance(result[2], datetime.date) else result[2],
            "completed_meals": result[3],
            "calorie_note": result[4],
            "actual_calories": result[5],
            "excess_deficit": result[6],
            "actual_protein": result[7],
            "created_at": result[8].isoformat() if isinstance(result[8], datetime.datetime) else result[8],
            "updated_at": result[9].isoformat() if isinstance(result[9], datetime.datetime) else result[9]
        }
        
        return tracking
    
    except Exception as e:
        logger.exception(f"Error saving daily tracking: {str(e)}")
        return None

def get_daily_tracking(user_id: str, tracking_date: str) -> Optional[Dict]:
    """
    Get daily tracking information for a specific date.
    
    Args:
        user_id: The user ID
        tracking_date: Date in YYYY-MM-DD format
        
    Returns:
        Dict with tracking info or None if not found or error
    """
    try:
        query = """
        SELECT id, user_id, tracking_date, completed_meals, calorie_note, 
               actual_calories, excess_deficit, actual_protein, created_at, updated_at
        FROM nutrition.daily_tracking
        WHERE user_id = %s AND tracking_date = %s
        """
        
        result = execute_db_query(query, (str(user_id), tracking_date), fetch_one=True)
        
        if not result:
            logger.info(f"No tracking found for user {user_id} on {tracking_date}")
            return None
        
        # Format the result
        tracking = {
            "id": result[0],
            "user_id": result[1],
            "tracking_date": result[2].isoformat() if isinstance(result[2], datetime.date) else result[2],
            "completed_meals": result[3],
            "calorie_note": result[4],
            "actual_calories": result[5],
            "excess_deficit": result[6],
            "actual_protein": result[7],
            "created_at": result[8].isoformat() if isinstance(result[8], datetime.datetime) else result[8],
            "updated_at": result[9].isoformat() if isinstance(result[9], datetime.datetime) else result[9]
        }
        
        return tracking
    
    except Exception as e:
        logger.exception(f"Error getting daily tracking: {str(e)}")
        return None

def get_weekly_tracking(user_id: str, start_date: str) -> List[Dict]:
    """
    Get daily tracking information for a week starting from start_date.
    
    Args:
        user_id: The user ID
        start_date: Start date in YYYY-MM-DD format
        
    Returns:
        List of dicts with tracking info for the week
    """
    try:
        query = """
        SELECT id, user_id, tracking_date, completed_meals, calorie_note, 
               actual_calories, excess_deficit, actual_protein, created_at, updated_at
        FROM nutrition.daily_tracking
        WHERE user_id = %s AND tracking_date >= %s AND tracking_date < (%s::date + interval '7 days')
        ORDER BY tracking_date
        """
        
        results = execute_db_query(query, (str(user_id), start_date, start_date), fetch_all=True)
        
        if not results:
            logger.info(f"No weekly tracking found for user {user_id} starting {start_date}")
            return []
        
        # Format the results
        trackings = []
        for result in results:
            tracking = {
                "id": result[0],
                "user_id": result[1],
                "tracking_date": result[2].isoformat() if isinstance(result[2], datetime.date) else result[2],
                "completed_meals": result[3],
                "calorie_note": result[4],
                "actual_calories": result[5],
                "excess_deficit": result[6],
                "actual_protein": result[7],
                "created_at": result[8].isoformat() if isinstance(result[8], datetime.datetime) else result[8],
                "updated_at": result[9].isoformat() if isinstance(result[9], datetime.datetime) else result[9]
            }
            trackings.append(tracking)
        
        return trackings
    
    except Exception as e:
        logger.exception(f"Error getting weekly tracking: {str(e)}")
        return []

def delete_daily_tracking(user_id: str, tracking_date: str) -> bool:
    """
    Delete daily tracking information for a specific date.
    
    Args:
        user_id: The user ID
        tracking_date: Date in YYYY-MM-DD format
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        query = """
        DELETE FROM nutrition.daily_tracking
        WHERE user_id = %s AND tracking_date = %s
        RETURNING id
        """
        
        result = execute_db_query(query, (str(user_id), tracking_date), fetch_one=True, commit=True)
        
        if result:
            logger.info(f"Deleted tracking for user {user_id} on {tracking_date}")
            return True
        else:
            logger.warning(f"No tracking found to delete for user {user_id} on {tracking_date}")
            return False
    
    except Exception as e:
        logger.exception(f"Error deleting daily tracking: {str(e)}")
        return False

def calculate_weekly_summary(user_id: str, start_date: str) -> Dict:
    """
    Calculate summary statistics for a week's worth of tracking data.
    
    Args:
        user_id: The user ID
        start_date: Start date in YYYY-MM-DD format
        
    Returns:
        Dict with summary statistics
    """
    weekly_tracking = get_weekly_tracking(user_id, start_date)
    
    # Inicializar summary
    summary = {
        "total_days_tracked": len(weekly_tracking),
        "average_calories": 0,
        "total_excess_deficit": 0,
        "meals_completion": {
            "Desayuno": 0,
            "Almuerzo": 0,
            "Comida": 0,
            "Merienda": 0,
            "Cena": 0
        },
        # Nuevos campos para mejorar el seguimiento
        "planned_calories": 0,      # Calorías objetivo para toda la semana
        "consumed_calories": 0,     # Calorías consumidas en la semana
        "completion_percentage": 0,  # Porcentaje de cumplimiento calórico
        "planned_protein": 0,       # Proteínas objetivo para la semana
        "consumed_protein": 0,      # Proteínas consumidas en la semana
        "protein_completion_percentage": 0 # Porcentaje de cumplimiento de proteínas
    }
    
    if not weekly_tracking:
        return summary
    
    # Obtener perfil nutricional para objetivos diarios
    try:
        profile_query = """
        SELECT daily_calories, proteins_grams 
        FROM nutrition.user_nutrition_profiles 
        WHERE user_id = %s
        ORDER BY updated_at DESC
        LIMIT 1
        """
        
        profile_result = execute_db_query(profile_query, (str(user_id),), fetch_one=True)
        
        if profile_result:
            daily_calories = profile_result[0] or 0
            daily_protein = profile_result[1] or 0
            
            # Calcular objetivos semanales (7 días)
            summary["planned_calories"] = daily_calories * 7
            summary["planned_protein"] = daily_protein * 7
    except Exception as e:
        logger.exception(f"Error getting nutrition profile for user {user_id}: {str(e)}")
    
    # Calculate totals from tracking data
    total_calories = 0
    total_excess_deficit = 0
    total_protein = 0  # Nuevo: para seguimiento de proteínas
    days_with_calories = 0
    
    for day in weekly_tracking:
        # Add to calorie total if available
        if day.get("actual_calories") is not None:
            total_calories += day["actual_calories"]
            summary["consumed_calories"] += day["actual_calories"]
            days_with_calories += 1
        
        # Add to protein total if available
        if day.get("actual_protein") is not None:
            total_protein += day["actual_protein"]
            summary["consumed_protein"] += day["actual_protein"]
        
        # Add to excess/deficit total if available
        if day.get("excess_deficit") is not None:
            total_excess_deficit += day["excess_deficit"]
        
        # Count completed meals
        completed_meals = day.get("completed_meals") or {}
        for meal_type, completed in completed_meals.items():
            if completed and meal_type in summary["meals_completion"]:
                summary["meals_completion"][meal_type] += 1
    
    # Calculate averages
    if days_with_calories > 0:
        summary["average_calories"] = total_calories / days_with_calories
    
    summary["total_excess_deficit"] = total_excess_deficit
    
    # Calcular porcentajes de cumplimiento
    if summary["planned_calories"] > 0:
        summary["completion_percentage"] = round((summary["consumed_calories"] / summary["planned_calories"]) * 100)
    
    if summary["planned_protein"] > 0:
        summary["protein_completion_percentage"] = round((summary["consumed_protein"] / summary["planned_protein"]) * 100)
    
    return summary