# back_end/gym/middlewares.py

import os
import logging
from typing import Optional, List, Callable, Dict, Any, Union
import json
# --- AÑADE/ASEGURA ESTAS IMPORTACIONES ---
from starlette.responses import RedirectResponse
from starlette import status
# --- FIN IMPORTACIONES ---
from fastapi import Request, Response # 'status' ya viene de starlette
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# NO importar verify_token globalmente para evitar importación circular

logger = logging.getLogger(__name__)

# Rutas públicas que no requieren autenticación
PUBLIC_PATHS = [
    "/login",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/auth/google/verify",
    "/static/",
    "/favicon.ico",
    "/api/verify-link-code",
    "/fitbit-callback", # Callback de Fitbit OAuth
    "/google-callback", # Callback de Google OAuth (si lo usas)
    # CONSIDERAR: Las rutas del bot quizás no deberían ser públicas si necesitan un usuario vinculado.
    # Podrían necesitar el header X-Telegram-Bot-Token o un JWT válido.
]
# Token secreto para autenticar solicitudes desde el bot de Telegram
TELEGRAM_BOT_API_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para verificar autenticación."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa cada solicitud verificando la autenticación."""
        path = request.url.path
        logger.debug(f"Middleware dispatch: Procesando path '{path}'")

        # 1. Verificar si la ruta es pública
        is_public_path = any(path.startswith(public_path) for public_path in PUBLIC_PATHS)
        if is_public_path:
            logger.info(f"✅ Path '{path}' es público.")
            return await call_next(request) # Continuar sin autenticar

        # 2. Si no es pública, verificar autenticación (Bot o JWT)
        user_info = None # Para guardar la info del usuario autenticado

        # 2.1. ¿Es el Bot de Telegram?
        telegram_token = request.headers.get("X-Telegram-Bot-Token")
        expected_telegram_token = TELEGRAM_BOT_API_TOKEN
        if telegram_token and expected_telegram_token and telegram_token == expected_telegram_token:
            logger.info(f"✅ Path '{path}' autenticado vía Telegram Bot Token.")
            user_info = {"id": -1, "is_telegram_bot": True, "display_name": "Telegram Bot"}

        # 2.2. Si no es el Bot, ¿es un usuario con JWT?
        elif not user_info: # Solo verificar JWT si no fue el bot
            auth_header = request.headers.get("Authorization")
            logger.debug(f"  Revisando Authorization Header para '{path}': {'Presente' if auth_header else 'Ausente'}")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                try:
                    from .services.jwt_service import verify_token # Importación local
                    payload = verify_token(token)
                    if payload:
                        user_id = payload.get("sub")
                        if user_id:
                            logger.info(f"✅ Path '{path}' autenticado vía JWT para user ID: {user_id}")
                            # Guardamos solo el ID por ahora, get_current_user buscará detalles si es necesario
                            user_info = {"id": user_id, "is_telegram_bot": False} # Marcamos como NO bot
                        else:
                             logger.warning(f"⚠️ Token JWT válido pero sin 'sub' (user_id) para path '{path}'.")
                    else:
                        logger.warning(f"⚠️ Token JWT encontrado pero inválido/expirado para path '{path}'.")
                except ImportError as e:
                    logger.error(f"Error crítico importando verify_token: {e}")
                except Exception as e_verify:
                    logger.error(f"Error durante verify_token: {e_verify}", exc_info=True)

        # 3. Decisión: Redirigir o Continuar
        if user_info:
            # Usuario autenticado (Bot o JWT)! Guardar info en el estado y continuar.
            request.state.user_info = user_info # Guardamos la info básica
            logger.debug(f"➡️ Usuario ID {user_info.get('id')} autenticado. Procediendo a la ruta '{path}'.")
            return await call_next(request)
        else:
            # NO AUTENTICADO para una ruta NO PÚBLICA
            logger.warning(f"🚦 Path '{path}' requiere autenticación pero NO se encontró token válido (JWT o Bot). Redirigiendo a /login.")
            # Construir URL de redirección
            redirect_path = f"/login"
            # Añadir la URL original para que pueda volver después de loguearse
            # Evitar añadir el propio /login como redirect_url
            if path != "/login":
                 # Asegurar que los query params también se pasen si son necesarios
                 # Ejemplo simple: solo el path. Podría necesitar urlencode completo.
                 current_url_encoded = request.url.path # urlencode(path) si tiene caracteres especiales
                 redirect_path += f"?redirect_url={current_url_encoded}"

            logger.info(f"🔀 Redirigiendo a: {redirect_path}")
            # No necesitas importar RedirectResponse aquí si ya está al inicio del archivo
            return RedirectResponse(url=redirect_path, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# Función Dependency para obtener detalles del usuario (AJUSTADA)
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Obtiene los detalles completos del usuario autenticado.
    Se basa en la información básica (`user_info`) puesta en `request.state` por el middleware.
    """
    user_info = getattr(request.state, "user_info", None)

    if not user_info:
        logger.debug("get_current_user: No se encontró user_info en request.state.")
        return None # No autenticado según el middleware

    user_id = user_info.get("id")
    is_bot = user_info.get("is_telegram_bot", False)

    if is_bot:
        logger.debug("get_current_user: Es el bot de Telegram.")
        # Devolver el objeto simulado para el bot
        return {"id": -1, "is_telegram_bot": True, "display_name": "Telegram Bot"}
    elif user_id:
        # Es un usuario normal autenticado por JWT, buscar detalles en BD
        logger.debug(f"get_current_user: Buscando detalles para user ID: {user_id}")
        try:
            from .services.auth_service import get_user_by_id # Importación local
            # El ID del JWT ('sub') es un string, convertir a int para buscar en BD
            user_details = get_user_by_id(int(user_id))
            if user_details:
                logger.debug(f"get_current_user: Detalles encontrados para ID {user_id}: {user_details.get('display_name')}")
                user_details["is_telegram_bot"] = False # Asegurar que no es el bot
                return user_details
            else:
                logger.warning(f"get_current_user: Token JWT válido para ID {user_id}, pero usuario no encontrado en BD.")
                return None # Podría ser un usuario eliminado después de emitir el token
        except (ValueError, TypeError) as e:
            logger.error(f"get_current_user: Error convirtiendo user_id '{user_id}' a int: {e}")
            return None
        except ImportError as e:
             logger.error(f"get_current_user: Error importando get_user_by_id: {e}")
             return None
        except Exception as e:
            logger.exception(f"get_current_user: Error inesperado al obtener usuario ID {user_id}: {e}")
            return None
    else:
        # Caso inesperado: user_info existe pero sin id y no es bot?
        logger.error("get_current_user: Estado de usuario inválido en request.state.")
        return None