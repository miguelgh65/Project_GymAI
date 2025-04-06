# Archivo: back_end/gym/middlewares.py

from fastapi import Depends, Request
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response

# --- Importaciones Corregidas ---
try:
    # Usar importación relativa (. significa desde el mismo directorio gym)
    from .services.auth_service import get_user_by_id, get_user_id_by_google, get_user_id_by_telegram
except ImportError as e:
    logging.error(f"Error importando servicios en middleware (relativa): {e}")
    # Define stubs si es absolutamente necesario para arrancar, pero es mejor arreglar imports
    def get_user_by_id(id): logging.error(f"STUB: get_user_by_id({id}) llamado"); return None
    def get_user_id_by_google(gid): return None
    def get_user_id_by_telegram(tid): return None
# --- Fin Importaciones Corregidas ---


# Asegúrate que el logger se configure en app_fastapi.py con nivel DEBUG
logger = logging.getLogger(__name__)

async def get_current_user(request: Request):
    """Dependencia para obtener el usuario autenticado."""
    return getattr(request.state, "user", None)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticación y gestión básica de sesión."""

    async def dispatch(self, request: Request, call_next):
        # --- LOGS DETALLADOS AQUÍ ---
        current_path = request.url.path
        method = request.method
        origin = request.headers.get('origin', 'N/A')
        raw_cookies = request.headers.get('cookie', 'N/A')

        logger.debug(f"--- 🪵 MIDDLEWARE REQ START 🪵 ---")
        logger.debug(f"➡️ Path: '{current_path}', Method: '{method}'")
        logger.debug(f"🌍 Origin Header: {origin}")
        logger.debug(f"🍪 Raw Cookie Header: {raw_cookies}")
        logger.debug(f"🍪 Parsed Cookies Dict: {dict(request.cookies)}")

        cookie_user_id = request.cookies.get("user_id")
        logger.info(f"❓ Extracted 'user_id' Cookie Value: '{cookie_user_id}'")

        public_paths = [
            '/docs', '/openapi.json', '/login',
            '/api/auth/google/verify', '/api/verify-link-code', '/favicon.ico',
        ]
        public_prefixes = ['/static/']

        is_public = current_path in public_paths or \
                    any(current_path.startswith(prefix) for prefix in public_prefixes)
        logger.debug(f"🧐 Path '{current_path}' es público: {is_public}")

        user = None
        user_id_to_use = None

        if cookie_user_id:
            logger.info(f"✅ Cookie 'user_id' ENCONTRADA: '{cookie_user_id}'")
            if cookie_user_id.isdigit():
                user_id_to_use = int(cookie_user_id)
                try:
                    logger.debug(f"🕵️ Intentando buscar usuario ID={user_id_to_use} en DB...")
                    # Asegúrate que get_user_by_id está correctamente importado arriba
                    user = get_user_by_id(user_id_to_use)
                    if user:
                        logger.info(f"👤✅ Usuario ID={user_id_to_use} ENCONTRADO en DB. Email: {user.get('email', 'N/A')}")
                        request.state.user = user
                    else:
                        logger.warning(f"👤❌ Usuario ID={user_id_to_use} NO encontrado en DB (cookie inválida o error DB?).")
                        request.state.user = None
                except Exception as e:
                    logger.error(f"💥 ERROR buscando usuario ID '{user_id_to_use}': {e}", exc_info=True)
                    request.state.user = None
            else:
                 logger.warning(f"⚠️ Cookie 'user_id={cookie_user_id}' no es un dígito válido.")
                 request.state.user = None
        else:
            logger.info(f"❌ Cookie 'user_id' NO encontrada en la petición.")
            request.state.user = None

        if not is_public and not user:
            logger.warning(f"🚦 DECISIÓN: Path '{current_path}' NO público y SIN usuario. Cookie leída: '{cookie_user_id}'. Redirigiendo a /login.")
            return RedirectResponse(url="/login?redirect_url=" + current_path, status_code=307)

        elif current_path == '/login' and user:
            logger.info(f"🚦 DECISIÓN: Path es /login pero usuario SÍ autenticado (ID: {user.get('id', 'N/A')}). Redirigiendo a /.")
            return RedirectResponse(url="/", status_code=307)

        else:
            user_status = f"Autenticado (ID: {user.get('id', 'N/A')})" if user else "No autenticado"
            logger.debug(f"🚦 DECISIÓN: Path '{current_path}' (Público: {is_public}, Usuario: {user_status}). Dejando pasar.")
            try:
                response = await call_next(request)
                logger.info(f"⬅️ Response Status: {response.status_code} for '{current_path}'")
                set_cookie_header = response.headers.get('set-cookie')
                allow_origin_header = response.headers.get('access-control-allow-origin')
                allow_creds_header = response.headers.get('access-control-allow-credentials')
                logger.debug(f"🍪 Response Set-Cookie Header (si existe): {set_cookie_header}")
                logger.debug(f"🌍 Response Access-Control-Allow-Origin: {allow_origin_header}")
                logger.debug(f"🔑 Response Access-Control-Allow-Credentials: {allow_creds_header}")
            except Exception as call_next_err:
                 logger.error(f"💥 ERROR durante call_next para '{current_path}': {call_next_err}", exc_info=True)
                 raise call_next_err

        logger.debug(f"--- 🪵 MIDDLEWARE REQ END 🪵 --- Path='{current_path}'. Finished.")
        return response