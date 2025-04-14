# Archivo: back_end/gym/routes/fitbit/__init__.py
from fastapi import APIRouter

# Importar routers
from .routes import router as fitbit_routes
from .callbacks import router as fitbit_callbacks

# Combinar los routers en uno solo
router = APIRouter()
router.include_router(fitbit_routes)
router.include_router(fitbit_callbacks)

# Para importar fácilmente en app_fastapi.py: from .routes.fitbit import router as fitbit_router