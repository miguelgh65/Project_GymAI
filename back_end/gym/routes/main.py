# Archivo: back_end/gym/routes/main.py
import os
import sys
import logging
import json
import datetime # Asegúrate que datetime está importado si usas tipos de fecha aquí

# Asegúrate de que esta ruta funcione en tu entorno. Ajusta si es necesario.
# (Comentado porque puede depender de cómo ejecutas)
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
# Asumiendo que los servicios y utils están en las rutas correctas
# Ajusta estas importaciones si tu estructura es diferente
try:
    # <<< CORRECCIÓN IMPORTACIÓN >>>
    # Importar TODAS las funciones necesarias de database.py
    from services.database import (
        get_exercise_logs,
        insert_into_db,
        reset_today_routine_status # <-- Asegúrate que esta línea esté presente
    )
    from services.prompt_service import format_for_postgres
    from utils.formatting import clean_input
    # Asumiendo que el middleware está en la ruta correcta
    from back_end.gym.middlewares import get_current_user
except ImportError as e:
     # Manejo básico de error de importación
     logging.error(f"Error de importación en main.py: {e}. Verifica las rutas.")
     # Podrías querer lanzar una excepción o definir stubs si es crítico
     # Por ahora, definimos stubs para que el archivo no falle al cargar
     async def get_current_user(request: Request): return None
     def get_exercise_logs(user_id, days): return []
     def insert_into_db(json_data, user_id): return False
     # Quita o comenta el stub si la importación real funciona
     # def reset_today_routine_status(user_id):
     #     logging.error("STUB INUTILIZADO: reset_today_routine_status debería importarse correctamente.")
     #     return False
     def format_for_postgres(text): return None
     def clean_input(text): return text

# Añade el prefijo /api aquí
router = APIRouter(prefix="/api", tags=["main"])
logger = logging.getLogger(__name__) # Usar __name__ es una buena práctica

# La ruta ahora es relativa al prefijo: /api/
@router.get("", response_class=JSONResponse) # Ruta -> /api/
async def get_api_root(request: Request, user = Depends(get_current_user)):
    # Mantenemos la ruta GET /api/ para un status check simple de la API
    logger.info(f"Acceso a la raíz de la API. User: {user.get('id') if user else 'None'}")
    return JSONResponse(content={
        "success": True,
        "message": "API funcionando correctamente",
        "user_id": user.get("id") if user else None,
        "google_id": user.get("google_id") if user else None
    })

