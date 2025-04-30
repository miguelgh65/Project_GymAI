# back_end/gym/routes/nutrition/__init__.py
from fastapi import APIRouter
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a combined router for all nutrition endpoints
router = APIRouter()

# Import all nutrition-related routers
try:
    # Calculator router
    from .calculator import router as calculator_router
    router.include_router(calculator_router)
    logger.info("✅ Calculator router included")
except ImportError as e:
    logger.error(f"❌ Error importing calculator router: {e}")

try:
    # Ingredients router
    from .ingredients import router as ingredients_router
    router.include_router(ingredients_router)
    logger.info("✅ Ingredients router included")
except ImportError as e:
    logger.error(f"❌ Error importing ingredients router: {e}")

try:
    # Meals router
    from .meals import router as meals_router
    router.include_router(meals_router)
    logger.info("✅ Meals router included")
except ImportError as e:
    logger.error(f"❌ Error importing meals router: {e}")

try:
    # Meal plans router
    from .meal_plans import router as meal_plans_router
    router.include_router(meal_plans_router)
    logger.info("✅ Meal plans router included")
except ImportError as e:
    logger.error(f"❌ Error importing meal plans router: {e}")

try:
    # TRACKING ROUTER - Make sure this is included!
    from .tracking import router as tracking_router
    router.include_router(tracking_router)
    logger.info("✅ Tracking router included")
except ImportError as e:
    logger.error(f"❌ Error importing tracking router: {e}")

# Additional nutrition-related routers can be added here

# Export the combined router
__all__ = ['router']