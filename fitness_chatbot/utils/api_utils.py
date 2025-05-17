# fitness_chatbot/utils/api_utils.py
import logging
import json
import os
import requests
import time
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("fitness_chatbot")

# URL base para las APIs - Usando un puerto diferente para evitar auto-referencia
# Si estamos en el mismo contenedor, usamos localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost")

# Tiempo de espera para solicitudes - AUMENTADO
DEFAULT_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Número de reintentos para solicitudes internas
DEFAULT_RETRIES = int(os.getenv("API_RETRIES", "3"))

# Bandera para detectar si estamos dentro del contexto de una solicitud de chatbot
# Esto ayudará a evitar bucles infinitos
IN_CHATBOT_CONTEXT = False

def get_auth_token() -> Optional[str]:
    """
    Obtiene el token de autenticación JWT para usar en las solicitudes a la API.
    
    Returns:
        El token JWT o None si no está disponible
    """
    return None  # Esto será reemplazado por el token real que viene del usuario

def make_api_request(
    endpoint: str, 
    method: str = "GET", 
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    auth_token: Optional[str] = None
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
        retries: Número de reintentos para solicitudes fallidas
        auth_token: Token JWT para autenticación
        
    Returns:
        Dict con la respuesta JSON o información de error
    """
    global IN_CHATBOT_CONTEXT
    
    # Si estamos en contexto de chatbot y la solicitud es a un endpoint restringido,
    # usamos el endpoint _internal correspondiente
    if IN_CHATBOT_CONTEXT and endpoint in ["logs", "ejercicios_stats"]:
        logger.info(f"⚠️ Detectada posible referencia circular. Usando endpoint interno.")
        endpoint = f"internal/{endpoint}"
    
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
    
    # Añadir cabecera especial para marcar que es una solicitud interna
    # Esto ayudará al backend a identificar solicitudes internas
    default_headers["X-Internal-Request"] = "true"
    
    # Fusionar cabeceras personalizadas si se proporcionan
    if headers:
        default_headers.update(headers)
    
    logger.info(f"Realizando solicitud {method} a {url}")
    if params:
        logger.debug(f"Parámetros: {params}")
    if json_data:
        logger.debug(f"Datos JSON: {json_data}")
    if auth_token:
        logger.debug(f"Solicitud autenticada con token: {auth_token[:10]}...")
    
    # Configuración para reintentos
    retry_count = 0
    max_retries = retries
    
    # Si es un endpoint interno, usar reintentos
    should_retry = endpoint.startswith("internal/")
    
    while True:
        try:
            # Realizar la solicitud con el timeout especificado
            response = requests.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_data,
                headers=default_headers,
                timeout=timeout  # CORREGIDO: Eliminado cero inicial que causaba error de octal
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
                
                # Si debemos reintentar y no hemos agotado los reintentos
                if should_retry and retry_count < max_retries and response.status_code >= 500:
                    retry_count += 1
                    retry_delay = 0.5 * (2 ** retry_count)  # Backoff exponencial
                    logger.info(f"Reintentando en {retry_delay:.2f} segundos... ({retry_count}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            else:
                logger.info(f"API respondió exitosamente ({response.status_code})")
            
            return response_data
            
        except requests.RequestException as e:
            logger.error(f"Error en solicitud API: {str(e)}")
            
            # Si debemos reintentar y no hemos agotado los reintentos
            if should_retry and retry_count < max_retries:
                retry_count += 1
                retry_delay = 0.5 * (2 ** retry_count)  # Backoff exponencial
                logger.info(f"Reintentando en {retry_delay:.2f} segundos... ({retry_count}/{max_retries})")
                time.sleep(retry_delay)
                continue
            
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", 500) if hasattr(e, "response") else 500
            }

def get_exercise_data(
    user_id: str, 
    exercise: Optional[str] = None, 
    days: int = 30,
    auth_token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Obtiene datos de ejercicios del usuario.
    
    Args:
        user_id: ID del usuario
        exercise: Nombre del ejercicio específico (opcional)
        days: Número de días hacia atrás para obtener datos
        auth_token: Token JWT para autenticación
        timeout: Tiempo de espera personalizado
        
    Returns:
        Dict con datos de ejercicios
    """
    global IN_CHATBOT_CONTEXT
    
    # Marcar que estamos en contexto de chatbot
    old_context = IN_CHATBOT_CONTEXT
    IN_CHATBOT_CONTEXT = True
    
    try:
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
            return make_api_request(endpoint, params=params, auth_token=auth_token, timeout=timeout)
        else:
            # Obtener logs generales de ejercicios
            endpoint = "logs"
            params = {"days": days}
            
            logger.info(f"Obteniendo logs de ejercicios para los últimos {days} días")
            return make_api_request(endpoint, params=params, auth_token=auth_token, timeout=timeout)
    finally:
        # Restaurar el contexto previo
        IN_CHATBOT_CONTEXT = old_context

def log_exercise(
    user_id: str, 
    exercise_data: Union[str, Dict[str, Any]],
    auth_token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Registra un ejercicio en el backend.
    
    Args:
        user_id: ID del usuario
        exercise_data: Descripción textual del ejercicio o diccionario con datos completos
        auth_token: Token JWT para autenticación
        timeout: Tiempo de espera personalizado
        
    Returns:
        Dict con resultado del registro
    """
    global IN_CHATBOT_CONTEXT
    
    # Marcar que estamos en contexto de chatbot
    old_context = IN_CHATBOT_CONTEXT
    IN_CHATBOT_CONTEXT = True
    
    try:
        endpoint = "log-exercise"
        
        # Si exercise_data es un string, convertirlo a diccionario
        json_data = {}
        if isinstance(exercise_data, str):
            json_data = {"exercise_data": exercise_data}
        elif isinstance(exercise_data, dict):
            # Si ya es un diccionario, verificar que tenga exercise_data
            if "exercise_data" not in exercise_data:
                logger.error("El diccionario exercise_data debe tener una clave 'exercise_data'")
                return {"success": False, "error": "Formato de datos incorrecto"}
            json_data = exercise_data
        else:
            logger.error(f"Tipo de datos no soportado: {type(exercise_data)}")
            return {"success": False, "error": "Tipo de datos no soportado"}
        
        logger.info(f"Registrando ejercicio para usuario {user_id}: {json_data}")
        return make_api_request(endpoint, method="POST", json_data=json_data, auth_token=auth_token, timeout=timeout)
    finally:
        # Restaurar el contexto previo
        IN_CHATBOT_CONTEXT = old_context

def get_nutrition_data(
    user_id: str, 
    days: int = 7,
    auth_token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Obtiene datos de nutrición del usuario.
    
    Args:
        user_id: ID del usuario
        days: Número de días hacia atrás para obtener datos
        auth_token: Token JWT para autenticación
        timeout: Tiempo de espera personalizado
        
    Returns:
        Dict con datos de nutrición
    """
    global IN_CHATBOT_CONTEXT
    
    # Marcar que estamos en contexto de chatbot
    old_context = IN_CHATBOT_CONTEXT
    IN_CHATBOT_CONTEXT = True
    
    try:
        endpoint = "nutrition/tracking/week"
        logger.info(f"Obteniendo datos de nutrición para los últimos {days} días")
        return make_api_request(endpoint, auth_token=auth_token, timeout=timeout)
    except Exception as e:
        logger.error(f"Error obteniendo datos de nutrición: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # Restaurar el contexto previo
        IN_CHATBOT_CONTEXT = old_context
def get_today_routine(
    user_id: str, 
    auth_token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Obtiene la rutina del día actual para el usuario.
    
    Args:
        user_id: ID del usuario
        auth_token: Token JWT para autenticación
        timeout: Tiempo de espera personalizado
        
    Returns:
        Dict con datos de la rutina del día
    """
    global IN_CHATBOT_CONTEXT
    
    # Marcar que estamos en contexto de chatbot
    old_context = IN_CHATBOT_CONTEXT
    IN_CHATBOT_CONTEXT = True
    
    try:
        endpoint = "rutina_hoy"
        params = {"format": "json"}
        
        logger.info(f"Obteniendo rutina de hoy para usuario {user_id}")
        return make_api_request(
            endpoint=endpoint, 
            method="GET",
            params=params, 
            auth_token=auth_token, 
            timeout=timeout
        )
    except Exception as e:
        logger.error(f"Error obteniendo rutina del día: {e}")
        return {
            "success": False, 
            "error": str(e),
            "message": "No se pudo obtener la rutina del día"
        }
    finally:
        # Restaurar el contexto previo
        IN_CHATBOT_CONTEXT = old_context
        
def get_progress_data(
    user_id: str, 
    exercise: Optional[str] = None,
    auth_token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Obtiene datos de progreso del usuario.
    
    Args:
        user_id: ID del usuario
        exercise: Nombre del ejercicio específico (opcional)
        auth_token: Token JWT para autenticación
        timeout: Tiempo de espera personalizado
        
    Returns:
        Dict con datos de progreso
    """
    # Usar el mismo endpoint que get_exercise_data pero con más días para ver progreso
    return get_exercise_data(user_id, exercise, days=90, auth_token=auth_token, timeout=timeout)