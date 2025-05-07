# back_end/gym/routes/nutrition/meal_plan_items.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Dict

# Changed relative imports to absolute
from back_end.gym.middlewares import get_current_user
from back_end.gym.models.nutrition_schemas import (
    MealPlanItemCreate,
    MealPlanItemUpdate,
    MealPlanItemResponse
)
from back_end.gym.services.nutrition.meal_plans_service import get_meal_plan
from back_end.gym.services.nutrition.meal_plan_items_service import (
    add_meal_to_plan,
    get_meal_plan_item,
    update_meal_plan_item,
    delete_meal_plan_item
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["meal_plan_items"])

#########################################
# Endpoints for Meal Plan Items
#########################################

@router.post("/meal-plan-items", response_model=MealPlanItemResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_to_plan_endpoint(
    request: Request,
    meal_plan_item: MealPlanItemCreate,
    user = Depends(get_current_user)
):
    """Adds a meal to a meal plan."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        # Check if the plan belongs to the user
        meal_plan = get_meal_plan(meal_plan_item.meal_plan_id, user_id, with_items=False)
        if not meal_plan:
            raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_item.meal_plan_id} no encontrado")
        
        # Add item
        meal_plan_item_data = meal_plan_item.model_dump()
        result = add_meal_to_plan(meal_plan_item_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al añadir comida al plan")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al añadir comida al plan: {e}")
        raise HTTPException(status_code=500, detail=f"Error al añadir comida al plan: {str(e)}")

@router.get("/meal-plan-items/{item_id}", response_model=MealPlanItemResponse)
async def get_meal_plan_item_endpoint(
    request: Request,
    item_id: int,
    user = Depends(get_current_user)
):
    """Gets a specific meal plan item."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        result = get_meal_plan_item(item_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Elemento de plan de comida con ID {item_id} no encontrado")
        
        # Check if the plan belongs to the user
        meal_plan = get_meal_plan(result['meal_plan_id'], user_id, with_items=False)
        if not meal_plan:
            raise HTTPException(status_code=403, detail="No tienes permiso para acceder a este elemento")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener elemento de plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener elemento de plan de comida: {str(e)}")

@router.put("/meal-plan-items/{item_id}", response_model=MealPlanItemResponse)
async def update_meal_plan_item_endpoint(
    request: Request,
    item_id: int,
    meal_plan_item: MealPlanItemUpdate,
    user = Depends(get_current_user)
):
    """Updates a meal plan item."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        # Check if the item exists
        current_item = get_meal_plan_item(item_id)
        if not current_item:
            raise HTTPException(status_code=404, detail=f"Elemento de plan de comida con ID {item_id} no encontrado")
        
        # Check if the plan belongs to the user
        meal_plan = get_meal_plan(current_item['meal_plan_id'], user_id, with_items=False)
        if not meal_plan:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este elemento")
        
        # If changing the plan, check if the new one belongs to the user
        if 'meal_plan_id' in meal_plan_item.model_dump(exclude_unset=True):
            new_plan = get_meal_plan(meal_plan_item.meal_plan_id, user_id, with_items=False)
            if not new_plan:
                raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_item.meal_plan_id} no encontrado")
        
        # Update item
        meal_plan_item_data = meal_plan_item.model_dump(exclude_unset=True)
        result = update_meal_plan_item(item_id, meal_plan_item_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al actualizar elemento de plan de comida")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar elemento de plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar elemento de plan de comida: {str(e)}")

@router.delete("/meal-plan-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan_item_endpoint(
    request: Request,
    item_id: int,
    user = Depends(get_current_user)
):
    """Deletes a meal plan item."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # FIX: Get Google ID first, fall back to internal ID
        user_id = user.get('google_id')
        if not user_id:
            user_id = user.get('id')
            
        # Check if the item exists
        current_item = get_meal_plan_item(item_id)
        if not current_item:
            raise HTTPException(status_code=404, detail=f"Elemento de plan de comida con ID {item_id} no encontrado")
        
        # Check if the plan belongs to the user
        meal_plan = get_meal_plan(current_item['meal_plan_id'], user_id, with_items=False)
        if not meal_plan:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este elemento")
        
        result = delete_meal_plan_item(item_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al eliminar elemento de plan de comida")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar elemento de plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar elemento de plan de comida: {str(e)}")