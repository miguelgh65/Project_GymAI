# back_end/gym/middlewares.py

import os
import logging
from typing import Optional, List, Callable, Dict, Any, Union
import json

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse  # ¡AQUÍ ESTÁ LA CORRECCIÓN!
from starlette.middleware.base import BaseHTTPMiddleware

# NO importar verify_token aquí para evitar el error circular
# from .services.jwt_service import verify_token

logger = logging.getLogger(__name__)

# Rutas públicas que no requieren autenticación
PUBLIC_PATHS = [
    "/login",        # Página de login
    "/docs",         # Swagger UI
    "/redoc",        # ReDoc
    "/openapi.json", # Esquema OpenAPI
    "/api/auth/google/verify", # Endpoint para verificación de Google
    "/static/",      # Archivos estáticos
    "/favicon.ico",  # Favicon
    "/api/verify-link-code", # Verificación de código para vincular Telegram
    "/fitbit-callback", # Callback de Fitbit OAuth
    "/google-callback", # Callback de Google OAuth
    # Rutas para el bot de Telegram
    "/api/logs",
    "/api/rutina",
    "/api/rutina_hoy",
    "/api/log-exercise",
]
def validate_telegram_token(request: Request):
    telegram_token = request.headers.get("X-Telegram-Bot-Token")
    expected_token = os.getenv("TELEGRAM_BOT_API_TOKEN")
    
    if telegram_token and telegram_token == expected_token:
        # Si el token coincide, considéralo como una solicitud válida del bot
        return {
            "id": -1,  # ID especial para bot
            "is_telegram_bot": True  # Añadí is_telegram_bot en lugar de telegram_bot para consistencia
        }
    return None

# Token secreto para autenticar solicitudes desde el bot de Telegram
TELEGRAM_BOT_API_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para verificar autenticación del usuario en cada solicitud."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa cada solicitud verificando la autenticación del usuario."""
        path = request.url.path
        
        # Verificar si la ruta es pública
        is_public_path = any(path.startswith(public_path) for public_path in PUBLIC_PATHS)
        
        if is_public_path:
            logger.info(f"✅ Path '{path}' es público y no requiere autenticación.")
            response = await call_next(request)
            logger.info(f"⬅️ Response Status: {response.status_code} for '{path}'")
            return response
        
        # Verificar token JWT del header Authorization
        auth_header = request.headers.get("Authorization")
        user_id = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            logger.info(f"🔑 Token JWT encontrado en header")
            
            # Verificar token y extraer user_id
            try:
                # Importar aquí para evitar la importación circular
                from .services.jwt_service import verify_token
                payload = verify_token(token)
                if payload:
                    user_id = payload.get("sub")
                    logger.info(f"✅ Token JWT válido para usuario ID: {user_id}")
            except ImportError as e:
                logger.error(f"Error importando verify_token: {e}")
        
        if not user_id:
            logger.warning(f"🚦 DECISIÓN: Path '{path}' NO público y SIN token JWT válido. Redirigiendo a /login.")
            redirect_path = f"/login?redirect_url={request.url.path}"
            logger.info(f"🔀 Redirigiendo a: {redirect_path}")
            return RedirectResponse(url=redirect_path, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        
        # Usuario autenticado, continuar con la solicitud
        # Añadir user_id al estado de la solicitud para usarlo en las dependencias
        request.state.user_id = user_id
        response = await call_next(request)
        logger.info(f"⬅️ Response Status: {response.status_code} for '{path}'")
        return response

async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    # Verificar si es una solicitud del bot de Telegram
    telegram_token = request.headers.get("X-Telegram-Bot-Token")
    expected_telegram_token = os.getenv("TELEGRAM_BOT_API_TOKEN")
    
    logger.info(f"Token recibido: {telegram_token}")
    logger.info(f"Token esperado: {expected_telegram_token}")
    
    if telegram_token and telegram_token == expected_telegram_token:
        logger.info("✅ Autenticación con token de Telegram exitosa")
        return {
            "id": -1,  # ID especial para bot
            "google_id": None,
            "display_name": "Telegram Bot",
            "is_telegram_bot": True,
            "email": "telegram_bot@system.local"
        }
    
    # Resto de la lógica de autenticación...

    # Primero intentar obtener user_id del estado (establecido por el middleware)
    user_id = getattr(request.state, "user_id", None)

    # Si no está en el estado, intentar extraerlo del token
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                # Importar aquí para evitar la importación circular
                from .services.jwt_service import verify_token
                payload = verify_token(token)
                if payload:
                    user_id = payload.get("sub")
            except ImportError as e:
                logger.error(f"Error importando verify_token: {e}")

    if not user_id:
        logger.debug(f"❌ No se encontró token JWT válido o user_id en el estado de la petición.")
        return None

    try:
        # Importar get_user_by_id localmente para evitar importaciones circulares
        from .services.auth_service import get_user_by_id
        
        # Obtener usuario de la base de datos
        user = get_user_by_id(int(user_id))
        if user:
            logger.debug(f"✅ Usuario obtenido por ID {user_id}: {user.get('display_name', 'Unknown')}")
            return user
        else:
            logger.warning(f"⚠️ No se encontró usuario con ID {user_id} en la base de datos.")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Error al obtener usuario con ID {user_id}: {str(e)}")
        return None
    except Exception as e:
        logger.exception(f"❌ Error inesperado al obtener usuario: {str(e)}")
        return None