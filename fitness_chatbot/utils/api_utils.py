# fitness_chatbot/utils/api_utils.py
import logging
import json
import os
import requests
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("fitness_chatbot")

# URL base para las APIs - Usamos localhost dentro del contenedor
# Dentro de Docker, usamos localhost ya que estamos en el mismo contenedor que el backend
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5050")

# La función para obtener el token de autenticación desde el middleware de FastAPI
# El token debe ser obtenido inicialmente y pasado al nodo
def get_auth_token() -> Optional[str]:
    """
    Obtiene el token de autenticación JWT para usar en las solicitudes a la API.
    
    Returns:
        El token JWT o None si no está disponible
    """
    # En un entorno real, este token vendría del frontend o estaría almacenado en algún lugar seguro
    # Para fines de prueba, podrías usar un token hard-coded
    return None  # Esto será reemplazado por el token real que viene del usuario

def make_api_request(
    endpoint: str, 
    method: str = "GET", 
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    auth_token: Optional[str] = None  # Nuevo parámetro para el token
) -> Dict[str, Any]:
    """
    Realiza una solicitud a la API del backend.
    
    Args:
        endpoint: Ruta del endpoint (sin la base URL)
        method: Método HTTP (GET, POST, PUT, DELETE)
        params: Parámetros de consulta
        json_data: Datos JSON para el cuerpo de la solicitud
        headers: Cabeceras HTTP adicionales
        timeout: Tiempo de espera en segundos
        auth_token: Token JWT para autenticación
        
    Returns:
        Dict con la respuesta JSON o información de error
    """
    # Asegurar que el endpoint no comienza con /
    if endpoint.startswith("/"):
        endpoint = endpoint[1:]
    
    # Construir URL completa
    url = f"{API_BASE_URL}/api/{endpoint}"
    
    # Configurar cabeceras por defecto
    default_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Añadir token de autenticación si está disponible
    if auth_token:
        default_headers["Authorization"] = f"Bearer {auth_token}"
    
    # Combinar con cabeceras adicionales
    if headers:
        default_headers.update(headers)
    
    logger.info(f"Realizando solicitud {method} a {url}")
    if params:
        logger.debug(f"Parámetros: {params}")
    if json_data:
        logger.debug(f"Datos JSON: {json_data}")
    if auth_token:
        logger.debug(f"Solicitud autenticada con token: {auth_token[:10]}...")
    
    try:
        # Realizar la solicitud
        response = requests.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json_data,
            headers=default_headers,
            timeout=timeout
        )
        
        # Intentar obtener respuesta JSON
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.warning(f"Respuesta no JSON recibida: {response.text[:200]}")
            response_data = {"text": response.text}
        
        # Añadir información sobre la respuesta
        response_data["status_code"] = response.status_code
        response_data["success"] = 200 <= response.status_code < 300
        
        if not response_data["success"]:
            logger.warning(f"API respondió con código {response.status_code}: {response_data.get('detail', '')}")
        else:
            logger.info(f"API respondió exitosamente ({response.status_code})")
        
        return response_data
    
    except requests.RequestException as e:
        logger.error(f"Error en solicitud API: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500) if hasattr(e, "response") else 500
        }

def get_exercise_data(
    user_id: str, 
    exercise: Optional[str] = None, 
    days: int = 30,
    auth_token: Optional[str] = None  # Nuevo parámetro para el token
) -> Dict[str, Any]:
    """
    Obtiene datos de ejercicios del usuario.
    
    Args:
        user_id: ID del usuario
        exercise: Nombre del ejercicio específico (opcional)
        days: Número de días hacia atrás para obtener datos
        auth_token: Token JWT para autenticación
        
    Returns:
        Dict con datos de ejercicios
    """
    if exercise:
        # Obtener datos de un ejercicio específico
        endpoint = "ejercicios_stats"
        # Usar fecha actual para filtrar
        from datetime import datetime, timedelta
        fecha_hasta = datetime.now().strftime("%Y-%m-%d")
        fecha_desde = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        params = {
            "desde": fecha_desde,
            "hasta": fecha_hasta,
            "ejercicio": exercise
        }
        
        logger.info(f"Obteniendo estadísticas para ejercicio: {exercise}")
        return make_api_request(endpoint, params=params, auth_token=auth_token)
    else:
        # Obtener logs generales de ejercicios
        endpoint = "logs"
        params = {"days": days}
        
        logger.info(f"Obteniendo logs de ejercicios para los últimos {days} días")
        return make_api_request(endpoint, params=params, auth_token=auth_token)

def log_exercise(
    user_id: str, 
    exercise_data: str,
    auth_token: Optional[str] = None  # Nuevo parámetro para el token
) -> Dict[str, Any]:
    """
    Registra un ejercicio en el backend.
    
    Args:
        user_id: ID del usuario
        exercise_data: Descripción textual del ejercicio
        auth_token: Token JWT para autenticación
        
    Returns:
        Dict con resultado del registro
    """
    endpoint = "log-exercise"
    json_data = {"exercise_data": exercise_data}
    
    logger.info(f"Registrando ejercicio para usuario {user_id}: {exercise_data}")
    return make_api_request(endpoint, method="POST", json_data=json_data, auth_token=auth_token)

def get_nutrition_data(
    user_id: str, 
    days: int = 7,
    auth_token: Optional[str] = None  # Nuevo parámetro para el token
) -> Dict[str, Any]:
    """
    Obtiene datos de nutrición del usuario.
    
    Args:
        user_id: ID del usuario
        days: Número de días hacia atrás para obtener datos
        auth_token: Token JWT para autenticación
        
    Returns:
        Dict con datos de nutrición
    """
    # Esto debería apuntar a un endpoint de nutrición en el backend
    # Si no existe, devolver datos simulados
    try:
        endpoint = "nutrition/tracking/week"
        logger.info(f"Obteniendo datos de nutrición para los últimos {days} días")
        return make_api_request(endpoint, auth_token=auth_token)
    except Exception as e:
        logger.error(f"Error obteniendo datos de nutrición: {e}")
        return {"success": False, "error": str(e)}

def get_progress_data(
    user_id: str, 
    exercise: Optional[str] = None,
    auth_token: Optional[str] = None  # Nuevo parámetro para el token
) -> Dict[str, Any]:
    """
    Obtiene datos de progreso del usuario.
    
    Args:
        user_id: ID del usuario
        exercise: Nombre del ejercicio específico (opcional)
        auth_token: Token JWT para autenticación
        
    Returns:
        Dict con datos de progreso
    """
    # Usar el mismo endpoint que get_exercise_data pero con más días para ver progreso
    return get_exercise_data(user_id, exercise, days=90, auth_token=auth_token)