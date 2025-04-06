# Archivo: back_end/gym/routes/routine.py
import os
import sys
from dotenv import load_dotenv
import base64
import json
import secrets
from datetime import datetime, timedelta
import logging
import psycopg2 # Importado pero quizás no usado directamente aquí si usas servicios
import requests
# Ajusta las rutas de importación según tu estructura
try:
    # <<< --- CORRECCIÓN DE IMPORTACIONES --- >>>
    # Importa DB_CONFIG y otras configuraciones necesarias
    from ..config import DB_CONFIG
    from fastapi import (APIRouter, Depends, Form, HTTPException, Query, Request,
                         Response, status)
    from fastapi.responses import JSONResponse, RedirectResponse
    # Importa las funciones de servicio CORRECTAS que necesitas
    # Asegúrate que estas funciones existen y hacen lo que se espera
    from ..services.database import get_routine, get_today_routine, save_routine
    # Importa la función para obtener el ID de Google/interno desde Telegram ID
    # Asumimos que existe una función así en auth_service o database_service
    from ..services.auth_service import get_user_id_by_telegram # O get_google_id_by_telegram si la tienes

    # Importa tu middleware de autenticación
    from ..middlewares import get_current_user # Ajusta la ruta si es diferente
    # Importa utilidades si las usas
    from ..utils.date_utils import get_weekday_name # Ajusta la ruta si es diferente

except ImportError as e:
    logging.error(f"Error CRÍTICO de importación en routine.py: {e}. Revisa las rutas.")
    # Define stubs o lanza error si es crítico para el arranque
    async def get_current_user(request: Request): return None
    def get_routine(user_id): return {}
    def get_today_routine(user_id): return {"success": False, "message": "Error interno (stub)"}
    def save_routine(user_id, data): return False
    def get_user_id_by_telegram(telegram_id: str): return None # Placeholder
    def get_weekday_name(day_num): return "Desconocido"
    DB_CONFIG = {} # Placeholder
    # Considera lanzar 'raise e' si la app no debe iniciar sin estas importaciones

# Make sure to load environment variables
load_dotenv()

# Añadir prefijo /api
router = APIRouter(prefix="/api", tags=["routine"])
logger = logging.getLogger(__name__) # Logger

