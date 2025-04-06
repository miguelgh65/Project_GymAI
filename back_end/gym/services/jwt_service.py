# back_end/gym/services/jwt_service.py
import os
import jwt
import time
import logging
from datetime import datetime, timedelta

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_temporal_para_desarrollo")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 días

# Crear logger correctamente
logger = logging.getLogger(__name__)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Crea un token JWT con los datos proporcionados.
    """
    to_encode = data.copy()
    
    # Establecer expiración
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Añadir claims estándar
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # Crear token
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Token JWT creado para usuario_id={data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error al crear token JWT: {e}")
        return None

def verify_token(token: str):
    """
    Verifica un token JWT y devuelve los datos si es válido.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token JWT no contiene 'sub' (user_id)")
            return None
        
        # Verificar tipo de token
        token_type = payload.get("type")
        if token_type != "access":
            logger.warning(f"Tipo de token incorrecto: {token_type}")
            return None
            
        # Verificar expiración (jwt.decode ya lo verifica, pero podemos hacer validaciones adicionales)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token JWT expirado")
            return None
            
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"Error al verificar token JWT: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al verificar token: {e}")
        return None