# Archivo: back_end/gym/routes/auth.py (Corregido con lógica condicional de cookie)

import os
import json
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, Form, HTTPException, Query, Request, Response, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse

# Importar dependencia y servicios (Asegúrate que las rutas sean correctas)
from back_end.gym.middlewares import get_current_user
try:
    from services.auth_service import (
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
except ImportError as e:
    logging.error(f"Error Crítico de importación en auth.py: {e}. ¡Las funciones de Auth no estarán disponibles!")
    # Puedes definir stubs aquí si necesitas que el servidor arranque SÍ o SÍ,
    # pero es mejor arreglar las importaciones.
    # Por ejemplo: def verify_google_token(token): return None
    raise e # Relanzar el error para que sea visible que algo falla al iniciar


# Cargar variables de entorno
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')

# Router con prefijo /api
router = APIRouter(prefix="/api", tags=["authentication"])
logger = logging.getLogger(__name__)

# --- Rutas API ---

# Ruta: /api/generate-link-code
@router.post("/generate-link-code", response_class=JSONResponse)
async def generate_link_code_route(request: Request, user: dict = Depends(get_current_user)): # Usar dependencia
    """Genera un código para vincular una cuenta de Telegram (Requiere Login)."""
    # La dependencia get_current_user maneja si el usuario está logueado o no
    if not user:
        logger.warning("Intento de generar código de enlace sin autenticación.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id_internal = user.get("id") # Obtener ID interno del usuario ya autenticado
    logger.info(f"Solicitud para generar código de enlace para user_id interno: {user_id_internal}")

    try:
        # Ya tenemos el usuario de la dependencia, no necesitamos buscarlo de nuevo por ID
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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Faltan parámetros requeridos")

        # verify_link_code debería actualizar el telegram_id en la tabla users
        # y asociarlo al user_id interno correcto basado en el código.
        success = verify_link_code(code, telegram_id)
        if success:
            logger.info(f"Código '{code}' verificado con éxito para Telegram ID: {telegram_id}")
            return JSONResponse(content={"success": True, "message": "Cuentas vinculadas correctamente"})
        else:
            logger.warning(f"Código '{code}' inválido o expirado para Telegram ID: {telegram_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido o expirado")

    except json.JSONDecodeError: raise HTTPException(status_code=400, detail="JSON inválido.")
    except HTTPException as http_exc: raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado en verify_link_code_route: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno")


# Ruta: /api/auth/google/verify (Usada por el frontend Login.js)
@router.post("/auth/google/verify", response_class=JSONResponse)
async def verify_google_signin(request: Request, response: Response):
    """Verifica el token de Google Sign-In y crea/actualiza el usuario."""
    logger.info("Recibida solicitud para verificar token de Google.")
    try:
        data = await request.json()
        token = data.get("id_token")
        # telegram_id = data.get("telegram_id") # Podría venir si se vincula durante el login

        if not token: raise HTTPException(status_code=400, detail="Token no proporcionado")
        if not GOOGLE_CLIENT_ID: raise HTTPException(status_code=500, detail="Error config servidor (Client ID).")

        user_info = verify_google_token(token)
        if not user_info: raise HTTPException(status_code=400, detail="Token inválido o expirado")

        google_id = user_info.get("sub")
        email = user_info.get("email")
        display_name = user_info.get("name")
        profile_picture = user_info.get("picture")

        logger.info(f"Obteniendo o creando usuario para Google ID: {google_id}, Email: {email}")
        # get_or_create_user ahora recibe todos los datos y maneja la lógica
        # de buscar por google_id, luego email, y crear o actualizar.
        # Debe devolver el ID INTERNO del usuario (ej: 1, 2, 3...).
        user_id_internal = get_or_create_user(
            google_id=google_id,
            # telegram_id=telegram_id, # Pasar si se soporta vinculación en login
            email=email,
            display_name=display_name,
            profile_picture=profile_picture
        )
        logger.info(f"ID de usuario interno obtenido/creado: {user_id_internal}")

        if not user_id_internal:
             raise HTTPException(status_code=500, detail="Error al crear/actualizar usuario")

        # --- INICIO: Lógica de Cookie Corregida ---
        cookie_max_age = 86400 * 30 # 30 días
        cookie_key = "user_id"
        cookie_value = str(user_id_internal)

        # Determinar atributos basados en el entorno
        is_secure_env = request.url.scheme == "https"
        # Por defecto, Lax es más seguro
        cookie_samesite = "lax"
        # Secure=True SOLO si la conexión es HTTPS
        cookie_secure = is_secure_env

        # NO aplicar workaround de samesite=none por ahora, mantener Lax.
        # Si Lax sigue fallando en HTTP localhost cross-port, la solución
        # es usar HTTPS local o configurar un proxy same-origin.
        # logger.warning(f"Usando cookie: secure={cookie_secure}, samesite='{cookie_samesite}'")


        logger.info(f"Configurando cookie: key={cookie_key}, value={cookie_value}, httponly=True, secure={cookie_secure}, samesite='{cookie_samesite}', max_age={cookie_max_age}, path='/'")

        response.set_cookie(
            key=cookie_key,
            value=cookie_value,
            httponly=True,           # ¡Importante para seguridad!
            secure=cookie_secure,    # True si es HTTPS
            samesite=cookie_samesite,# Usar Lax (o Strict si aplica)
            max_age=cookie_max_age,  # Tiempo de vida
            path="/"                 # Válida para todo el sitio
        )
        logger.info(f"Cookie '{cookie_key}={cookie_value}' establecida en la respuesta.")
        # --- FIN: Lógica de Cookie ---

        return JSONResponse(
            content={
                "success": True,
                "user_id": user_id_internal, # Devuelve el ID interno
                "message": "Autenticación exitosa",
                "redirect": "/" # Sugerencia para el frontend
            }
        )

    # ... (manejo de excepciones como antes) ...
    except json.JSONDecodeError: raise HTTPException(status_code=400, detail="JSON inválido.")
    except HTTPException as http_exc: raise http_exc
    except Exception as e:
        logger.exception(f"Error inesperado en verify_google_signin: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Ruta: /api/logout
@router.get("/logout", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def logout(request: Request, response: Response):
    """Cierra la sesión eliminando la cookie y redirigiendo a /login."""
    user_id = request.cookies.get("user_id")
    logger.info(f"Recibida solicitud de logout para usuario (cookie): {user_id}")

    redirect_url = "/login?logout=success" # Redirigir siempre a login

    # Crear respuesta y eliminar cookie (igual que antes)
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.delete_cookie(
        key="user_id",
        path="/",
        httponly=True,
        secure= request.url.scheme == "https",
        samesite="lax" # Coincidir con cómo se creó
    )
    logger.info(f"Cookie 'user_id' eliminada para usuario: {user_id}")

    # Cabeceras anti-caché (igual que antes)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# Ruta: /api/current-user
@router.get("/current-user", response_class=JSONResponse)
async def get_current_user_api(request: Request, user: dict = Depends(get_current_user)): # Usa la dependencia
    """Obtiene la información del usuario autenticado por cookie."""
    logger.info(f"Solicitud a /api/current-user. Usuario obtenido de dependencia: {'Sí' if user else 'No'}")

    if not user:
        # Si la ruta es privada, el middleware ya debería haber actuado.
        # Si llega aquí es porque la ruta se consideró pública o algo falló.
        logger.warning("Acceso a /api/current-user sin usuario autenticado.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No hay sesión activa")

    # Devolver información segura (igual que antes)
    safe_user_info = {
        "id": user.get("id"), "display_name": user.get("display_name"),
        "email": user.get("email"), "profile_picture": user.get("profile_picture"),
        "has_telegram": user.get("telegram_id") is not None,
        "has_google": user.get("google_id") is not None,
    }
    logger.info(f"Devolviendo información para usuario id={user.get('id')}")
    return JSONResponse(content={"success": True, "user": safe_user_info})


# Ruta: /api/link-telegram (Si es necesaria, requiere estar logueado)
@router.post("/link-telegram", response_class=JSONResponse)
async def link_telegram_account(
    request: Request,
    telegram_id: str = Form(...),
    user = Depends(get_current_user) # Requiere login web previo
):
    """Vincula una cuenta de Telegram a la cuenta web actual."""
    if not user: raise HTTPException(status_code=401, detail="Usuario no autenticado")

    user_id_internal = user.get("id")
    logger.info(f"Usuario autenticado ID: {user_id_internal}. Vinculando Telegram ID: {telegram_id}")

    try:
        # ... (lógica de verificación si telegram_id ya existe y migración como antes) ...
        existing_user_id = get_user_id_by_telegram(telegram_id)
        if existing_user_id and existing_user_id != user_id_internal:
             logger.warning(f"Telegram ID {telegram_id} ya vinculado a ID {existing_user_id}. Migrando a {user_id_internal}.")
             if not migrate_user_data(telegram_id, user_id_internal):
                  raise HTTPException(status_code=500, detail="Error al migrar datos.")
             logger.info("Migración completada.")

        # Actualizar usuario actual con telegram_id
        updated_user_id = get_or_create_user(
             # Pasa todos los datos conocidos para asegurar que se actualiza el correcto
             internal_id=user_id_internal, # Pasar ID interno para asegurar la actualización
             google_id=user.get("google_id"),
             telegram_id=telegram_id, # El ID a añadir/actualizar
             email=user.get("email"),
             display_name=user.get("display_name"),
             profile_picture=user.get("profile_picture")
        )
        # get_or_create_user debe poder buscar por internal_id y actualizar

        if not updated_user_id or updated_user_id != user_id_internal:
             logger.error(f"Discrepancia de ID al vincular telegram {telegram_id} a usuario {user_id_internal}. Devuelto: {updated_user_id}")
             raise HTTPException(status_code=500, detail="Error al actualizar usuario con Telegram ID")

        logger.info(f"Telegram ID {telegram_id} vinculado/actualizado para usuario {user_id_internal}.")
        return JSONResponse(content={"success": True, "message": "Cuenta de Telegram vinculada"})

    except Exception as e:
        logger.exception(f"Error inesperado en link_telegram_account para usuario {user_id_internal}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")