# Ruta: /api/rutina_hoy
@router.get("/rutina_hoy", response_class=JSONResponse)
async def rutina_hoy(
    request: Request,
    format: str = Query(None),
    telegram_id: str = Query(None, description="ID de Telegram del usuario"), # Renombrado para claridad
    user = Depends(get_current_user) # Obtiene info del usuario autenticado (web o bot)
):
    """Obtiene la rutina programada para el día de hoy para el usuario."""
    if not user:
        logger.warning("Intento de acceso a /api/rutina_hoy sin autenticación válida.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado o sin ID válido."
        )

    is_telegram_bot_request = user.get('is_telegram_bot', False)
    user_id_for_logic = None # ID que se usará para consultar rutinas (debería ser google_id o ID interno)

    if is_telegram_bot_request:
        # --- LÓGICA CORREGIDA PARA BOT DE TELEGRAM ---
        if not telegram_id:
            logger.error("Bot solicitó rutina pero no proporcionó telegram_id en los parámetros Query.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parámetro 'telegram_id' requerido para solicitudes del bot.")

        logger.info(f"Bot solicitando rutina para telegram_id: {telegram_id}")
        # Buscar el ID interno/google_id correspondiente al telegram_id
        # Asume que get_user_id_by_telegram devuelve el ID interno/google_id necesario para rutinas
        # O usa una función get_google_id_by_telegram si la tienes
        internal_user_id = get_user_id_by_telegram(str(telegram_id)) # Llama a tu función de servicio

        if not internal_user_id:
            logger.warning(f"No se encontró un usuario interno/google_id vinculado al telegram_id: {telegram_id}")
            # Puedes decidir devolver success: False o un error 404/403
            return JSONResponse(content={
                "success": False,
                "message": "Este usuario de Telegram no está vinculado a una cuenta.",
                "dia_nombre": get_weekday_name(datetime.now().isoweekday()), # Nombre del día actual
                "rutina": []
            }, status_code=status.HTTP_404_NOT_FOUND) # O 403 Forbidden si prefieres

        user_id_for_logic = internal_user_id # Usar el ID interno/google_id encontrado
        logger.info(f"Telegram ID {telegram_id} corresponde a Usuario ID (interno/google): {user_id_for_logic}")
        # --- FIN LÓGICA CORREGIDA ---
    else:
        # Usuario normal (Google/Web)
        user_id_for_logic = user.get('google_id') # Usa google_id si está disponible
        if not user_id_for_logic:
             user_id_for_logic = str(user.get('id')) # Fallback al ID interno si google_id no está
        logger.info(f"Usuario Web solicitando rutina. Usando ID: {user_id_for_logic}")

    if not user_id_for_logic:
        logger.error(f"CRÍTICO: No se pudo determinar un ID de usuario válido para la lógica. Usuario autenticado: {user}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno: No se pudo identificar al usuario para la consulta.")

    logger.info(f"Obteniendo rutina de hoy para Usuario ID (interno/google): {user_id_for_logic}")

    # Llamar al servicio de base de datos con el ID CORRECTO
    result = get_today_routine(user_id_for_logic)

    # Añadir día actual a la respuesta si no lo incluye get_today_routine
    if 'dia_nombre' not in result:
        try:
            # Usar timezone si está configurada
            tz_madrid = ZoneInfo("Europe/Madrid") # Necesita: from zoneinfo import ZoneInfo
            now_local = datetime.now(tz_madrid)
        except NameError: # Fallback si zoneinfo no está disponible
             now_local = datetime.now()
        dia_actual_num = now_local.isoweekday()
        result['dia_nombre'] = get_weekday_name(dia_actual_num) # Usa tu helper

    # Devolver siempre JSONResponse para consistencia
    # El status code HTTP será 200 OK, el 'success' dentro del JSON indica si se encontró rutina
    return JSONResponse(content=result)


# Ruta: /api/rutina (GET)
@router.get("/rutina", response_class=JSONResponse)
async def get_routine_config(
    request: Request,
    format: str = Query(None), # Parámetro 'format' parece no usarse, considerar quitarlo
    telegram_id: str = Query(None, description="ID de Telegram del usuario"),
    user = Depends(get_current_user)
):
    """Obtiene la configuración completa de la rutina semanal del usuario."""
    if not user:
        logger.warning("Intento de acceso a GET /api/rutina sin autenticación válida.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado o sin ID válido."
        )

    is_telegram_bot_request = user.get('is_telegram_bot', False)
    user_id_for_logic = None

    if is_telegram_bot_request:
        # --- LÓGICA CORREGIDA PARA BOT DE TELEGRAM ---
        if not telegram_id:
            logger.error("Bot solicitó config rutina pero no proporcionó telegram_id.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parámetro 'telegram_id' requerido.")

        logger.info(f"Bot solicitando config rutina para telegram_id: {telegram_id}")
        internal_user_id = get_user_id_by_telegram(str(telegram_id))
        if not internal_user_id:
            logger.warning(f"No se encontró usuario interno/google_id para telegram_id: {telegram_id}")
            # Devuelve éxito true pero rutina vacía, ya que la llamada fue válida pero no hay datos
            return JSONResponse(content={"success": True, "rutina": {}})
        user_id_for_logic = internal_user_id
        logger.info(f"Telegram ID {telegram_id} -> Usuario ID (interno/google): {user_id_for_logic}")
        # --- FIN LÓGICA CORREGIDA ---
    else:
        # Usuario normal (Google/Web)
        user_id_for_logic = user.get('google_id')
        if not user_id_for_logic: user_id_for_logic = str(user.get('id'))
        logger.info(f"Usuario Web solicitando config rutina. Usando ID: {user_id_for_logic}")

    if not user_id_for_logic:
        logger.error(f"CRÍTICO: No se pudo determinar ID válido para GET /api/rutina. Usuario: {user}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno: No se pudo identificar al usuario.")

    logger.info(f"Obteniendo configuración de rutina para Usuario ID (interno/google): {user_id_for_logic}")

    # Llama al servicio con el ID correcto
    rutina_data = get_routine(user_id_for_logic)
    # Devuelve siempre éxito true si la obtención fue posible (incluso si está vacía)
    return JSONResponse(content={"success": True, "rutina": rutina_data if rutina_data is not None else {}})