# La ruta ahora es relativa al prefijo: /api/log-exercise
@router.post("/log-exercise", response_class=JSONResponse, status_code=status.HTTP_200_OK) # Ruta -> /api/log-exercise
async def log_exercise_endpoint(
    request: Request,
    user = Depends(get_current_user)
):
    logger.info("Iniciando procesamiento de registro de ejercicio con IA en /api/log-exercise")

    if not user:
        logger.warning("Intento de registro sin autenticación en /api/log-exercise")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado.")

    # Determinar qué ID usar para la lógica de negocio (Google ID parece ser el principal)
    user_id_for_logic = user.get('google_id')
    if not user_id_for_logic:
         # Fallback al ID interno si no hay Google ID (revisar si esto es correcto para tu lógica)
         user_id_for_logic = str(user.get('id'))
         if not user_id_for_logic:
             logger.error(f"No se pudo determinar un ID válido para el usuario: {user}")
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ID de usuario inválido.")

    logger.info(f"Procesando para user_id_for_logic: {user_id_for_logic}")

    try:
        content_type = request.headers.get("content-type", "")
        exercise_data = None
        day_name_for_reset = None # Variable para guardar el día si se envía para reset

        # Extraer datos (igual que antes)
        if "application/json" in content_type:
            data = await request.json()
            exercise_data = data.get('exercise_data', '').strip()
            day_name_for_reset = data.get('day_name') # Intenta obtener day_name si viene en JSON
            logger.info("Recibido JSON desde la web")
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
             form_data = await request.form()
             exercise_data = form_data.get('exercise_data', '').strip()
             logger.info("Recibido Form Data (probablemente Telegram)")
        else:
            logger.error(f"Content-Type no soportado: {content_type}")
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content-Type no soportado.")


        if not exercise_data:
            logger.warning(f"Intento de registro sin datos para usuario {user_id_for_logic}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos de ejercicio no proporcionados.")

        # <<< INICIO CORRECCIÓN: Llamada a función real >>>
        if exercise_data == 'RESET_ROUTINE':
            logger.info(f"Recibida señal RESET_ROUTINE para usuario {user_id_for_logic}. Día: {day_name_for_reset}")

            # Llamar directamente a la función importada
            try:
                # Llama a la función importada desde services.database
                # Asegúrate que la función reset_today_routine_status esté importada arriba
                success_reset = reset_today_routine_status(user_id_for_logic)
                # Si tu función necesita 'day_name', pásalo:
                # success_reset = reset_today_routine_status(user_id_for_logic, day_name=day_name_for_reset)

            except Exception as db_error:
                 # Captura cualquier error durante la llamada a la función de BD
                 # Usa exc_info=True para loggear el traceback completo
                 logger.error(f"Error llamando a reset_today_routine_status para {user_id_for_logic}: {db_error}", exc_info=True)
                 success_reset = False

            if success_reset:
                 logger.info(f"Rutina de hoy reiniciada para {user_id_for_logic}")
                 return JSONResponse(content={
                     "success": True,
                     "message": "Estado de la rutina de hoy reiniciado correctamente."
                 })
            else:
                 logger.error(f"Fallo al reiniciar rutina de hoy para {user_id_for_logic}")
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al reiniciar el estado de la rutina en la base de datos.")
        # <<< FIN CORRECCIÓN: Llamada a función real >>>

        # --- Si NO es RESET_ROUTINE, continúa con la lógica normal de IA ---
        logger.info(f"Procesando registro normal para usuario {user_id_for_logic}")
        cleaned_text = clean_input(exercise_data)
        # logger.debug(f"Texto limpiado: {cleaned_text}") # Debug si es necesario

        formatted_json = format_for_postgres(cleaned_text) # Llamada a la función corregida
        # logger.debug(f"JSON formateado por IA: {formatted_json}") # Debug si es necesario

        if formatted_json is None:
            logger.error(f"Error en procesamiento de IA para usuario {user_id_for_logic}. Input: '{exercise_data}'")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo interpretar la descripción del entrenamiento. Intenta ser más específico, ej: 'Press Banca 3x10 80kg'"
            )

        success_insert = insert_into_db(formatted_json, user_id_for_logic)
        logger.info(f"Resultado de inserción para {user_id_for_logic}: {'Éxito' if success_insert else 'Fallo'}")

        if success_insert:
            return JSONResponse(content={
                "success": True,
                "message": "Entrenamiento procesado por IA y registrado correctamente."
            })
        else:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al registrar el entrenamiento en la base de datos.")

    except HTTPException as http_exc:
         # Re-lanzar excepciones HTTP para que FastAPI las maneje
         raise http_exc
    except Exception as e:
        # Capturar cualquier otra excepción inesperada
        logger.exception(f"Error inesperado en log_exercise_endpoint para {user_id_for_logic}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor al procesar la solicitud.")


# La ruta ahora es relativa al prefijo: /api/logs
@router.get("/logs", response_class=JSONResponse) # Ruta -> /api/logs
async def get_logs_endpoint(
    request: Request,
    days: int = Query(7, ge=1, description="Número de días hacia atrás para obtener logs."),
    user = Depends(get_current_user)
):
    if not user:
        logger.warning("Intento de obtener logs sin autenticación")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado.")

    user_id_for_logic = user.get('google_id')
    if not user_id_for_logic:
         logger.error(f"Usuario autenticado pero sin Google ID: {user}")
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ID de usuario inválido para obtener logs.")

    logger.info(f"Obteniendo logs para {user_id_for_logic}, {days} días.")

    try:
        logs = get_exercise_logs(user_id_for_logic, days)

        if logs is None:
            # Esto indica un error en la función de BD, no necesariamente que no haya logs
            logger.error(f"La función get_exercise_logs devolvió None para usuario {user_id_for_logic}.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al consultar los logs de entrenamiento.")

        logger.info(f"Logs obtenidos ({len(logs)} registros) exitosamente para usuario {user_id_for_logic}")
        # Devuelve la lista de logs directamente (puede ser vacía si no hay registros)
        return JSONResponse(content={
            "success": True,
            "logs": logs
        })

    except Exception as e:
        logger.exception(f"Error inesperado al obtener logs para {user_id_for_logic}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor al obtener logs.")