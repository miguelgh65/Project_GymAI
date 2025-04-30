# Archivo: back_end/gym/routes/fitbit/routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from ...middlewares import get_current_user
from ...services.fitbit.auth_service import FitbitAuthService
from ...services.fitbit.api_service import FitbitApiService
from ...repositories.fitbit_repository import FitbitRepository

# Configuración de logging
logger = logging.getLogger(__name__)

# Router para endpoints de Fitbit
router = APIRouter(
    prefix="/api/fitbit", 
    tags=["fitbit"],
)

@router.get('/connect-url', name="fitbit_connect_url")
async def get_fitbit_connect_url(request: Request, user = Depends(get_current_user)):
    """Devuelve la URL de conexión a Fitbit sin redirigir."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = str(user['id'])
    
    # Generar URL de autorización y estado CSRF
    auth_url, state = FitbitAuthService.generate_auth_url()
    
    # Preparar respuesta con URL de redirección
    response = JSONResponse(content={"success": True, "redirect_url": auth_url})
    
    # Configuración mejorada de cookies para CSRF
    secure = request.url.scheme == "https"
    response.set_cookie(
        key="fitbit_oauth_state", 
        value=state, 
        httponly=True, 
        secure=secure,
        samesite="lax" if not secure else "none",
        max_age=600,  # 10 minutos
        path="/"
    )
    response.set_cookie(
        key="fitbit_user_id_pending", 
        value=user_id, 
        httponly=True, 
        secure=secure,
        samesite="lax" if not secure else "none",
        max_age=600,  # 10 minutos
        path="/"
    )
    
    logger.info(f"Cookie de estado Fitbit configurada: {state[:10]}... para usuario {user_id}")
    return response

@router.get('/connect', name="fitbit_connect")
async def connect_fitbit_start(request: Request, user = Depends(get_current_user)):
    """Inicia el flujo OAuth de Fitbit con redirección."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = str(user['id'])
    
    # Generar URL de autorización y estado CSRF
    auth_url, state = FitbitAuthService.generate_auth_url()
    
    # Redireccionar directamente a Fitbit
    response = RedirectResponse(
        url=auth_url, 
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )
    
    # Configuración mejorada de cookies para CSRF
    secure = request.url.scheme == "https"
    response.set_cookie(
        key="fitbit_oauth_state", 
        value=state, 
        httponly=True, 
        secure=secure,
        samesite="lax" if not secure else "none",
        max_age=600,  # 10 minutos
        path="/"
    )
    response.set_cookie(
        key="fitbit_user_id_pending", 
        value=user_id, 
        httponly=True, 
        secure=secure,
        samesite="lax" if not secure else "none",
        max_age=600,  # 10 minutos
        path="/"
    )
    
    logger.info(f"Redirigiendo a OAuth Fitbit con state: {state[:10]}... para usuario {user_id}")
    return response

@router.get("/data", name="fitbit_data", response_class=JSONResponse)
async def get_fitbit_data_api(
    request: Request,
    data_type: str = Query(..., description="Tipo de dato a obtener",
                          enum=['profile', 'devices', 'activity_summary', 'sleep_log', 'heart_rate_intraday', 'cardio_score']),
    date: str = Query(None, description="Fecha (YYYY-MM-DD). Por defecto: hoy"),
    detail_level: str = Query(None, description="Detalle para intradía ('1sec', '1min')"),
    user = Depends(get_current_user)
):
    """Obtiene datos específicos de Fitbit para el usuario autenticado."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = str(user['id'])

    # Verificar si hay tokens válidos
    token_data = FitbitRepository.get_tokens(user_id)
    
    if not token_data or not token_data.get("is_connected"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Usuario no conectado a Fitbit.",
            headers={"X-Fitbit-Connected": "false"}
        )
        
    # Obtener access token válido (posiblemente refrescando)
    access_token = FitbitAuthService.get_valid_access_token(user_id)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Error al acceder a Fitbit (token inválido/expirado).",
            headers={"X-Fitbit-Connected": "false"}
        )
    
    # Obtener datos de Fitbit
    try:
        data = FitbitApiService.get_data(
            access_token=access_token,
            data_type=data_type,
            date=date,
            detail_level=detail_level
        )
        return JSONResponse(content={
            "success": True, 
            "data_type": data_type, 
            "data": data, 
            "is_connected": True
        })
    except Exception as e:
        logger.error(f"Error al obtener datos de Fitbit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener datos de Fitbit: {str(e)}"
        )

@router.post("/disconnect", name="fitbit_disconnect", response_class=JSONResponse)
async def disconnect_fitbit_api(request: Request, user = Depends(get_current_user)):
    """Desconecta la cuenta de Fitbit eliminando los tokens."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = str(user['id'])
    
    # Revocar token en Fitbit (opcional)
    # FitbitAuthService.revoke_token(user_id)
    
    # Eliminar tokens de la base de datos
    success = FitbitRepository.delete_tokens(user_id)
    
    if success:
        return JSONResponse(content={"success": True, "message": "Cuenta de Fitbit desconectada."})
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error al intentar desconectar la cuenta de Fitbit."
        )