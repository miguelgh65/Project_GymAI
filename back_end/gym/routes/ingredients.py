# back_end/gym/routes/ingredients.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Optional

from ..middlewares import get_current_user
from ..models.nutrition_schemas import (
    IngredientCreate, 
    IngredientUpdate, 
    IngredientResponse
)
from ..services.ingredient_service import (
    get_ingredient,
    create_ingredient,
    list_ingredients,
    update_ingredient,
    delete_ingredient,
    check_ingredient_exists
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nutrition", tags=["ingredients"])

@router.post("/ingredients", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient_endpoint(
    request: Request,
    ingredient: IngredientCreate,
    user = Depends(get_current_user)
):
    """Crea un nuevo ingrediente."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        ingredient_data = ingredient.model_dump()
        result = create_ingredient(ingredient_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al crear ingrediente")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al crear ingrediente: {e}")
        if "duplicate key" in str(e):
            raise HTTPException(status_code=409, detail=f"Ingrediente '{ingredient.ingredient_name}' ya existe")
        raise HTTPException(status_code=500, detail=f"Error al crear ingrediente: {str(e)}")

@router.get("/ingredients", response_class=JSONResponse)
async def list_ingredients_endpoint(
    request: Request,
    search: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Lista todos los ingredientes, con opción de búsqueda."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        ingredients_list = list_ingredients(search)
        return JSONResponse(content={"success": True, "ingredients": ingredients_list})
    
    except Exception as e:
        logger.error(f"Error al listar ingredientes: {e}")
        raise HTTPException(status_code=500, detail=f"Error al listar ingredientes: {str(e)}")

@router.get("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient_endpoint(
    request: Request,
    ingredient_id: int,
    user = Depends(get_current_user)
):
    """Obtiene un ingrediente por su ID."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        result = get_ingredient(ingredient_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Ingrediente con ID {ingredient_id} no encontrado")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener ingrediente: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener ingrediente: {str(e)}")

@router.put("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient_endpoint(
    request: Request,
    ingredient_id: int,
    ingredient: IngredientUpdate,
    user = Depends(get_current_user)
):
    """Actualiza un ingrediente existente."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar si el ingrediente existe
        if not check_ingredient_exists(ingredient_id):
            raise HTTPException(status_code=404, detail=f"Ingrediente con ID {ingredient_id} no encontrado")
        
        # Actualizar ingrediente
        ingredient_data = ingredient.model_dump(exclude_unset=True)
        result = update_ingredient(ingredient_id, ingredient_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al actualizar ingrediente")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar ingrediente: {e}")
        if "duplicate key" in str(e):
            raise HTTPException(status_code=409, detail=f"Ya existe un ingrediente con el nombre proporcionado")
        raise HTTPException(status_code=500, detail=f"Error al actualizar ingrediente: {str(e)}")

@router.delete("/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient_endpoint(
    request: Request,
    ingredient_id: int,
    user = Depends(get_current_user)
):
    """Elimina un ingrediente."""
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    try:
        # Verificar si el ingrediente existe
        if not check_ingredient_exists(ingredient_id):
            raise HTTPException(status_code=404, detail=f"Ingrediente con ID {ingredient_id} no encontrado")
        
        result = delete_ingredient(ingredient_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al eliminar ingrediente")
        
        return None
    
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar ingrediente: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar ingrediente: {str(e)}")