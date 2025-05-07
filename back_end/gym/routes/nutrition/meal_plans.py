# back_end/gym/routes/nutrition/meal_plans.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict

# Changed relative imports to absolute
from back_end.gym.middlewares import get_current_user
from back_end.gym.models.nutrition_schemas import (
    MealPlanCreate,
    MealPlanUpdate,
    MealPlanResponse,
    MealPlanWithItems
)
from back_end.gym.services.nutrition.meal_plans_service import (
    create_meal_plan,
    list_meal_plans,
    get_meal_plan,
    update_meal_plan,
    delete_meal_plan
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["meal_plans"])

#########################################
# Endpoints for Meal Plans
#########################################

@router.post("/meal-plans", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan_endpoint(
    request: Request,
    meal_plan: MealPlanCreate,
    user = Depends(get_current_user)
):
    """Creates a new meal plan."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
        
        # Debug log to verify the ID being used
        logger.info(f"Creating meal plan for user ID: {user_id}")
        
        meal_plan_data = meal_plan.model_dump()
        result = create_meal_plan(user_id, meal_plan_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al crear plan de comida")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al crear plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear plan de comida: {str(e)}")

@router.get("/meal-plans", response_class=JSONResponse)
async def list_meal_plans_endpoint(
    request: Request,
    is_active: Optional[bool] = None,
    user = Depends(get_current_user)
):
    """Lists all meal plans for a user."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        meal_plans_list = list_meal_plans(user_id, is_active)
        return JSONResponse(content={"success": True, "meal_plans": meal_plans_list})
    
    except Exception as e:
        logger.error(f"Error al listar planes de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al listar planes de comida: {str(e)}")

@router.get("/meal-plans/{meal_plan_id}", response_model=MealPlanWithItems)
async def get_meal_plan_endpoint(
    request: Request,
    meal_plan_id: int,
    user = Depends(get_current_user)
):
    """Gets a meal plan by ID, including all its items."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        result = get_meal_plan(meal_plan_id, user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_id} no encontrado")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener plan de comida: {str(e)}")

@router.put("/meal-plans/{meal_plan_id}", response_model=MealPlanResponse)
async def update_meal_plan_endpoint(
    request: Request,
    meal_plan_id: int,
    meal_plan: MealPlanUpdate,
    user = Depends(get_current_user)
):
    """Updates an existing meal plan."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        # Check if the plan exists and belongs to the user
        existing_plan = get_meal_plan(meal_plan_id, user_id, with_items=False)
        if not existing_plan:
            raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_id} no encontrado")
        
        # Update plan
        meal_plan_data = meal_plan.model_dump(exclude_unset=True)
        result = update_meal_plan(meal_plan_id, user_id, meal_plan_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al actualizar plan de comida")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar plan de comida: {str(e)}")

@router.delete("/meal-plans/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan_endpoint(
    request: Request,
    meal_plan_id: int,
    user = Depends(get_current_user)
):
    """Deletes a meal plan."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        # Check if the plan exists and belongs to the user
        existing_plan = get_meal_plan(meal_plan_id, user_id, with_items=False)
        if not existing_plan:
            raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_id} no encontrado")
        
        result = delete_meal_plan(meal_plan_id, user_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al eliminar plan de comida")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar plan de comida: {str(e)}")