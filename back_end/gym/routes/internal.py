# back_end/gym/routes/internal.py
# Endpoints internos para uso exclusivo de los componentes internos del sistema
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

# Importaciones para la autenticación y acceso a BD
from back_end.gym.middlewares import get_current_user
from services.database import get_exercise_logs

# Configurar router con prefijo y tags
router = APIRouter(
    prefix="/api/internal",
    tags=["internal"]
)

logger = logging.getLogger(__name__)

@router.get("/logs", response_class=JSONResponse)
async def internal_get_logs_endpoint(
    request: Request,
    days: int = Query(30, ge=1, description="Número de días hacia atrás para obtener logs."),
    user = Depends(get_current_user)
):
    """
    Endpoint INTERNO para obtener logs de ejercicios.
    Este endpoint es similar a /api/logs pero optimizado para llamadas internas.
    """
    if not user:
        logger.warning("Intento de obtener logs internos sin autenticación")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado.")

    # Verificar si es una solicitud interna
    if "X-Internal-Request" not in request.headers:
        logger.warning("Intento de acceso a endpoint interno desde fuera del sistema")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Este endpoint es solo para uso interno del sistema."
        )
    
    # Obtener el ID del usuario
    user_id = user.get('google_id')
    if not user_id:
        user_id = str(user.get('id'))
    
    logger.info(f"Obteniendo logs INTERNOS para {user_id}, {days} días.")

    try:
        # Acceso directo a la función de base de datos (sin overhead adicional)
        logs = get_exercise_logs(user_id, days)

        if logs is None:
            logger.error(f"La función get_exercise_logs devolvió None para usuario {user_id}.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Error interno al consultar los logs de entrenamiento."
            )

        logger.info(f"Logs INTERNOS obtenidos ({len(logs)} registros) para usuario {user_id}")
        
        # Devolver simplemente la lista de logs sin procesamiento adicional
        return JSONResponse(content={
            "success": True,
            "logs": logs
        })

    except Exception as e:
        logger.exception(f"Error inesperado al obtener logs INTERNOS para {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno del servidor al obtener logs: {str(e)}"
        )

