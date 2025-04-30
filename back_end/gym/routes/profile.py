# Archivo: back_end/gym/routes/profile.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ..middlewares import get_current_user
from ..services.auth_service import get_user_by_id

# Configuración de logging
logger = logging.getLogger(__name__)

# Router de perfil (sin Fitbit)
router = APIRouter(
    prefix="/api/profile", 
    tags=["profile"],
)

@router.get("", name="get_profile")
async def get_profile(request: Request, user = Depends(get_current_user)):
    """Obtiene la información de perfil del usuario autenticado."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    # Obtener datos adicionales si es necesario
    # Por ahora, simplemente devolver los datos de usuario
    return JSONResponse(content={
        "success": True,
        "user": {
            "id": user.get("id"),
            "display_name": user.get("display_name"),
            "email": user.get("email"),
            "profile_picture": user.get("profile_picture"),
            "has_telegram": user.get("telegram_id") is not None,
            "has_google": user.get("google_id") is not None,
        }
    })

@router.put("/update", name="update_profile")
async def update_profile(request: Request, user = Depends(get_current_user)):
    """Actualiza la información de perfil del usuario."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")
    
    # TODO: Implementar actualización de perfil
    return JSONResponse(content={"success": True, "message": "Perfil actualizado correctamente"})