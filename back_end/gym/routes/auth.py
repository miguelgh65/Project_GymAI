# back_end/gym/routes/auth.py
import os
import json
import logging
import psycopg2 # Necesario si usas psycopg2 aquí directamente
from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, Form, HTTPException, Query, Request, Response, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse

# --- Importaciones Corregidas ---
# Usar importación relativa (..) para subir un nivel desde routes a gym
from ..middlewares import get_current_user
try:
    from ..services.auth_service import (
        generate_link_code,
        get_or_create_user,
        get_user_by_email,
        get_user_by_id,
        get_user_id_by_google,
        get_user_id_by_telegram,
        migrate_user_data,
        verify_google_token,
        verify_link_code
    )
    from ..config import DB_CONFIG # Importar DB_CONFIG desde gym
except ImportError as e:
    logging.critical(f"Error Crítico de importación en auth.py (relativa): {e}. ¡Auth no funcionará!")
    raise e
# --- Fin Importaciones Corregidas ---


# Cargar variables de entorno
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
if not GOOGLE_CLIENT_ID:
    logging.warning("La variable de entorno GOOGLE_CLIENT_ID no está configurada.")

# Router con prefijo /api
router = APIRouter(prefix="/api", tags=["authentication"])
logger = logging.getLogger(__name__)

# --- Rutas API ---

