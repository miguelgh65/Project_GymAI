# back_end/gym/routes/meals.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict

from ..middlewares import get_current_user
from ..models.nutrition_schemas import (
    MealCreate, 
    MealUpdate, 
    MealResponse,
    MealIngredientCreate,
    MealIngredientUpdate,
    MealIngredientResponse
)
from ..services.meal_service import (
    get_meal,
    create_meal,
    list_meals,
    update_meal,
    delete_meal,
    check_meal_exists,
    add_ingredient_to_meal,
    get_meal_ingredients,
    update_meal_ingredient,
    delete_meal_ingredient,
    recalculate_meal_macros  # Aunque no lo uses directamente, está disponible
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["meals"])

#########################################
# Endpoints para Comidas (Meals)
#########################################

@router.post("/meals", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_endpoint(
    request: Request,
    meal: MealCreate,
    user = Depends(get_current_user)
):
    """Crea una nueva comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        meal_data = meal.model_dump()
        result = create_meal(meal_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al crear comida")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al crear comida: {e}")
        if "duplicate key" in str(e):
            raise HTTPException(status_code=409, detail=f"Ya existe una comida con el nombre '{meal.meal_name}'")
        raise HTTPException(status_code=500, detail=f"Error al crear comida: {str(e)}")

@router.get("/meals", response_class=JSONResponse)
async def list_meals_endpoint(
    request: Request,
    search: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Lista todas las comidas, con opción de búsqueda."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        meals_list = list_meals(search)
        return JSONResponse(content={"success": True, "meals": meals_list})
    
    except Exception as e:
        logger.error(f"Error al listar comidas: {e}")
        raise HTTPException(status_code=500, detail=f"Error al listar comidas: {str(e)}")

@router.get("/meals/{meal_id}", response_model=Dict)
async def get_meal_endpoint(
    request: Request,
    meal_id: int,
    with_ingredients: bool = False,
    user = Depends(get_current_user)
):
    """Obtiene una comida por su ID. Opcionalmente incluye ingredientes detallados."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        result = get_meal(meal_id, with_ingredients)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Comida con ID {meal_id} no encontrada")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener comida: {str(e)}")

@router.put("/meals/{meal_id}", response_model=MealResponse)
async def update_meal_endpoint(
    request: Request,
    meal_id: int,
    meal: MealUpdate,
    user = Depends(get_current_user)
):
    """Actualiza una comida existente."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar si la comida existe
        if not check_meal_exists(meal_id):
            raise HTTPException(status_code=404, detail=f"Comida con ID {meal_id} no encontrada")
        
        # Actualizar comida
        meal_data = meal.model_dump(exclude_unset=True)
        result = update_meal(meal_id, meal_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al actualizar comida")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar comida: {e}")
        if "duplicate key" in str(e):
            raise HTTPException(status_code=409, detail=f"Ya existe una comida con el nombre proporcionado")
        raise HTTPException(status_code=500, detail=f"Error al actualizar comida: {str(e)}")

@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_endpoint(
    request: Request,
    meal_id: int,
    user = Depends(get_current_user)
):
    """Elimina una comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar si la comida existe
        if not check_meal_exists(meal_id):
            raise HTTPException(status_code=404, detail=f"Comida con ID {meal_id} no encontrada")
        
        result = delete_meal(meal_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al eliminar comida")
        
        return None
    
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar comida: {str(e)}")

#########################################
# Endpoints para relación Meal-Ingredient
#########################################

@router.post("/meal-ingredients", response_model=MealIngredientResponse, status_code=status.HTTP_201_CREATED)
async def add_ingredient_to_meal_endpoint(
    request: Request,
    meal_ingredient: MealIngredientCreate,
    user = Depends(get_current_user)
):
    """Añade un ingrediente a una comida con su cantidad."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        result = add_ingredient_to_meal(
            meal_ingredient.meal_id,
            meal_ingredient.ingredient_id,
            meal_ingredient.quantity
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al añadir ingrediente a la comida")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al añadir ingrediente a comida: {e}")
        if "duplicate key" in str(e):
            raise HTTPException(status_code=409, detail="Este ingrediente ya está asociado a esta comida")
        raise HTTPException(status_code=500, detail=f"Error al añadir ingrediente a comida: {str(e)}")

@router.get("/meals/{meal_id}/ingredients", response_class=JSONResponse)
async def get_meal_ingredients_endpoint(
    request: Request,
    meal_id: int,
    user = Depends(get_current_user)
):
    """Obtiene todos los ingredientes de una comida con sus cantidades."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        ingredients_list = get_meal_ingredients(meal_id)
        return JSONResponse(content={"success": True, "meal_id": meal_id, "ingredients": ingredients_list})
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al obtener ingredientes de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener ingredientes de comida: {str(e)}")

@router.put("/meal-ingredients/{meal_ingredient_id}", response_model=MealIngredientResponse)
async def update_meal_ingredient_endpoint(
    request: Request,
    meal_ingredient_id: int,
    meal_ingredient: MealIngredientUpdate,
    user = Depends(get_current_user)
):
    """Actualiza la cantidad de un ingrediente en una comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        meal_ingredient_data = meal_ingredient.model_dump(exclude_unset=True)
        result = update_meal_ingredient(meal_ingredient_id, meal_ingredient_data)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Relación comida-ingrediente con ID {meal_ingredient_id} no encontrada")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al actualizar ingrediente en comida: {e}")
        if "duplicate key" in str(e):
            raise HTTPException(status_code=409, detail="Ya existe una relación con esta comida e ingrediente")
        raise HTTPException(status_code=500, detail=f"Error al actualizar ingrediente en comida: {str(e)}")

@router.delete("/meal-ingredients/{meal_ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_ingredient_endpoint(
    request: Request,
    meal_ingredient_id: int,
    user = Depends(get_current_user)
):
    """Elimina un ingrediente de una comida."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        result = delete_meal_ingredient(meal_ingredient_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Relación comida-ingrediente con ID {meal_ingredient_id} no encontrada")
        
        return None
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al eliminar ingrediente de comida: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar ingrediente de comida: {str(e)}")