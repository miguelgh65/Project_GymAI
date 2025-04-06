# Archivo: back_end/gym/routes/routine.py
import os
import sys

from dotenv import load_dotenv
# Ajusta la ruta si es necesario
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import json
import secrets
from datetime import datetime, timedelta
import logging # Importar logging

import psycopg2
import requests
# Ajusta las rutas de importación según tu estructura
try:
    from config import DB_CONFIG
    from fastapi import (APIRouter, Depends, Form, HTTPException, Query, Request,
                        Response, status) # Añadir status
    from fastapi.responses import JSONResponse, RedirectResponse
    from services.database import get_routine, get_today_routine, save_routine
    from back_end.gym.middlewares import get_current_user
    from utils.date_utils import get_weekday_name # Importar desde utils
except ImportError as e:
    logging.error(f"Error de importación en routine.py: {e}")
    # Define stubs si es necesario para que el archivo cargue
    async def get_current_user(request: Request): return None
    def get_routine(user_id): return {}
    def get_today_routine(user_id): return {"success": False, "message": "Error interno"}
    def save_routine(user_id, data): return False
    def get_weekday_name(day_num): return "Desconocido"
    DB_CONFIG = {} # Placeholder

# Make sure to load environment variables
load_dotenv()

# Añadir prefijo /api
router = APIRouter(prefix="/api", tags=["routine"])
logger = logging.getLogger(__name__) # Logger


# Ruta: /api/rutina_hoy
@router.get("/rutina_hoy", response_class=JSONResponse)
async def rutina_hoy(request: Request, format: str = Query(None), user = Depends(get_current_user)):
    """Página de rutina del día."""
    if not user or not user.get('google_id'):
        logger.warning("Intento de acceso a /api/rutina_hoy sin autenticación válida.")
        # Devolver 401 si no está autenticado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado o sin ID válido."
        )

    user_id = user['google_id']
    logger.info(f"Obteniendo rutina de hoy para usuario Google ID: {user_id}")

    result = get_today_routine(user_id)
    # Añadir día actual a la respuesta si no lo incluye get_today_routine
    if 'dia_nombre' not in result:
         dia_actual_num = datetime.now().isoweekday()
         result['dia_nombre'] = get_weekday_name(dia_actual_num)

    # Devolver siempre JSONResponse para consistencia
    return JSONResponse(content=result)

# Ruta: /api/rutina (GET)
@router.get("/rutina", response_class=JSONResponse)
async def get_routine_config(request: Request, format: str = Query(None), user = Depends(get_current_user)):
    """Página de configuración de rutina."""
    if not user or not user.get('google_id'):
        logger.warning("Intento de acceso a GET /api/rutina sin autenticación válida.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado o sin ID válido."
        )

    user_id = user['google_id']
    logger.info(f"Obteniendo configuración de rutina para usuario Google ID: {user_id}")

    rutina_data = get_routine(user_id)
    # Devolver siempre éxito true si la obtención fue posible (incluso si está vacía)
    return JSONResponse(content={"success": True, "rutina": rutina_data if rutina_data is not None else {}})

# Ruta: /api/rutina (POST)
@router.post("/rutina", response_class=JSONResponse)
async def save_routine_config(request: Request, user = Depends(get_current_user)):
    """Guarda la configuración de rutina."""
    if not user or not user.get('google_id'):
         logger.warning("Intento de acceso a POST /api/rutina sin autenticación válida.")
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Usuario no autenticado o sin ID válido."
         )

    user_id = user['google_id']
    logger.info(f"Intentando guardar rutina para usuario Google ID: {user_id}")

    try:
        data = await request.json()
        rutina_data = data.get("rutina", {})
        logger.debug(f"Datos de rutina recibidos: {rutina_data}")

        success = save_routine(user_id, rutina_data)

        if success:
            logger.info(f"Rutina guardada exitosamente para usuario Google ID: {user_id}")
            return JSONResponse(content={
                "success": True,
                "message": "Rutina actualizada correctamente"
            })
        else:
            logger.error(f"Fallo al guardar rutina en la BD para usuario Google ID: {user_id}")
            raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="Error al guardar la rutina en la base de datos."
             )
    except json.JSONDecodeError:
         logger.error("Error al decodificar JSON en POST /api/rutina")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato JSON inválido.")
    except Exception as e:
        logger.exception(f"Error inesperado en POST /api/rutina para usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

