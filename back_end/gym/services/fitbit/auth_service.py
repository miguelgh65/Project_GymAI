# Archivo: back_end/gym/services/fitbit/auth_service.py
import os
import logging
import base64
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from ...repositories.fitbit_repository import FitbitRepository

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logger = logging.getLogger(__name__)

# Configuración de Fitbit
FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID')
FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET')
FITBIT_REDIRECT_URI = os.getenv('FITBIT_REDIRECT_URI')
FITBIT_AUTH_URL = os.getenv('FITBIT_AUTH_URL', 'https://www.fitbit.com/oauth2/authorize')
FITBIT_TOKEN_URL = os.getenv('FITBIT_TOKEN_URL', 'https://api.fitbit.com/oauth2/token')

class FitbitAuthService:
    """Servicio para gestionar la autenticación OAuth con Fitbit."""
    
    @staticmethod
    def generate_auth_url():
        """
        Genera una URL de autorización de Fitbit y un estado CSRF.
        
        Returns:
            tuple: (url, state) - URL de autorización y estado CSRF
        """
        state = secrets.token_urlsafe(16)
        
        auth_params = {
            "response_type": "code",
            "client_id": FITBIT_CLIENT_ID,
            "redirect_uri": FITBIT_REDIRECT_URI,
            "scope": "activity heartrate location nutrition profile settings sleep weight",
            "state": state,
        }
        
        auth_url = f"{FITBIT_AUTH_URL}?{urlencode(auth_params)}"
        
        return auth_url, state
    
    @staticmethod
    def exchange_code_for_token(code):
        """
        Intercambia un código de autorización por tokens de acceso.
        
        Args:
            code (str): Código de autorización de Fitbit
            
        Returns:
            dict: Tokens de acceso o None si hay error
        """
        # Preparar encabezados de autenticación
        auth_string = f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}"
        auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Datos para la solicitud
        data = {
            "client_id": FITBIT_CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": FITBIT_REDIRECT_URI
        }
        
        try:
            logger.info(f"Intercambiando código por tokens")
            response = requests.post(
                FITBIT_TOKEN_URL,
                headers=headers,
                data=data,
                timeout=20
            )
            
            if response.status_code != 200:
                logger.error(f"Error al intercambiar código: {response.status_code}")
                logger.error(f"Respuesta: {response.text[:200]}")
                return None
            
            tokens = response.json()
            return tokens
            
        except Exception as e:
            logger.exception(f"Error al intercambiar código por tokens: {str(e)}")
            return None
    
    @staticmethod
    def refresh_token(refresh_token, user_id):
        """
        Refresca un token de acceso usando el refresh token.
        
        Args:
            refresh_token (str): Token de refresco
            user_id (str): ID del usuario
            
        Returns:
            dict: Nuevos tokens o None si hay error
        """
        auth_string = f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}"
        auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        try:
            logger.info(f"Refrescando token para usuario {user_id}")
            response = requests.post(
                FITBIT_TOKEN_URL,
                headers=headers,
                data=data,
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Error al refrescar token: {response.status_code}")
                logger.error(f"Respuesta: {response.text[:200]}")
                # Si el token es inválido, eliminar tokens
                if response.status_code in [400, 401]:
                    FitbitRepository.delete_tokens(user_id)
                return None
            
            new_tokens = response.json()
            
            # Guardar nuevos tokens
            if FitbitRepository.save_tokens(user_id, new_tokens):
                logger.info(f"Tokens refrescados guardados para usuario {user_id}")
                return new_tokens
            else:
                logger.error(f"Error al guardar tokens refrescados")
                return None
                
        except Exception as e:
            logger.exception(f"Error al refrescar token: {str(e)}")
            return None
    
    @staticmethod
    def get_valid_access_token(user_id):
        """
        Obtiene un token de acceso válido, refrescándolo si es necesario.
        
        Args:
            user_id (str): ID del usuario
            
        Returns:
            str: Token de acceso válido o None si hay error
        """
        token_data = FitbitRepository.get_tokens(user_id)
        
        if not token_data or not token_data.get('is_connected'):
            return None
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_at_str = token_data.get('expires_at')
        
        if not access_token or not refresh_token or not expires_at_str:
            return None
        
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.now()
            
            # Ajustar zona horaria si es necesario
            if expires_at.tzinfo:
                now = now.replace(tzinfo=expires_at.tzinfo)
            
            # Si está por expirar en menos de 5 minutos, refrescar
            if now + timedelta(minutes=5) >= expires_at:
                logger.info(f"Token expirado/por expirar para usuario {user_id}. Refrescando...")
                new_tokens = FitbitAuthService.refresh_token(refresh_token, user_id)
                return new_tokens.get('access_token') if new_tokens else None
            else:
                return access_token
                
        except Exception as e:
            logger.exception(f"Error al verificar expiración del token: {str(e)}")
            return None