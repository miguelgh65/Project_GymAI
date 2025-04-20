# back_end/gym/routes/nutrition/tracking.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import date, datetime, timedelta
from pydantic import BaseModel

# Import dependencies
from back_end.gym.middlewares import get_current_user
from back_end.gym.utils.json_utils import CustomJSONResponse
from back_end.gym.config import DB_CONFIG  # Import to use directly with psycopg2
import psycopg2
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["tracking"])

# Schema models
class CompletedMeals(BaseModel):
    Desayuno: Optional[bool] = False
    Almuerzo: Optional[bool] = False
    Comida: Optional[bool] = False
    Merienda: Optional[bool] = False
    Cena: Optional[bool] = False
    Otro: Optional[bool] = False

class DailyTrackingCreate(BaseModel):
    tracking_date: date
    completed_meals: CompletedMeals
    calorie_note: Optional[str] = None
    actual_calories: Optional[int] = None
    excess_deficit: Optional[int] = None

class DailyTrackingResponse(BaseModel):
    id: int
    user_id: str
    tracking_date: date
    completed_meals: Dict[str, bool]
    calorie_note: Optional[str] = None
    actual_calories: Optional[int] = None
    excess_deficit: Optional[int] = None
    created_at: datetime
    updated_at: datetime

# Direct database functions for simplicity
def save_tracking(user_id, tracking_date, completed_meals, calorie_note=None, 
                 actual_calories=None, excess_deficit=None):
    """Save tracking data directly with psycopg2"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check if record exists
        cur.execute(
            "SELECT id FROM nutrition.daily_tracking WHERE user_id = %s AND tracking_date = %s",
            (str(user_id), tracking_date)
        )
        existing = cur.fetchone()
        
        if existing:
            # Update existing record
            query = """
            UPDATE nutrition.daily_tracking
            SET 
                completed_meals = %s,
                calorie_note = %s,
                actual_calories = %s,
                excess_deficit = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND tracking_date = %s
            RETURNING id, user_id, tracking_date, completed_meals, calorie_note, 
                     actual_calories, excess_deficit, created_at, updated_at
            """
            
            params = (
                json.dumps(completed_meals),
                calorie_note,
                actual_calories,
                excess_deficit,
                str(user_id),
                tracking_date
            )
        else:
            # Insert new record
            query = """
            INSERT INTO nutrition.daily_tracking
                (user_id, tracking_date, completed_meals, calorie_note, actual_calories, excess_deficit)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, tracking_date, completed_meals, calorie_note, 
                     actual_calories, excess_deficit, created_at, updated_at
            """
            
            params = (
                str(user_id),
                tracking_date,
                json.dumps(completed_meals),
                calorie_note,
                actual_calories,
                excess_deficit
            )
        
        cur.execute(query, params)
        result = cur.fetchone()
        conn.commit()
        
        if not result:
            return None
            
        # Format result
        return {
            "id": result[0],
            "user_id": result[1],
            "tracking_date": result[2],
            "completed_meals": result[3],
            "calorie_note": result[4],
            "actual_calories": result[5],
            "excess_deficit": result[6],
            "created_at": result[7],
            "updated_at": result[8]
        }
        
    except Exception as e:
        logger.exception(f"Error saving tracking data: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_tracking(user_id, tracking_date):
    """Get tracking data directly with psycopg2"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT id, user_id, tracking_date, completed_meals, calorie_note, 
                  actual_calories, excess_deficit, created_at, updated_at
            FROM nutrition.daily_tracking
            WHERE user_id = %s AND tracking_date = %s
            """,
            (str(user_id), tracking_date)
        )
        
        result = cur.fetchone()
        
        if not result:
            return None
            
        # Format result
        return {
            "id": result[0],
            "user_id": result[1],
            "tracking_date": result[2],
            "completed_meals": result[3],
            "calorie_note": result[4],
            "actual_calories": result[5],
            "excess_deficit": result[6],
            "created_at": result[7],
            "updated_at": result[8]
        }
        
    except Exception as e:
        logger.exception(f"Error getting tracking data: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Routes
@router.post("/tracking", response_model=DailyTrackingResponse)
async def create_or_update_tracking(
    request: Request,
    tracking_data: DailyTrackingCreate,
    user = Depends(get_current_user)
):
    """Create or update daily nutrition tracking"""
    logger.debug(f"POST /tracking received: {tracking_data}")
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Extract and prepare data
        user_id = user['id']
        tracking_date = tracking_data.tracking_date.isoformat()
        completed_meals = tracking_data.completed_meals.dict()
        
        # Save to database
        result = save_tracking(
            user_id=user_id,
            tracking_date=tracking_date,
            completed_meals=completed_meals,
            calorie_note=tracking_data.calorie_note,
            actual_calories=tracking_data.actual_calories,
            excess_deficit=tracking_data.excess_deficit
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al guardar el seguimiento")
        
        return result
    
    except Exception as e:
        logger.error(f"Error creating/updating tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear/actualizar seguimiento: {str(e)}")

@router.get("/tracking/day/{date_str}", response_class=CustomJSONResponse)
async def get_tracking_for_day(
    request: Request,
    date_str: str,
    user = Depends(get_current_user)
):
    """Get daily nutrition tracking for a specific date"""
    logger.debug(f"GET /tracking/day/{date_str} received")
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Validate date format (YYYY-MM-DD)
        try:
            tracking_date = datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
        
        # Get tracking data
        result = get_tracking(
            user_id=user['id'],
            tracking_date=tracking_date
        )
        
        return CustomJSONResponse(content={"success": True, "tracking": result})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching daily tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener seguimiento diario: {str(e)}")

@router.get("/tracking/week", response_class=CustomJSONResponse)
async def get_tracking_for_week(
    request: Request,
    start_date: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get nutrition tracking for a week"""
    logger.debug(f"GET /tracking/week received with start_date={start_date}")
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Simple implementation for testing
        # Returns empty array for now - you can implement the full version later
        return CustomJSONResponse(content={"success": True, "tracking": []})
    
    except Exception as e:
        logger.error(f"Error fetching weekly tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener seguimiento semanal: {str(e)}")

@router.get("/tracking/summary")
async def get_weekly_summary(
    request: Request,
    start_date: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get summary statistics for a week of tracking data"""
    logger.debug(f"GET /tracking/summary received with start_date={start_date}")
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Simple implementation for testing
        return {
            "total_days_tracked": 0,
            "average_calories": 0,
            "total_excess_deficit": 0,
            "meals_completion": {
                "Desayuno": 0,
                "Almuerzo": 0,
                "Comida": 0,
                "Merienda": 0,
                "Cena": 0
            }
        }
    
    except Exception as e:
        logger.error(f"Error calculating weekly summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error al calcular resumen semanal: {str(e)}")

@router.delete("/tracking/{date_str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracking(
    request: Request,
    date_str: str,
    user = Depends(get_current_user)
):
    """Delete nutrition tracking for a specific date"""
    logger.debug(f"DELETE /tracking/{date_str} received")
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    # Simple implementation - you can add the full functionality later
    return None