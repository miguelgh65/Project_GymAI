import os
import json
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, Form, HTTPException, Query, Request, Response, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse

# Importar dependencia y servicios (Asegúrate que las rutas sean correctas)
from back_end.gym.middlewares import get_current_user # Ajusta si es necesario
try:
    from services.auth_service import (
        generate_link_code,
        get_or_create_user,
        get_user_by_email,
        get_user_by_id,
        get_user_id_by_google,
        get_user_id_by_telegram, # Necesario para devolver has_telegram
        migrate_user_data,
        verify_google_token,
        verify_link_code
    )
except ImportError as e:
    logging.critical(f"Error Crítico de importación en auth.py: {e}. ¡Las funciones de Auth no estarán disponibles!")
    raise e

# Cargar variables de entorno
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
if not GOOGLE_CLIENT_ID:
    logging.warning("La variable de entorno GOOGLE_CLIENT_ID no está configurada.")

# Router con prefijo /api
router = APIRouter(prefix="/api", tags=["authentication"]) # Asume que el router se define aquí
logger = logging.getLogger(__name__)

# --- Rutas API ---

# Ruta: /api/generate-link-code
@router.post("/generate-link-code", response_class=JSONResponse)
async def generate_link_code_route(request: Request, user: dict = Depends(get_current_user)): # Usar dependencia
    """Genera un código para vincular una cuenta de Telegram (Requiere Login)."""
    if not user:
        logger.warning("Intento de generar código de enlace sin autenticación.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id_internal = user.get("id")
    if not user_id_internal: # Verificación adicional
         logger.error("Usuario autenticado pero sin ID interno en el objeto 'user'.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno de sesión.")

    logger.info(f"Solicitud para generar código de enlace para user_id interno: {user_id_internal}")

    try:
        code = generate_link_code(user_id_internal)
        if not code:
            logger.error(f"Error al generar código de enlace para user_id: {user_id_internal}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al generar código")

        logger.info(f"Código de enlace generado: {code} para user_id: {user_id_internal}")
        return JSONResponse(content={"success": True, "code": code})
    except Exception as e:
        logger.exception(f"Error inesperado en generate_link_code_route para user_id {user_id_internal}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")


# Ruta: /api/verify-link-code (Usada por el bot de Telegram, no necesita cookie)
@router.post("/verify-link-code", response_class=JSONResponse)
async def verify_link_code_route(request: Request):
    """Verifica un código de vinculación desde el bot de Telegram."""
    logger.info("Recibida solicitud para verificar código de enlace desde Bot.")
    try:
        data = await request.json()
        code = data.get("code")
        telegram_id = data.get("telegram_id")
        logger.debug(f"Verificando código: {code} para Telegram ID: {telegram_id}")

        if not code or not telegram_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Faltan parámetros requeridos (code, telegram_id)")

        success = verify_link_code(code, str(telegram_id)) # Asegurar que telegram_id es string
        if success:
            logger.info(f"Código '{code}' verificado con éxito para Telegram ID: {telegram_id}")
            return JSONResponse(content={"success": True, "message": "Cuentas vinculadas correctamente"})
        else:
            logger.warning(f"Código '{code}' inválido o expirado para Telegram ID: {telegram_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido o expirado")

    except json.JSONDecodeError:
        logger.warning("Error al decodificar JSON en /api/verify-link-code")
        raise HTTPException(status_code=400, detail="JSON inválido.")
    except HTTPException as http_exc:
        raise http_exc # Re-lanzar excepciones HTTP conocidas
    except Exception as e:
        logger.exception(f"Error inesperado en verify_link_code_route: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Ruta: /api/auth/google/verify (Usada por el frontend Login.js)
@router.post("/auth/google/verify", response_class=JSONResponse)
async def verify_google_signin(request: Request, response: Response):
    """
    Verifica el token de Google Sign-In, crea/actualiza usuario,
    establece cookie y devuelve datos básicos del usuario.
    """
    logger.info("Recibida solicitud para verificar token de Google.")
    try:
        data = await request.json()
        token = data.get("id_token")

        if not token: raise HTTPException(status_code=400, detail="Token no proporcionado")
        if not GOOGLE_CLIENT_ID: raise HTTPException(status_code=500, detail="Error configuración servidor (Client ID Google no configurado).")

        user_info = verify_google_token(token)
        if not user_info: raise HTTPException(status_code=400, detail="Token de Google inválido o expirado")

        google_id = user_info.get("sub")
        email = user_info.get("email")
        display_name = user_info.get("name")
        profile_picture = user_info.get("picture")

        if not google_id: # El 'sub' (subject) es esencial
             logger.error(f"Token de Google verificado pero falta 'sub' (Google ID). UserInfo: {user_info}")
             raise HTTPException(status_code=400, detail="Token de Google inválido (falta ID).")

        logger.info(f"Obteniendo o creando usuario para Google ID: {google_id}, Email: {email}")
        # get_or_create_user debe devolver el ID INTERNO del usuario.
        user_id_internal = get_or_create_user(
            google_id=google_id,
            email=email,
            display_name=display_name,
            profile_picture=profile_picture
        )
        logger.info(f"ID de usuario interno obtenido/creado: {user_id_internal}")

        if not user_id_internal:
             logger.error(f"get_or_create_user devolvió None o 0 para Google ID {google_id}")
             raise HTTPException(status_code=500, detail="Error al crear o actualizar el usuario en la base de datos")

        # --- INICIO: Preparar datos de usuario para devolver ---
        # Intenta obtener el estado de vinculación de Telegram (puede devolver None)
        # Es crucial que get_user_id_by_telegram maneje el user_id_internal como input
        # y devuelva algo interpretable (ej. el ID de telegram si existe, None si no).
        # Asumiendo que get_user_by_id puede obtener el telegram_id:
        # user_details = get_user_by_id(user_id_internal) # Obtener detalles completos
        # has_telegram_linked = user_details.get("telegram_id") is not None if user_details else False

        # Alternativa: Llamar a get_user_id_by_telegram si está adaptada
        # Nota: get_user_id_by_telegram originalmente buscaba por telegram_id, necesita adaptarse
        # o usar get_user_by_id como arriba. Por simplicidad, asumimos get_user_by_id:
        temp_user_details = get_user_by_id(user_id_internal)
        has_telegram_linked = temp_user_details.get("telegram_id") is not None if temp_user_details else False


        user_data_for_frontend = {
             "id": user_id_internal,
             "display_name": display_name, # Obtenido de Google
             "email": email,               # Obtenido de Google
             "profile_picture": profile_picture, # Obtenido de Google
             "has_telegram": has_telegram_linked, # Obtenido de nuestra BD
             "has_google": True # Acaba de autenticarse con Google
        }
        logger.info(f"Preparados datos para frontend: {user_data_for_frontend}")
        # --- FIN: Preparar datos de usuario ---

        # --- Lógica de Cookie (Sin cambios) ---
        cookie_max_age = 86400 * 30 # 30 días en segundos
        cookie_key = "user_id"
        cookie_value = str(user_id_internal)
        is_secure_env = request.url.scheme == "https"
        cookie_samesite = "lax"
        cookie_secure = is_secure_env
        logger.info(f"Configurando cookie: key={cookie_key}, value={cookie_value}, httponly={True}, secure={cookie_secure}, samesite='{cookie_samesite}', max_age={cookie_max_age}, path='/'")
        response.set_cookie(
            key=cookie_key,
            value=cookie_value,
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=cookie_max_age,
            path="/"
        )
        logger.info(f"Cookie '{cookie_key}={cookie_value}' configurada para ser enviada en la respuesta.")
        # --- Fin Lógica de Cookie ---

        # --- Devolver éxito Y los datos del usuario ---
        return JSONResponse(
            content={
                "success": True,
                "user": user_data_for_frontend, # <<< DATOS DEL USUARIO INCLUIDOS
                "message": "Autenticación exitosa",
                "redirect": "/" # Sugerencia para frontend
            }
        )

    except json.JSONDecodeError:
        logger.warning("Error al decodificar JSON en /api/auth/google/verify")
        raise HTTPException(status_code=400, detail="JSON inválido.")
    except HTTPException as http_exc:
        logger.warning(f"HTTPException en verify_google_signin: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado en verify_google_signin: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor durante la autenticación.")

# Aquí irían las otras funciones del router de autenticación...
# como logout, get_current_user_api, generate_link_code, etc.

# Ruta: /api/logout
@router.get("/logout", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def logout(request: Request, response: Response):
    """Cierra la sesión eliminando la cookie y redirigiendo a /login."""
    user_id_from_cookie = request.cookies.get("user_id")
    logger.info(f"Recibida solicitud de logout para usuario (cookie detectada: {user_id_from_cookie or 'Ninguna'})")

    redirect_url = "/login?logout=success" # URL a la que redirige el backend

    # Crear respuesta de redirección
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # Eliminar la cookie
    logger.info(f"Intentando eliminar cookie 'user_id'...")
    response.delete_cookie(
        key="user_id",
        path="/",
        httponly=True,
        secure= request.url.scheme == "https", # Debe coincidir con cómo se creó
        samesite="lax" # Debe coincidir con cómo se creó
    )
    logger.info(f"Cookie 'user_id' marcada para eliminación en la respuesta.")

    # Cabeceras anti-caché para la respuesta de redirección
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# Ruta: /api/current-user
@router.get("/current-user", response_class=JSONResponse)
async def get_current_user_api(request: Request, user: dict = Depends(get_current_user)): # Usa la dependencia
    """Obtiene la información del usuario autenticado por cookie."""
    logger.info(f"Solicitud a /api/current-user...") # Log inicial

    if not user:
        # Este caso debería ser manejado por el middleware si la ruta es privada.
        # Si llega aquí, podría indicar un problema en la lógica del middleware o la ruta se marcó pública.
        logger.warning("Acceso a /api/current-user SIN usuario autenticado (middleware no redirigió?).")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay sesión activa o la sesión es inválida."
        )

    # Devolver información segura del usuario (filtrando datos sensibles si los hubiera)
    safe_user_info = {
        "id": user.get("id"),
        "display_name": user.get("display_name"),
        "email": user.get("email"),
        "profile_picture": user.get("profile_picture"),
        "has_telegram": user.get("telegram_id") is not None,
        "has_google": user.get("google_id") is not None,
        # Añadir más campos si son necesarios y seguros para el frontend
    }
    logger.info(f"Devolviendo información para usuario ID={user.get('id')}")
    return JSONResponse(content={"success": True, "user": safe_user_info})


# Ruta: /api/link-telegram (Requiere estar logueado via web)
@router.post("/link-telegram", response_class=JSONResponse)
async def link_telegram_account(
    request: Request,
    telegram_id: str = Form(...),
    user = Depends(get_current_user) # Requiere login web previo
):
    """(Requiere Login Web) Vincula una cuenta de Telegram a la cuenta web actual."""
    if not user: raise HTTPException(status_code=401, detail="Usuario no autenticado")

    user_id_internal = user.get("id")
    if not user_id_internal: # Verificación adicional
         logger.error("Usuario autenticado pero sin ID interno en el objeto 'user'.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno de sesión.")

    logger.info(f"Usuario autenticado ID: {user_id_internal}. Intentando vincular Telegram ID: {telegram_id}")

    try:
        # Verificar si el telegram_id ya existe y pertenece a OTRO usuario
        existing_user_id = get_user_id_by_telegram(str(telegram_id))
        if existing_user_id and existing_user_id != user_id_internal:
             logger.warning(f"Telegram ID {telegram_id} ya está vinculado al usuario interno ID {existing_user_id}. Se intentará migrar datos a usuario actual ID {user_id_internal}.")
             # Aquí iría la lógica de migración de datos si es necesaria
             # Por ejemplo: migrate_user_data(telegram_id, user_id_internal)
             # ¡¡Implementar migrate_user_data si es necesario!!
             # if not migrate_user_data(str(telegram_id), user_id_internal):
             #      raise HTTPException(status_code=500, detail="Error crítico al migrar datos de Telegram.")
             logger.info(f"Migración de datos para Telegram ID {telegram_id} completada (o no implementada).")

        # Actualizar el usuario actual añadiendo/sobrescribiendo el telegram_id
        # Usamos get_or_create_user que debería manejar la actualización si encuentra el internal_id
        # Necesita modificarse get_or_create_user para buscar PRIMERO por internal_id si se proporciona.
        # ---- INICIO: Lógica Asumida para Actualizar Usuario ----
        # Esto requiere que get_or_create_user sea adaptado o crear una función específica `update_user_telegram_id`
        conn = None
        cur = None
        try:
             conn = psycopg2.connect(**DB_CONFIG)
             cur = conn.cursor()
             cur.execute("UPDATE users SET telegram_id = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                         (str(telegram_id), user_id_internal))
             conn.commit()
             updated_rows = cur.rowcount
             cur.close()
             conn.close()
             if updated_rows == 0:
                  logger.error(f"No se encontró el usuario con ID interno {user_id_internal} para actualizar Telegram ID.")
                  raise HTTPException(status_code=404, detail="Usuario no encontrado para vincular.")
             logger.info(f"Telegram ID {telegram_id} vinculado/actualizado para usuario {user_id_internal}.")
             return JSONResponse(content={"success": True, "message": "Cuenta de Telegram vinculada correctamente."})
        except psycopg2.Error as db_err:
            logger.error(f"Error DB al vincular Telegram ID {telegram_id} a usuario {user_id_internal}: {db_err}")
            if conn: conn.rollback()
            raise HTTPException(status_code=500, detail="Error de base de datos al vincular Telegram.")
        finally:
            if cur: cur.close()
            if conn: conn.close()
        # ---- FIN: Lógica Asumida ----

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado en link_telegram_account para usuario {user_id_internal}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al vincular cuenta.")