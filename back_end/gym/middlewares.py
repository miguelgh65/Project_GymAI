# Archivo: back_end/gym/middlewares.py

from fastapi import Depends, Request
# <<< Importar servicios y logging (si no está configurado globalmente) >>>
import logging
try:
    from services.auth_service import get_user_by_id, get_user_id_by_google, get_user_id_by_telegram
except ImportError as e:
    logging.error(f"Error importando servicios en middleware: {e}")
    def get_user_by_id(id): return None
    def get_user_id_by_google(gid): return None
    def get_user_id_by_telegram(tid): return None

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response # Añadir Response

logger = logging.getLogger(__name__)

async def get_current_user(request: Request):
    """Dependencia para obtener el usuario autenticado."""
    # logger.debug(f"Dependencia get_current_user llamada. request.state.user: {getattr(request.state, 'user', 'No establecido')}")
    return getattr(request.state, "user", None)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticación y gestión básica de sesión."""

    async def dispatch(self, request: Request, call_next):
        # Rutas que NO requieren autenticación para acceder
        # Deben ser lo más específicas posible
        public_paths = [
            '/docs', # Documentación Swagger/OpenAPI
            '/openapi.json',
            '/login', # Página/ruta de login del frontend (si es manejada por backend redirect)
            '/api/auth/google/verify', # Endpoint de verificación de Google
            '/api/verify-link-code', # Endpoint de verificación de Telegram
            # '/api/generate-link-code', # ¿Debería ser pública o requerir login? Revisar. Asumamos privada por ahora.
            # '/api/logout', # El logout en sí es público, pero necesita la cookie para saber a quién desloguear
            '/favicon.ico',
            # '/api/current-user' # Esta NO debería ser pública, requiere saber quién eres
        ]
        # Prefijos públicos (para assets estáticos, etc.)
        public_prefixes = ['/static/'] # <<< CORRECCIÓN: Quitado '/api/' y '/auth/' >>>

        current_path = request.url.path
        logger.debug(f"\n--- MIDDLEWARE START ---")
        logger.debug(f"MIDDLEWARE REQ: Path='{current_path}', Method='{request.method}'")

        # Determinar si la ruta actual es pública
        is_public = current_path in public_paths or \
                    any(current_path.startswith(prefix) for prefix in public_prefixes)

        # Intentar obtener ID de usuario desde la cookie
        cookie_user_id = request.cookies.get("user_id")
        user = None
        user_id_to_use = None

        if cookie_user_id and cookie_user_id.isdigit():
            user_id_to_use = int(cookie_user_id)
            logger.debug(f"MIDDLEWARE AUTH: Cookie 'user_id={user_id_to_use}' encontrada.")
            try:
                user = get_user_by_id(user_id_to_use)
                if user:
                    logger.debug(f"MIDDLEWARE AUTH: Usuario ID={user_id_to_use} encontrado en DB.")
                    request.state.user = user # Poner usuario en el estado para la dependencia
                else:
                    logger.warning(f"MIDDLEWARE AUTH: Cookie user_id={user_id_to_use} inválida (no encontrado en DB).")
                    request.state.user = None
            except Exception as e:
                logger.error(f"MIDDLEWARE ERROR: Exception getting user by ID '{user_id_to_use}': {e}", exc_info=True)
                request.state.user = None
        else:
            logger.debug(f"MIDDLEWARE AUTH: No se encontró cookie 'user_id' válida.")
            request.state.user = None

        # --- Lógica de Redirección/Acceso ---
        # 1. Si la ruta NO es pública Y NO hay usuario -> Redirigir a Login
        if not is_public and not user:
            logger.info(f"MIDDLEWARE DECISION: Path '{current_path}' NO es público y NO hay usuario. Redirigiendo a /login.")
            # Importante: Asume que /login es manejado por el frontend.
            # Podrías necesitar devolver un 401 aquí si es una API pura.
            # Por ahora, mantenemos la redirección si es una app web tradicional.
            # Si tu frontend espera 401 para redirigir, cambia esto:
            # return Response(status_code=401, content="Unauthorized")
            return RedirectResponse(url="/login?redirect_url=" + current_path) # Redirige a la página de login

        # 2. Si la ruta ES /login PERO SÍ hay usuario -> Redirigir a Inicio
        elif current_path == '/login' and user:
            logger.info(f"MIDDLEWARE DECISION: Path es /login pero usuario SÍ está autenticado. Redirigiendo a /.")
            return RedirectResponse(url="/")

        # 3. En cualquier otro caso (ruta pública, o ruta privada con usuario) -> Continuar
        else:
            logger.debug(f"MIDDLEWARE DECISION: Path '{current_path}' es público o usuario está autenticado. Proceeding.")
            response = await call_next(request)
            logger.debug(f"MIDDLEWARE ACTION: Response received status: {response.status_code}")

        # <<< CORRECCIÓN: Eliminar el seteo de cookie redundante de aquí >>>
        # El cookie solo debe establecerse en el endpoint de login (/api/auth/google/verify)

        logger.debug(f"--- MIDDLEWARE END --- Request for {current_path} {request.method} finished.")
        return response