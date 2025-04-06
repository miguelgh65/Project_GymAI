# Archivo: back_end/gym/middlewares.py

from fastapi import Depends, Request
# <<< Importar servicios y logging (si no está configurado globalmente) >>>
import logging
try:
    # Asegúrate que estas rutas de importación son correctas para tu estructura
    from services.auth_service import get_user_by_id, get_user_id_by_google, get_user_id_by_telegram
except ImportError as e:
    logging.error(f"Error importando servicios en middleware: {e}")
    # Define stubs si es absolutamente necesario para arrancar, pero es mejor arreglar imports
    def get_user_by_id(id): logging.error(f"STUB: get_user_by_id({id}) llamado"); return None
    def get_user_id_by_google(gid): return None
    def get_user_id_by_telegram(tid): return None

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response # Añadir Response

logger = logging.getLogger(__name__) # Usa el nombre del módulo como logger

async def get_current_user(request: Request):
    """Dependencia para obtener el usuario autenticado."""
    # logger.debug(f"Dependencia get_current_user llamada. request.state.user: {getattr(request.state, 'user', 'No establecido')}")
    return getattr(request.state, "user", None)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticación y gestión básica de sesión."""

    async def dispatch(self, request: Request, call_next):
        # Rutas que NO requieren autenticación para acceder
        public_paths = [
            '/docs', # Documentación Swagger/OpenAPI
            '/openapi.json',
            '/login', # Página/ruta de login del frontend (si es manejada por backend redirect)
            '/api/auth/google/verify', # Endpoint de verificación de Google
            '/api/verify-link-code', # Endpoint de verificación de Telegram
            '/favicon.ico',
            # '/api/logout', # Logout necesita saber quién eres (cookie) pero la acción es pública
            # '/api/generate-link-code', # Requiere login, por tanto NO es pública
            # '/api/current-user' # NO es pública
        ]
        # Prefijos públicos (para assets estáticos, etc.)
        public_prefixes = ['/static/']

        current_path = request.url.path
        # Usar nivel INFO para logs importantes del flujo
        logger.info(f"--- MIDDLEWARE REQ START --- Path='{current_path}', Method='{request.method}'")

        is_public = current_path in public_paths or \
                    any(current_path.startswith(prefix) for prefix in public_prefixes)
        logger.info(f"MIDDLEWARE CHECK: Path '{current_path}' es público: {is_public}")

        cookie_user_id = request.cookies.get("user_id")
        user = None
        user_id_to_use = None

        if cookie_user_id:
            # Loguea la cookie encontrada SIEMPRE que exista
            logger.info(f"MIDDLEWARE AUTH: Cookie 'user_id={cookie_user_id}' encontrada.")
            if cookie_user_id.isdigit():
                user_id_to_use = int(cookie_user_id)
                try:
                    logger.info(f"MIDDLEWARE AUTH: Intentando buscar usuario ID={user_id_to_use} en DB.")
                    user = get_user_by_id(user_id_to_use) # Llama a la función real
                    if user:
                        logger.info(f"MIDDLEWARE AUTH: Usuario ID={user_id_to_use} ENCONTRADO en DB. Email: {user.get('email', 'N/A')}")
                        request.state.user = user # Poner usuario en el estado para la dependencia
                    else:
                        # Este es un punto CRÍTICO si ocurre justo después del login
                        logger.warning(f"MIDDLEWARE AUTH: Usuario ID={user_id_to_use} NO encontrado en DB (cookie inválida o DB error?).")
                        request.state.user = None
                except Exception as e:
                    logger.error(f"MIDDLEWARE ERROR: Excepción buscando usuario ID '{user_id_to_use}': {e}", exc_info=True)
                    request.state.user = None
            else:
                 logger.warning(f"MIDDLEWARE AUTH: Cookie 'user_id={cookie_user_id}' encontrada pero no es un dígito válido.")
                 request.state.user = None
        else:
            logger.info(f"MIDDLEWARE AUTH: No se encontró cookie 'user_id' en la petición.")
            request.state.user = None

        # --- Lógica de Redirección/Acceso ---
        # 1. Si la ruta NO es pública Y NO hay usuario (user es None) -> Redirigir a Login
        if not is_public and not user:
            # Loguear con más detalle por qué se redirige
            logger.warning(f"MIDDLEWARE DECISION: Path '{current_path}' NO es público y NO hay usuario (user object is None). Cookie raw leída: '{cookie_user_id}'. Redirigiendo a /login.")
            # Redirigir a la página de login del frontend
            return RedirectResponse(url="/login?redirect_url=" + current_path, status_code=307) # 307 es común para redirects post-auth check

        # 2. Si la ruta ES /login PERO SÍ hay usuario -> Redirigir a Inicio
        elif current_path == '/login' and user:
            logger.info(f"MIDDLEWARE DECISION: Path es /login pero usuario SÍ está autenticado (ID: {user.get('id', 'N/A')}). Redirigiendo a /.")
            return RedirectResponse(url="/", status_code=307)

        # 3. En cualquier otro caso (ruta pública, o ruta privada con usuario) -> Continuar
        else:
            user_status = f"Autenticado (ID: {user.get('id', 'N/A')})" if user else "No autenticado"
            logger.info(f"MIDDLEWARE DECISION: Path '{current_path}' (Público: {is_public}, Usuario: {user_status}). Proceeding.")
            response = await call_next(request)
            logger.info(f"MIDDLEWARE ACTION: Response received for '{current_path}'. Status: {response.status_code}")

        logger.info(f"--- MIDDLEWARE REQ END --- Path='{current_path}'. Finished.")
        return response