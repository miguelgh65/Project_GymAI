# Archivo: back_end/gym/routes/fitbit/callbacks.py
import logging
from urllib.parse import urlencode
from fastapi import APIRouter, Query, Request, status
from fastapi.responses import RedirectResponse

from ...services.fitbit.auth_service import FitbitAuthService
from ...repositories.fitbit_repository import FitbitRepository

# Configuración de logging
logger = logging.getLogger(__name__)

# Router para callbacks de OAuth
router = APIRouter(
    prefix="/api/fitbit", 
    tags=["fitbit_callbacks"],
)

# URLs del Frontend
FRONTEND_APP_URL = "http://localhost"  # Ajustar según configuración
FRONTEND_FITBIT_SUCCESS_PATH = "/profile?fitbit_status=success"
FRONTEND_FITBIT_ERROR_PATH = "/profile?fitbit_status=error"

@router.get('/callback', name="fitbit_callback")
async def fitbit_callback_handler(
    request: Request, 
    code: str = Query(None), 
    state: str = Query(None), 
    error: str = Query(None)
):
    """Callback de Fitbit. Valida estado, intercambia código, guarda tokens y redirige al frontend."""
    # Logging detallado
    logger.info("🔒 Inicio de callback de Fitbit")
    logger.info(f"Parámetros recibidos:")
    logger.info(f"  - Código: {'Presente' if code else 'Ausente'}")
    logger.info(f"  - Estado: {state or 'N/A'}")
    logger.info(f"  - Error: {error or 'Ninguno'}")

    # Logging de cookies
    logger.info("🍪 Información de Cookies:")
    for cookie_name, cookie_value in request.cookies.items():
        logger.info(f"  - {cookie_name}: {cookie_value}")

    # Logging de headers (útil para debugging)
    logger.info("📋 Headers de la solicitud:")
    for header_name, header_value in request.headers.items():
        logger.info(f"  - {header_name}: {header_value}")

    # Extraer estado y usuario de las cookies
    expected_state = request.cookies.get('fitbit_oauth_state')
    user_id_pending = request.cookies.get('fitbit_user_id_pending')

    # Helper para redirigir al frontend
    def create_frontend_redirect(is_error=True, message=None):
        base_url = FRONTEND_APP_URL.rstrip('/')
        path = FRONTEND_FITBIT_ERROR_PATH if is_error else FRONTEND_FITBIT_SUCCESS_PATH
        final_url = f"{base_url}{path}"
        
        if message:
            separator = '&' if '?' in final_url else '?'
            final_url += f"{separator}{urlencode({'message': message})}"
        
        response = RedirectResponse(final_url, status_code=status.HTTP_303_SEE_OTHER)
        
        # Eliminar cookies de OAuth
        response.delete_cookie(
            key="fitbit_oauth_state", 
            path="/", 
            httponly=True, 
            samesite="lax",
            secure=request.url.scheme == "https"
        )
        response.delete_cookie(
            key="fitbit_user_id_pending", 
            path="/", 
            httponly=True, 
            samesite="lax",
            secure=request.url.scheme == "https"
        )
        
        logger.info(f"Redirigiendo a Frontend: {final_url}. Es error: {is_error}")
        return response

    # Validaciones exhaustivas
    if error:
        logger.warning(f"Fitbit devolvió un error explícito: {error}")
        return create_frontend_redirect(
            is_error=True, 
            message=f"Fitbit denegó acceso: {error}"
        )

    if not code:
        logger.error("No se recibió código de autorización de Fitbit")
        return create_frontend_redirect(
            is_error=True, 
            message="No se recibió código de autorización. Por favor, inténtalo de nuevo."
        )

    if not expected_state:
        logger.critical("Falta el estado CSRF en las cookies")
        return create_frontend_redirect(
            is_error=True, 
            message="Error de seguridad: estado de sesión inválido"
        )

    if not state or state != expected_state:
        logger.error(
            f"Error de validación CSRF. "
            f"Esperado: {expected_state[:10]}..., "
            f"Recibido: {state[:10]}..."
        )
        return create_frontend_redirect(
            is_error=True, 
            message="Error de seguridad. Por favor, inténtalo de nuevo."
        )

    if not user_id_pending:
        logger.critical("No se encontró ID de usuario pendiente")
        return create_frontend_redirect(
            is_error=True, 
            message="Error interno: no se pudo identificar al usuario"
        )

    # Intercambiar código por tokens
    try:
        tokens = FitbitAuthService.exchange_code_for_token(code)
        
        if not tokens:
            logger.error(f"Error al intercambiar código por tokens para usuario {user_id_pending}")
            return create_frontend_redirect(
                is_error=True, 
                message="Error al conectar con Fitbit. Por favor, inténtalo de nuevo."
            )
        
        # Guardar tokens en base de datos
        success = FitbitRepository.save_tokens(user_id_pending, tokens)
        
        if success:
            logger.info(f"Tokens de Fitbit guardados para usuario {user_id_pending}")
            return create_frontend_redirect(
                is_error=False, 
                message="¡Fitbit conectado exitosamente!"
            )
        else:
            logger.error(f"Error al guardar tokens para usuario {user_id_pending}")
            return create_frontend_redirect(
                is_error=True, 
                message="Error interno al guardar la conexión con Fitbit."
            )
    
    except Exception as e:
        logger.exception(f"Error inesperado en callback de Fitbit: {str(e)}")
        return create_frontend_redirect(
            is_error=True, 
            message="Error inesperado. Por favor, inténtalo de nuevo más tarde."
        )