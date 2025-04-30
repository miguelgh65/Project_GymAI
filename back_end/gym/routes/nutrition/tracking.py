# back_end/gym/routes/nutrition/tracking.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import date, datetime, timedelta
import logging
import json

# Importaciones corregidas
from back_end.gym.middlewares import get_current_user
from back_end.gym.utils.json_utils import CustomJSONResponse
from back_end.gym.models.tracking_schemas import (
    CompletedMeals,
    DailyTrackingCreate,
    DailyTrackingResponse,
    WeeklyTrackingSummary
)

# Importar servicios correctamente
from back_end.gym.services.nutrition.tracking_service import (
    save_daily_tracking,
    get_daily_tracking,
    get_weekly_tracking,
    delete_daily_tracking,
    calculate_weekly_summary
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["tracking"])

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
        
        # Convert Pydantic model to dict for completion status
        completed_meals_dict = {}
        for meal, status in tracking_data.completed_meals.dict().items():
            completed_meals_dict[meal] = bool(status)
        
        # USAR EL SERVICIO EN LUGAR DE LA FUNCIÓN LOCAL
        result = save_daily_tracking(
            user_id=user_id,
            tracking_date=tracking_date,
            completed_meals=completed_meals_dict,
            calorie_note=tracking_data.calorie_note,
            actual_calories=tracking_data.actual_calories,
            excess_deficit=tracking_data.excess_deficit
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al guardar el seguimiento")
        
        # Manejar el JSON serializado
        if isinstance(result['completed_meals'], str):
            try:
                result['completed_meals'] = json.loads(result['completed_meals'])
            except json.JSONDecodeError:
                logger.error(f"Error deserializing completed_meals: {result['completed_meals']}")
                result['completed_meals'] = {}
        
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
        
        # Get tracking data using service
        result = get_daily_tracking(
            user_id=user['id'],
            tracking_date=tracking_date
        )
        
        # Handle serialized JSON in completed_meals
        if result and isinstance(result['completed_meals'], str):
            try:
                result['completed_meals'] = json.loads(result['completed_meals'])
            except json.JSONDecodeError:
                logger.error(f"Error deserializing completed_meals: {result['completed_meals']}")
                result['completed_meals'] = {}
        
        return {"success": True, "tracking": result}
    
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
        # If no start_date is provided, use the current date
        if not start_date:
            today = datetime.now().date()
            # Find the most recent Monday (or use today if it's Monday)
            days_since_monday = today.weekday()
            start_date = (today - timedelta(days=days_since_monday)).isoformat()
        
        # Get tracking data using service
        tracking_data = get_weekly_tracking(user['id'], start_date)
        
        # Handle serialized JSON in completed_meals for each day
        for day in tracking_data:
            if day and isinstance(day['completed_meals'], str):
                try:
                    day['completed_meals'] = json.loads(day['completed_meals'])
                except json.JSONDecodeError:
                    logger.error(f"Error deserializing weekly completed_meals: {day['completed_meals']}")
                    day['completed_meals'] = {}
        
        return {"success": True, "tracking": tracking_data}
    
    except Exception as e:
        logger.error(f"Error fetching weekly tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener seguimiento semanal: {str(e)}")

@router.get("/tracking/summary", response_class=CustomJSONResponse)
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
        # If no start_date is provided, use the current date
        if not start_date:
            today = datetime.now().date()
            # Find the most recent Monday (or use today if it's Monday)
            days_since_monday = today.weekday()
            start_date = (today - timedelta(days=days_since_monday)).isoformat()
        
        # Calculate summary using service
        summary = calculate_weekly_summary(user['id'], start_date)
        
        return {"success": True, "summary": summary}
    
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
    
    try:
        # Validate date format (YYYY-MM-DD)
        try:
            tracking_date = datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
        
        # Delete tracking using service
        result = delete_daily_tracking(user['id'], tracking_date)
        
        if not result:
            raise HTTPException(status_code=404, detail="No se encontró registro de seguimiento para esta fecha")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar seguimiento: {str(e)}")