# back_end/gym/routes/meal_plans.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict

from ..middlewares import get_current_user
from ..models.nutrition_schemas import (
    MealPlanCreate,
    MealPlanUpdate,
    MealPlanResponse,
    MealPlanWithItems,
    MealPlanItemCreate,
    MealPlanItemUpdate,
    MealPlanItemResponse
)
from ..services.meal_plans_service import (
    create_meal_plan,
    list_meal_plans,
    get_meal_plan,
    update_meal_plan,
    delete_meal_plan
)
from ..services.meal_plan_items_service import (
    add_meal_to_plan,
    get_meal_plan_items,
    get_meal_plan_item,
    update_meal_plan_item,
    delete_meal_plan_item
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["meal_plans"])

#########################################
# Endpoints para Planes de Comida
#########################################

@router.post("/meal-plans", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan_endpoint(
    request: Request,
    meal_plan: MealPlanCreate,
    user = Depends(get_current_user)
):
    """Crea un nuevo plan de comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        meal_plan_data = meal_plan.model_dump()
        result = create_meal_plan(user.get('id'), meal_plan_data)
        
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
    """Lista todos los planes de comida del usuario."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        meal_plans_list = list_meal_plans(user.get('id'), is_active)
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
    """Obtiene un plan de comida por su ID, incluyendo todos sus elementos/comidas."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        result = get_meal_plan(meal_plan_id, user.get('id'))
        
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
    """Actualiza un plan de comida existente."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar si el plan existe y pertenece al usuario
        existing_plan = get_meal_plan(meal_plan_id, user.get('id'), with_items=False)
        if not existing_plan:
            raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_id} no encontrado")
        
        # Actualizar plan
        meal_plan_data = meal_plan.model_dump(exclude_unset=True)
        result = update_meal_plan(meal_plan_id, user.get('id'), meal_plan_data)
        
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
    """Elimina un plan de comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar si el plan existe y pertenece al usuario
        existing_plan = get_meal_plan(meal_plan_id, user.get('id'), with_items=False)
        if not existing_plan:
            raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_id} no encontrado")
        
        result = delete_meal_plan(meal_plan_id, user.get('id'))
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al eliminar plan de comida")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar plan de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar plan de comida: {str(e)}")

#########################################
# Endpoints para Elementos de Plan de Comida
#########################################

@router.post("/meal-plan-items", response_model=MealPlanItemResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_to_plan_endpoint(
    request: Request,
    meal_plan_item: MealPlanItemCreate,
    user = Depends(get_current_user)
):
    """Añade una comida a un plan de comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar que el plan pertenece al usuario
        meal_plan = get_meal_plan(meal_plan_item.meal_plan_id, user.get('id'), with_items=False)
        if not meal_plan:
            raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_item.meal_plan_id} no encontrado")
        
        # Añadir elemento
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
    """Obtiene un elemento/comida específico de un plan de comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        result = get_meal_plan_item(item_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Elemento de plan de comida con ID {item_id} no encontrado")
        
        # Verificar que el plan pertenece al usuario
        meal_plan = get_meal_plan(result['meal_plan_id'], user.get('id'), with_items=False)
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
    """Actualiza un elemento/comida en un plan de comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar que el elemento existe
        current_item = get_meal_plan_item(item_id)
        if not current_item:
            raise HTTPException(status_code=404, detail=f"Elemento de plan de comida con ID {item_id} no encontrado")
        
        # Verificar que el plan pertenece al usuario
        meal_plan = get_meal_plan(current_item['meal_plan_id'], user.get('id'), with_items=False)
        if not meal_plan:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este elemento")
        
        # Si se cambia el plan, verificar que el nuevo también pertenece al usuario
        if 'meal_plan_id' in meal_plan_item.model_dump(exclude_unset=True):
            new_plan = get_meal_plan(meal_plan_item.meal_plan_id, user.get('id'), with_items=False)
            if not new_plan:
                raise HTTPException(status_code=404, detail=f"Plan de comida con ID {meal_plan_item.meal_plan_id} no encontrado")
        
        # Actualizar elemento
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
    """Elimina un elemento/comida de un plan de comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar que el elemento existe
        current_item = get_meal_plan_item(item_id)
        if not current_item:
            raise HTTPException(status_code=404, detail=f"Elemento de plan de comida con ID {item_id} no encontrado")
        
        # Verificar que el plan pertenece al usuario
        meal_plan = get_meal_plan(current_item['meal_plan_id'], user.get('id'), with_items=False)
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