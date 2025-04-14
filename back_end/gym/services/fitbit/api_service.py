# Archivo: back_end/gym/services/fitbit/api_service.py
import logging
from datetime import datetime, timedelta

import requests

from .data_service import FitbitDataService

# Configuración de logging
logger = logging.getLogger(__name__)

class FitbitApiService:
    """Servicio para interactuar con la API de Fitbit."""
    
    BASE_API_URL = "https://api.fitbit.com"
    
    @staticmethod
    def get_data(access_token, data_type, date=None, detail_level=None):
        """
        Obtiene datos de la API de Fitbit.
        
        Args:
            access_token (str): Token de acceso
            data_type (str): Tipo de datos (profile, activity_summary, etc.)
            date (str): Fecha en formato YYYY-MM-DD o None para hoy
            detail_level (str): Nivel de detalle para datos intradía
            
        Returns:
            dict: Datos de la API de Fitbit
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept-Language": "es_ES"
        }
        
        # Usar fecha actual si no se proporciona
        target_date = date if date else datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Construir URL de la API según el tipo de datos
        if data_type == 'profile':
            api_path = "/1/user/-/profile.json"
        elif data_type == 'devices':
            api_path = "/1/user/-/devices.json"
        elif data_type == 'activity_summary':
            api_path = f"/1/user/-/activities/date/{target_date}.json"
        elif data_type == 'sleep_log':
            api_path = f"/1.2/user/-/sleep/date/{target_date}.json"
        elif data_type == 'cardio_score':
            api_path = f"/1/user/-/cardioscore/date/{date if date else yesterday}.json"
        elif data_type == 'heart_rate_intraday':
            detail = detail_level if detail_level in ['1sec', '1min'] else '1min'
            api_path = f"/1/user/-/activities/heart/date/{target_date}/1d/{detail}.json"
        else:
            raise ValueError(f"Tipo de datos no soportado: {data_type}")
        
        # Construir URL completa
        url = f"{FitbitApiService.BASE_API_URL}{api_path}"
        
        try:
            logger.info(f"Solicitando datos de Fitbit: {data_type}")
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"Error {response.status_code} al obtener datos de Fitbit")
                logger.error(f"Respuesta: {response.text[:200]}")
                raise ValueError(f"Error {response.status_code} al obtener datos de Fitbit")
            
            data = response.json()
            
            # Procesar datos si es necesario
            processed_data = FitbitDataService.process_data(data_type, data)
            
            return processed_data
            
        except Exception as e:
            logger.exception(f"Error al obtener datos de Fitbit: {str(e)}")
            raise