# Ruta: /api/rutina (POST)
@router.post("/rutina", response_class=JSONResponse)
async def save_routine_config(
    request: Request,
    user = Depends(get_current_user)
):
    """Guarda la configuración de rutina semanal para el usuario."""
    if not user:
         logger.warning("Intento de acceso a POST /api/rutina sin autenticación válida.")
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Usuario no autenticado o sin ID válido."
         )

    is_telegram_bot_request = user.get('is_telegram_bot', False)
    user_id_for_logic = None

    try:
        data = await request.json()
        rutina_data_received = data.get("rutina", {}) # Datos de rutina a guardar
        logger.debug(f"Datos de rutina recibidos para guardar: {rutina_data_received}")

        if is_telegram_bot_request:
            # --- LÓGICA CORREGIDA PARA BOT DE TELEGRAM ---
            telegram_id_from_payload = data.get('telegram_id') # Bot debe enviar su ID en el payload
            if not telegram_id_from_payload:
                logger.error("Bot intentó guardar rutina pero no proporcionó telegram_id en el payload JSON.")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload debe incluir 'telegram_id' para solicitudes del bot.")

            logger.info(f"Bot guardando rutina. Payload telegram_id: {telegram_id_from_payload}")
            internal_user_id = get_user_id_by_telegram(str(telegram_id_from_payload))
            if not internal_user_id:
                logger.error(f"Bot intentó guardar rutina para telegram_id no vinculado: {telegram_id_from_payload}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario de Telegram no vinculado encontrado.")
            user_id_for_logic = internal_user_id
            logger.info(f"Telegram ID {telegram_id_from_payload} -> Usuario ID (interno/google): {user_id_for_logic}")
             # --- FIN LÓGICA CORREGIDA ---
        else:
            # Usuario normal (Google/Web)
            user_id_for_logic = user.get('google_id')
            if not user_id_for_logic: user_id_for_logic = str(user.get('id'))
            logger.info(f"Usuario Web guardando rutina. Usando ID: {user_id_for_logic}")

        if not user_id_for_logic:
            logger.error(f"CRÍTICO: No se pudo determinar ID válido para POST /api/rutina. Usuario: {user}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno: No se pudo identificar al usuario.")

        logger.info(f"Intentando guardar rutina para Usuario ID (interno/google): {user_id_for_logic}")

        # Llama al servicio con el ID correcto y los datos de rutina
        success = save_routine(user_id_for_logic, rutina_data_received)

        if success:
            logger.info(f"Rutina guardada exitosamente para usuario ID: {user_id_for_logic}")
            return JSONResponse(content={
                "success": True,
                "message": "Rutina actualizada correctamente"
            })
        else:
            logger.error(f"Fallo al guardar rutina en la BD para usuario ID: {user_id_for_logic}")
            raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="Error al guardar la rutina en la base de datos."
             )
    except json.JSONDecodeError:
         logger.error("Error al decodificar JSON en POST /api/rutina")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato JSON inválido.")
    except Exception as e:
        user_id_for_log = user_id_for_logic if 'user_id_for_logic' in locals() and user_id_for_logic else user.get('id', 'desconocido')
        logger.exception(f"Error inesperado en POST /api/rutina para usuario {user_id_for_log}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")