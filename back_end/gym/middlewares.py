# back_end/gym/middlewares.py

import os
import logging
from typing import Optional, Dict, Any, Callable
import json

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse # Asegúrate que RedirectResponse está importado
from starlette.middleware.base import BaseHTTPMiddleware

# NO importar verify_token aquí para evitar el error circular
# from .services.jwt_service import verify_token

logger = logging.getLogger(__name__)

# Rutas públicas que no requieren autenticación
PUBLIC_PATHS = [
    "/login",        # Página de login (aunque React la maneje, la ruta puede existir)
    "/docs",         # Swagger UI
    "/redoc",        # ReDoc
    "/openapi.json", # Esquema OpenAPI
    "/api/auth/google/verify", # Endpoint para verificación de Google
    "/static/",      # Archivos estáticos (si los sirve FastAPI)
    "/favicon.ico",  # Favicon
    "/api/verify-link-code", # Verificación de código para vincular Telegram
    "/fitbit-callback", # Callback inicial de Fitbit OAuth (redirige a /api/fitbit/callback)
    "/api/fitbit/callback", # <<< AÑADIDO: Callback handler de Fitbit (procesa código y estado) >>>
    "/google-callback", # Callback de Google OAuth (si lo usas en backend)
    # Considera si estas rutas REALMENTE deben ser públicas o si el bot debe autenticarse con token
    # "/api/logs",
    # "/api/rutina",
    # "/api/rutina_hoy",
    # "/api/log-exercise", # La lógica actual ya maneja autenticación JWT o Bot Token
]

# Token secreto para autenticar solicitudes desde el bot de Telegram
TELEGRAM_BOT_API_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para verificar autenticación del usuario en cada solicitud."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa cada solicitud verificando la autenticación del usuario."""
        path = request.url.path

        # Simplificar chequeo de ruta pública
        is_public_path = any(
            path == public_path or (public_path.endswith('/') and path.startswith(public_path))
            for public_path in PUBLIC_PATHS
        )

        if is_public_path:
            logger.debug(f"✅ Path '{path}' es público. Continuando...")
            response = await call_next(request)
            # No loguear status aquí, puede ser prematuro si hay otras middlewares
            # logger.info(f"⬅️ Response Status (public): {response.status_code} for '{path}'")
            return response

        # --- Lógica de Autenticación ---
        user_authenticated = False
        user_id = None

        # 1. Intentar autenticación con Token de Bot Telegram
        telegram_token = request.headers.get("X-Telegram-Bot-Token")
        if TELEGRAM_BOT_API_TOKEN and telegram_token == TELEGRAM_BOT_API_TOKEN:
            logger.info(f"🤖 Autenticado como Bot de Telegram para path '{path}'")
            user_authenticated = True
            request.state.is_telegram_bot = True # Marcar como bot para get_current_user
            # No establecemos user_id aquí, get_current_user devolverá el objeto bot
        else:
            # 2. Intentar autenticación con Token JWT
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                try:
                    # Importar aquí para evitar la importación circular
                    from .services.jwt_service import verify_token
                    payload = verify_token(token)
                    if payload:
                        user_id = payload.get("sub")
                        if user_id:
                            user_authenticated = True
                            request.state.user_id = user_id # Guardar ID para get_current_user
                            logger.info(f"🔑 Token JWT válido para usuario ID: {user_id} en path '{path}'")
                        else:
                             logger.warning(f"Token JWT válido pero sin 'sub' (user_id) para path '{path}'")
                    else:
                         logger.warning(f"Token JWT inválido/expirado detectado para path '{path}'")
                except ImportError as e:
                    logger.error(f"Error importando verify_token en middleware: {e}")
                except Exception as e:
                    logger.error(f"Error verificando token JWT: {e}", exc_info=True) # Loguear error JWT

        # --- Decisión ---
        if user_authenticated:
            # Usuario autenticado (Bot o JWT), continuar con la solicitud
            logger.debug(f"✅ Usuario autenticado. Continuando request para '{path}'")
            response = await call_next(request)
            # logger.info(f"⬅️ Response Status (authenticated): {response.status_code} for '{path}'")
            return response
        else:
            # No autenticado y ruta no pública -> Redirigir a login
            logger.warning(f"🚦 Path '{path}' NO público y SIN autenticación válida. Redirigiendo a /login.")
            # Construir URL de redirección segura
            redirect_path = "/login"  # Usar una ruta directa en lugar de url_for
            # Añadir redirect_url como query param
            final_redirect_url = f"{redirect_path}?redirect_url={request.url.path}"

            logger.info(f"🔀 Redirigiendo a: {final_redirect_url}")
            return RedirectResponse(url=final_redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# Dependencia para obtener el usuario actual (Bot o Usuario Logueado)
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Obtiene el usuario actual. Puede ser el bot de Telegram (ID especial)
    o un usuario normal autenticado vía JWT.
    """
    # Verificar si el middleware marcó la solicitud como proveniente del bot
    is_bot = getattr(request.state, "is_telegram_bot", False)
    if is_bot:
        # Devolver un diccionario representando al bot
        return {
            "id": "TELEGRAM_BOT_SYSTEM_ID", # ID único y constante para el bot
            "google_id": None,
            "display_name": "Telegram Bot",
            "is_telegram_bot": True,
            "email": "telegram_bot@system.local"
        }

    # Si no es el bot, buscar el user_id establecido por el middleware (desde JWT)
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        logger.debug("get_current_user: No se encontró user_id en el estado de la petición.")
        return None # No hay usuario autenticado

    try:
        # Importar get_user_by_id localmente para evitar importaciones circulares
        from .services.auth_service import get_user_by_id

        # Obtener usuario de la base de datos
        user = get_user_by_id(int(user_id)) # Asume que user_id es numérico interno
        if user:
            # Añadir explícitamente is_telegram_bot = False para usuarios normales
            user["is_telegram_bot"] = False
            logger.debug(f"✅ Usuario obtenido por ID {user_id}: {user.get('display_name', 'Unknown')}")
            return user
        else:
            logger.warning(f"⚠️ get_current_user: No se encontró usuario con ID {user_id} en la base de datos.")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"❌ get_current_user: Error al convertir/usar ID {user_id}: {str(e)}")
        return None
    except ImportError as e:
         logger.error(f"❌ get_current_user: Error importando get_user_by_id: {e}")
         return None
    except Exception as e:
        logger.exception(f"❌ get_current_user: Error inesperado al obtener usuario ID {user_id}: {str(e)}")
        return None