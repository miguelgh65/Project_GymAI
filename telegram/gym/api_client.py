# telegram/gym/api_client.py
import os
import logging
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5050')
TELEGRAM_BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN', '')

if not TELEGRAM_BOT_API_TOKEN:
    logging.warning("⚠️ TELEGRAM_BOT_API_TOKEN no está configurado en el archivo .env")

class ApiClient:
    """Cliente para hacer solicitudes a la API del backend."""
    
    @staticmethod
    def get_headers():
        """Devuelve las cabeceras necesarias para autenticarse como bot de Telegram."""
        return {
            'Content-Type': 'application/json',
            'X-Telegram-Bot-Token': TELEGRAM_BOT_API_TOKEN
        }
    
    @staticmethod
    def get_logs(telegram_id, days=7):
        """
        Obtiene los logs de ejercicios para un usuario.
        
        Args:
            telegram_id (str): ID de Telegram del usuario
            days (int): Número de días hacia atrás para obtener logs
            
        Returns:
            dict: Respuesta de la API con los logs
        """
        try:
            url = f"{BASE_URL}/api/logs?telegram_id={telegram_id}&days={days}"
            response = requests.get(url, headers=ApiClient.get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error al obtener logs: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Error al obtener los datos: {response.status_code}"
                }
        except Exception as e:
            logging.exception(f"Error al conectar con la API para obtener logs: {str(e)}")
            return {
                "success": False,
                "message": "Error de conexión con el servidor"
            }
    
    @staticmethod
    def get_routine(telegram_id):
        """
        Obtiene la configuración de rutina de un usuario.
        
        Args:
            telegram_id (str): ID de Telegram del usuario
            
        Returns:
            dict: Respuesta de la API con la rutina
        """
        try:
            url = f"{BASE_URL}/api/rutina?telegram_id={telegram_id}"
            response = requests.get(url, headers=ApiClient.get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error al obtener rutina: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Error al obtener la rutina: {response.status_code}"
                }
        except Exception as e:
            logging.exception(f"Error al conectar con la API para obtener rutina: {str(e)}")
            return {
                "success": False,
                "message": "Error de conexión con el servidor"
            }
    
    @staticmethod
    def get_today_routine(telegram_id):
        """
        Obtiene la rutina del día actual para un usuario.
        
        Args:
            telegram_id (str): ID de Telegram del usuario
            
        Returns:
            dict: Respuesta de la API con la rutina del día
        """
        try:
            url = f"{BASE_URL}/api/rutina_hoy?telegram_id={telegram_id}"
            response = requests.get(url, headers=ApiClient.get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error al obtener rutina de hoy: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Error al obtener la rutina de hoy: {response.status_code}"
                }
        except Exception as e:
            logging.exception(f"Error al conectar con la API para obtener rutina de hoy: {str(e)}")
            return {
                "success": False,
                "message": "Error de conexión con el servidor"
            }
    
    @staticmethod
    def save_routine(telegram_id, routine_data):
        """
        Guarda la configuración de rutina de un usuario.
        
        Args:
            telegram_id (str): ID de Telegram del usuario
            routine_data (dict): Datos de la rutina a guardar
            
        Returns:
            dict: Respuesta de la API
        """
        try:
            url = f"{BASE_URL}/api/rutina"
            data = {
                "telegram_id": telegram_id,
                "rutina": routine_data
            }
            response = requests.post(url, json=data, headers=ApiClient.get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error al guardar rutina: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Error al guardar la rutina: {response.status_code}"
                }
        except Exception as e:
            logging.exception(f"Error al conectar con la API para guardar rutina: {str(e)}")
            return {
                "success": False,
                "message": "Error de conexión con el servidor"
            }
    
    @staticmethod
    def log_exercise(telegram_id, exercise_data):
        """
        Registra un ejercicio para un usuario.
        
        Args:
            telegram_id (str): ID de Telegram del usuario
            exercise_data (str): Descripción del ejercicio a registrar
            
        Returns:
            dict: Respuesta de la API
        """
        try:
            url = f"{BASE_URL}/api/log-exercise"
            data = {
                "telegram_id": telegram_id,
                "exercise_data": exercise_data
            }
            response = requests.post(url, json=data, headers=ApiClient.get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error al registrar ejercicio: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Error al registrar el ejercicio: {response.status_code}"
                }
        except Exception as e:
            logging.exception(f"Error al conectar con la API para registrar ejercicio: {str(e)}")
            return {
                "success": False,
                "message": "Error de conexión con el servidor"
            }