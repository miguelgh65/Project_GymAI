# back_end/gym/routes/nutrition/__init__.py
from fastapi import APIRouter

# Importar todos los sub-routers de nutrición
# Asegurarse de que las importaciones sean correctas
# usando rutas absolutas si hay problemas con las rutas relativas
from back_end.gym.routes.nutrition.ingredients import router as ingredients_router
from back_end.gym.routes.nutrition.meals import router as meals_router
from back_end.gym.routes.nutrition.meal_plans import router as meal_plans_router
from back_end.gym.routes.nutrition.calculator import router as calculator_router

# Crear un router combinado para todas las rutas de nutrición
router = APIRouter()

# Incluir todos los sub-routers
router.include_router(ingredients_router)
router.include_router(meals_router)
router.include_router(meal_plans_router)
router.include_router(calculator_router)

# Exportar el router combinado
__all__ = ["router"]