# back_end/gym/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging
from .services.db_utils import execute_db_query  # Corregido: añadido 'services'
from . import config

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Valida el token JWT y devuelve la información del usuario.
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        
        # Verificar si el usuario existe en la base de datos
        query = "SELECT id, telegram_id, google_id, email, display_name FROM public.users WHERE id = %s"
        user = execute_db_query(query, (payload.get("user_id"),), fetch_one=True)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        # Convertir a diccionario para facilitar su uso
        if hasattr(user, "keys"):
            # Ya es un diccionario (RealDictRow)
            return user
        else:
            # Es una tupla, convertir a diccionario
            return {
                "id": user[0],
                "telegram_id": user[1],
                "google_id": user[2],
                "email": user[3],
                "display_name": user[4]
            }
    
    except jwt.PyJWTError as e:
        logger.error(f"Error de autenticación JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido"
        )
    except Exception as e:
        logger.error(f"Error al validar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )