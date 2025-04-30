# back_end/gym/routes/nutrition/nutrition.py
"""
Este archivo está ahora en desuso.
Las funcionalidades han sido divididas en archivos más específicos:
- calculator.py: Para cálculos de macros y perfiles nutricionales
- ingredients.py: Para gestión de ingredientes
- meals.py: Para gestión de comidas
- meal_plans.py: Para gestión de planes de comida

Este archivo solo existe para mantener retrocompatibilidad
y redirigir a las implementaciones actuales.
"""

from fastapi import APIRouter, status, HTTPException
from back_end.gym.routes.nutrition.calculator import router as calculator_router

# Crear un router de redirección
router = APIRouter(prefix="/api/nutrition-legacy", tags=["nutrition-legacy"])

@router.get("/")
async def nutrition_redirector():
    """
    Endpoint informativo que redirige a los nuevos endpoints.
    """
    return {
        "message": "Este endpoint está en desuso. Por favor, usa los nuevos endpoints:",
        "calculator": "/api/nutrition/calculate-macros",
        "profile": "/api/nutrition/profile",
        "ingredients": "/api/nutrition/ingredients",
        "meals": "/api/nutrition/meals",
        "meal_plans": "/api/nutrition/meal-plans"
    }