# Ruta: /api/generate-link-code
@router.post("/generate-link-code", response_class=JSONResponse)
async def generate_link_code_route(request: Request, user: dict = Depends(get_current_user)):
    """Genera un código para vincular una cuenta de Telegram (Requiere Login)."""
    if not user:
        logger.warning("Intento de generar código de enlace sin autenticación.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id_internal = user.get("id")
    if not user_id_internal:
         logger.error("Usuario autenticado pero sin ID interno en el objeto 'user'.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno de sesión.")

    logger.info(f"Solicitud para generar código de enlace para user_id interno: {user_id_internal}")

    try:
        # Asegúrate que generate_link_code está importado
        code = generate_link_code(user_id_internal)
        if not code:
            logger.error(f"Error al generar código de enlace para user_id: {user_id_internal}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al generar código")

        logger.info(f"Código de enlace generado: {code} para user_id: {user_id_internal}")
        return JSONResponse(content={"success": True, "code": code})
    except Exception as e:
        logger.exception(f"Error inesperado en generate_link_code_route para user_id {user_id_internal}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

# Ruta: /api/verify-link-code
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

        # Asegúrate que verify_link_code está importado
        success = verify_link_code(code, str(telegram_id))
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
        raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado en verify_link_code_route: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Ruta: /api/auth/google/verify
@router.post("/auth/google/verify", response_class=JSONResponse)
async def verify_google_signin(request: Request, response: Response):
    """Verifica token Google, crea/actualiza user, genera token JWT."""
    logger.info("Recibida solicitud para verificar token de Google.")
    try:
        # Log para ver el cuerpo completo de la solicitud
        body = await request.body()
        logger.info(f"Cuerpo de la solicitud (truncado): {body[:100]}...")
        
        data = await request.json()
        token = data.get("id_token")

        if not token:
            logger.warning("ID token no proporcionado en la solicitud")
            raise HTTPException(status_code=400, detail="Token no proporcionado")

        # Verificar que GOOGLE_CLIENT_ID está configurado
        if not GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID no está configurado en las variables de entorno")
            raise HTTPException(status_code=500, detail="Error configuración servidor (Client ID Google no configurado).")

        # Verificar token con Google
        logger.info(f"Llamando a verify_google_token con token de longitud {len(token)}")
        user_info = verify_google_token(token)
        
        if not user_info:
            logger.warning("verify_google_token devolvió None")
            raise HTTPException(status_code=400, detail="Token de Google inválido o expirado")

        google_id = user_info.get("sub")
        email = user_info.get("email")
        display_name = user_info.get("name")
        profile_picture = user_info.get("picture")

        if not google_id:
             logger.error(f"Token de Google verificado pero falta 'sub' (Google ID). UserInfo: {user_info}")
             raise HTTPException(status_code=400, detail="Token de Google inválido (falta ID).")

        logger.info(f"Obteniendo o creando usuario para Google ID: {google_id}, Email: {email}")
        
        # Crear o actualizar usuario
        user_id_internal = get_or_create_user(
            google_id=google_id, email=email, display_name=display_name, profile_picture=profile_picture
        )
        logger.info(f"ID de usuario interno obtenido/creado: {user_id_internal}")

        if not user_id_internal:
             logger.error(f"get_or_create_user devolvió None o 0 para Google ID {google_id}")
             raise HTTPException(status_code=500, detail="Error al crear o actualizar el usuario en la base de datos")

        # Obtener detalles completos del usuario
        temp_user_details = get_user_by_id(user_id_internal)
        has_telegram_linked = temp_user_details.get("telegram_id") is not None if temp_user_details else False

        # Crear objeto de usuario para el frontend
        user_data_for_frontend = {
             "id": user_id_internal, "display_name": display_name, "email": email,
             "profile_picture": profile_picture, "has_telegram": has_telegram_linked, "has_google": True
        }
        
        # Importar el servicio JWT
        from ..services.jwt_service import create_access_token
        
        # Crear token JWT
        jwt_data = {
            "sub": str(user_id_internal), # subject (user_id)
            "email": email,
            "name": display_name
        }
        
        access_token = create_access_token(jwt_data)
        if not access_token:
            logger.error(f"Error al crear token JWT para usuario {user_id_internal}")
            raise HTTPException(status_code=500, detail="Error al generar token de autenticación")
        
        logger.info(f"Token JWT generado para usuario {user_id_internal}")
        
        # Devolver el token JWT y los datos del usuario
        logger.info("Preparando respuesta final con token JWT y datos de usuario")
        return JSONResponse(
            content={ 
                "success": True, 
                "user": user_data_for_frontend,
                "access_token": access_token,
                "token_type": "bearer",
                "message": "Autenticación exitosa", 
                "redirect": "/" 
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

# Ruta: /api/logout
@router.get("/logout", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def logout(request: Request, response: Response):
    """Cierra la sesión eliminando la cookie y redirigiendo a /login."""
    user_id_from_cookie = request.cookies.get("user_id")
    logger.info(f"Recibida solicitud de logout para usuario (cookie detectada: {user_id_from_cookie or 'Ninguna'})")

    redirect_url = "/login?logout=success"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # --- Log Detallado ANTES de Delete-Cookie ---
    cookie_key_to_delete = "user_id"
    delete_path = "/"
    delete_secure = False # Para desarrollo
    delete_samesite = "lax"
    delete_httponly = True
    cookie_domain = None # No especificar dominio en desarrollo
    
    logger.info("--- 🍪🗑️ Preparando para eliminar Cookie 🗑️🍪 ---")
    logger.info(f"  Key: '{cookie_key_to_delete}', Path: '{delete_path}', HttpOnly: {delete_httponly}")
    logger.info(f"  Secure: {delete_secure} (False para desarrollo)")
    logger.info(f"  SameSite: '{delete_samesite}'")
    logger.info(f"  Domain: {cookie_domain}")
    logger.info("-----------------------------------------------")

    response.delete_cookie(
        key=cookie_key_to_delete, 
        path=delete_path, 
        httponly=delete_httponly,
        secure=delete_secure, 
        samesite=delete_samesite,
        # domain=cookie_domain  # No especificar dominio en desarrollo
    )
    logger.info(f"✅ Cookie '{cookie_key_to_delete}' marcada para eliminación en la respuesta.")

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

# Ruta: /api/current-user
@router.get("/current-user", response_class=JSONResponse)
async def get_current_user_api(request: Request, user: dict = Depends(get_current_user)):
    """Obtiene la información del usuario autenticado por token JWT."""
    logger.debug(f"--- 👤 Solicitud a /api/current-user ---")

    if not user:
        logger.warning("⚠️ Acceso a /api/current-user SIN usuario autenticado.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay sesión activa o la sesión es inválida."
        )

    safe_user_info = {
        "id": user.get("id"), "display_name": user.get("display_name"), "email": user.get("email"),
        "profile_picture": user.get("profile_picture"),
        "has_telegram": user.get("telegram_id") is not None, "has_google": user.get("google_id") is not None,
    }
    logger.info(f"✅ Devolviendo información para usuario ID={user.get('id')}")
    logger.debug(f"  User data: {safe_user_info}")
    return JSONResponse(content={"success": True, "user": safe_user_info})

# Ruta: /api/link-telegram
@router.post("/link-telegram", response_class=JSONResponse)
async def link_telegram_account(request: Request, telegram_id: str = Form(...), user = Depends(get_current_user)):
    """(Requiere Login Web) Vincula una cuenta de Telegram a la cuenta web actual."""
    if not user: raise HTTPException(status_code=401, detail="Usuario no autenticado")

    user_id_internal = user.get("id")
    if not user_id_internal:
         logger.error("Usuario autenticado pero sin ID interno en el objeto 'user'.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno de sesión.")

    logger.info(f"Usuario ID: {user_id_internal}. Vinculando Telegram ID: {telegram_id}")

    try:
        # Asegúrate que get_user_id_by_telegram está importado
        existing_user_id = get_user_id_by_telegram(str(telegram_id))
        if existing_user_id and existing_user_id != user_id_internal:
             logger.warning(f"Telegram ID {telegram_id} ya vinculado a user ID {existing_user_id}. Migrando a user ID {user_id_internal}.")
             # Lógica de migración (asegúrate que migrate_user_data existe si es necesaria)
             # if not migrate_user_data(str(telegram_id), user_id_internal):
             #      raise HTTPException(status_code=500, detail="Error crítico al migrar datos.")
             # logger.info(f"Migración de datos para Telegram ID {telegram_id} completada.")

        # Actualizar usuario actual (usando psycopg2 directamente)
        conn = None
        cur = None
        try:
             # Asegúrate que DB_CONFIG está importado
             conn = psycopg2.connect(**DB_CONFIG)
             cur = conn.cursor()
             cur.execute("UPDATE users SET telegram_id = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                         (str(telegram_id), user_id_internal))
             conn.commit()
             updated_rows = cur.rowcount
             if updated_rows == 0:
                  logger.error(f"No se encontró user ID {user_id_internal} para actualizar Telegram ID.")
                  raise HTTPException(status_code=404, detail="Usuario no encontrado para vincular.")
             logger.info(f"Telegram ID {telegram_id} vinculado/actualizado para user {user_id_internal}.")
             return JSONResponse(content={"success": True, "message": "Cuenta de Telegram vinculada."})
        except psycopg2.Error as db_err:
            logger.error(f"Error DB al vincular Telegram ID {telegram_id} a user {user_id_internal}: {db_err}")
            if conn: conn.rollback()
            raise HTTPException(status_code=500, detail="Error de base de datos al vincular.")
        finally:
            if cur: cur.close()
            if conn: conn.close()

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado en link_telegram_account para user {user_id_internal}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al vincular cuenta.")