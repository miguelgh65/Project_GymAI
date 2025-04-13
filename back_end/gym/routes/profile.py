# Imports (Python Standard Library)
import os
import sys
import base64
import json
import secrets
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Imports (External Libraries)
import psycopg2
import requests
from dotenv import load_dotenv
from fastapi import (APIRouter, Depends, Form, HTTPException, Query, Request,
                     Response, status)
from fastapi.responses import JSONResponse, RedirectResponse

# --- Carga de Variables de Entorno ---
load_dotenv()

# --- Importaciones del Proyecto ---
try:
    from config import DB_CONFIG
    from back_end.gym.middlewares import get_current_user
    # Importar servicio JWT para verificar tokens en URL
    from back_end.gym.services.jwt_service import verify_token
    from back_end.gym.services.auth_service import get_user_by_id
except ImportError as e:
    logging.critical(f"Error Crítico: No se pudieron importar módulos esenciales: {e}. Revisa las rutas.")
    sys.exit(f"Error de importación: {e}")

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Router de FastAPI ---
router = APIRouter(
    prefix="/api/fitbit", 
    tags=["fitbit"],
)

# --- Configuración de Fitbit ---
FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID')
FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET')
FITBIT_REDIRECT_URI = os.getenv('FITBIT_REDIRECT_URI')
FITBIT_AUTH_URL = os.getenv('FITBIT_AUTH_URL')
FITBIT_TOKEN_URL = os.getenv('FITBIT_TOKEN_URL')
FITBIT_PROFILE_URL = os.getenv('FITBIT_PROFILE_URL')

# URLs del Frontend
FRONTEND_APP_URL = os.getenv('FRONTEND_APP_URL', 'http://localhost:3000')
FRONTEND_FITBIT_SUCCESS_PATH = os.getenv('FRONTEND_FITBIT_SUCCESS_PATH', '/profile?fitbit_status=success')
FRONTEND_FITBIT_ERROR_PATH = os.getenv('FRONTEND_FITBIT_ERROR_PATH', '/profile?fitbit_status=error')

# --- Verificación de Variables Esenciales ---
required_fitbit_vars = {
    "FITBIT_CLIENT_ID": FITBIT_CLIENT_ID,
    "FITBIT_CLIENT_SECRET": FITBIT_CLIENT_SECRET,
    "FITBIT_REDIRECT_URI": FITBIT_REDIRECT_URI,
    "FITBIT_AUTH_URL": FITBIT_AUTH_URL,
    "FITBIT_TOKEN_URL": FITBIT_TOKEN_URL,
    "FITBIT_PROFILE_URL": FITBIT_PROFILE_URL,
    "FRONTEND_APP_URL": FRONTEND_APP_URL,
}

missing_vars = [key for key, value in required_fitbit_vars.items() if value is None]
if missing_vars:
    raise EnvironmentError(f"Error Crítico: Faltan variables de entorno esenciales para Fitbit: {', '.join(missing_vars)}. Verifica tu archivo .env.")

# --- Funciones de Utilidad para Base de Datos ---

def _execute_db_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Función auxiliar genérica para ejecutar consultas a la BD."""
    conn = None
    cur = None
    result = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, params)

        if commit:
            conn.commit()
            result = True
        elif fetch_one:
            result = cur.fetchone()
        elif fetch_all:
            result = cur.fetchall()

    except psycopg2.Error as db_err:
        logger.error(f"Error de base de datos: {db_err}", exc_info=True)
        if conn: conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Error inesperado en la base de datos: {e}", exc_info=True)
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return result

def get_fitbit_tokens_from_db(user_id):
    """Obtiene los tokens de Fitbit para un user_id específico desde la BD."""
    query = "SELECT client_id, access_token, refresh_token, expires_at FROM fitbit_tokens WHERE user_id = %s"
    try:
        result = _execute_db_query(query, (str(user_id),), fetch_one=True)
        if result:
            expires_at = result[3]
            expires_at_iso = expires_at.isoformat() if isinstance(expires_at, datetime) else str(expires_at)
            return {
                "is_connected": True, "client_id": result[0], "access_token": result[1],
                "refresh_token": result[2], "expires_at": expires_at_iso
            }
        else:
            return {"is_connected": False}
    except Exception as e:
        logger.error(f"Error al obtener tokens Fitbit para usuario {user_id}: {e}")
        return {"is_connected": False, "error": "Error de base de datos"}

def save_fitbit_tokens_to_db(user_id, client_id, tokens):
    """Guarda o actualiza los tokens de Fitbit en la base de datos usando UPSERT."""
    expires_in = tokens.get('expires_in', 28800)
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    user_id_str = str(user_id)

    # Crear tabla si no existe (Idealmente manejado por migraciones)
    create_table_query = """
        CREATE TABLE IF NOT EXISTS fitbit_tokens (
            id SERIAL PRIMARY KEY, user_id VARCHAR(255) NOT NULL UNIQUE, client_id VARCHAR(255) NOT NULL,
            access_token TEXT NOT NULL, refresh_token TEXT NOT NULL, expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        ); CREATE INDEX IF NOT EXISTS idx_fitbit_user_id ON fitbit_tokens(user_id);
    """
    try: _execute_db_query(create_table_query, commit=True)
    except Exception as e:
        if "already exists" not in str(e): logger.warning(f"Error al intentar crear tabla fitbit_tokens: {e}")

    upsert_query = """
        INSERT INTO fitbit_tokens (user_id, client_id, access_token, refresh_token, expires_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            client_id = EXCLUDED.client_id, access_token = EXCLUDED.access_token, refresh_token = EXCLUDED.refresh_token,
            expires_at = EXCLUDED.expires_at, updated_at = NOW();
    """
    params = (user_id_str, client_id, access_token, refresh_token, expires_at)
    try:
        success = _execute_db_query(upsert_query, params, commit=True)
        if success: logger.info(f"Tokens Fitbit guardados/actualizados para usuario {user_id_str}")
        return success
    except Exception as e:
        logger.error(f"Error al guardar tokens Fitbit para usuario {user_id_str}: {e}", exc_info=True)
        return False

def delete_fitbit_tokens(user_id):
    """Elimina los tokens de Fitbit para un usuario de la BD."""
    query = "DELETE FROM fitbit_tokens WHERE user_id = %s"
    try:
        success = _execute_db_query(query, (str(user_id),), commit=True)
        if success: logger.info(f"Tokens Fitbit eliminados para usuario {user_id}")
        return success
    except Exception as e:
        logger.error(f"Error al eliminar tokens Fitbit para usuario {user_id}: {e}", exc_info=True)
        return False

# --- Funciones de Utilidad para la API de Fitbit ---

def refresh_fitbit_tokens(refresh_token, user_id):
    """Refresca los tokens de Fitbit y guarda los nuevos."""
    auth_string = f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    try:
        logger.info(f"Intentando refrescar token Fitbit para usuario {user_id}")
        response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data, timeout=15)
        if response.status_code == 200:
            new_tokens = response.json()
            logger.info(f"Refresco de token exitoso para usuario {user_id}")
            if save_fitbit_tokens_to_db(user_id, FITBIT_CLIENT_ID, new_tokens):
                logger.info(f"Tokens refrescados guardados para usuario {user_id}")
                return new_tokens
            else:
                logger.error(f"FALLO al guardar tokens refrescados para usuario {user_id}")
                return None
        else:
            logger.error(f"Error al refrescar token Fitbit para usuario {user_id}: {response.status_code}, {response.text[:200]}")
            if response.status_code in [400, 401]:
                 logger.warning(f"Refresh token inválido para usuario {user_id}. Eliminando tokens.")
                 delete_fitbit_tokens(user_id)
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red/timeout durante refresco token Fitbit para usuario {user_id}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error inesperado durante refresco token Fitbit para usuario {user_id}: {e}")
        return None

def get_valid_access_token(user_id):
    """Obtiene un access_token válido, refrescándolo si es necesario."""
    token_data = get_fitbit_tokens_from_db(user_id)
    if not token_data or not token_data.get('is_connected'): return None

    expires_at_str = token_data.get('expires_at')
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    if not expires_at_str or not access_token or not refresh_token: return None

    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        now_aware = datetime.now(expires_at.tzinfo)
    except ValueError:
         logger.error(f"Error al parsear timestamp de expiración '{expires_at_str}' para usuario {user_id}.")
         return None

    if now_aware + timedelta(minutes=5) >= expires_at: # Margen de 5 min
        logger.info(f"Token Fitbit expirado/por expirar para usuario {user_id}. Refrescando...")
        new_tokens = refresh_fitbit_tokens(refresh_token, user_id)
        return new_tokens.get('access_token') if new_tokens else None
    else:
        return access_token

# --- Función para autenticar con token en URL (NUEVA) ---
async def authenticate_with_token_param(request: Request, user = None):
    """
    Autenticar con token JWT en parámetro de URL si el middleware no autenticó.
    
    Esta función permite el flujo OAuth de Fitbit incluso cuando 
    el navegador no puede incluir headers de autorización.
    """
    # Si el middleware ya autenticó al usuario, usarlo directamente
    if user:
        return user
    
    # Intentar autenticar con el token de la URL
    token = request.query_params.get("token")
    if not token:
        return None
    
    try:
        # Verificar el token
        payload = verify_token(token)
        if not payload or not payload.get("sub"):
            logger.warning(f"Token inválido en URL para {request.url}")
            return None
            
        # Obtener datos del usuario
        user_id = payload.get("sub")
        user = get_user_by_id(int(user_id))
        
        if user:
            logger.info(f"Usuario autenticado vía token URL: ID={user_id}")
            return user
        else:
            logger.warning(f"Usuario no encontrado con ID={user_id} (de token URL)")
            return None
    except Exception as e:
        logger.error(f"Error verificando token URL: {str(e)}")
        return None

# --- Endpoints de la API de Fitbit ---

@router.get('/connect', name="fitbit_connect")
async def connect_fitbit_start(
    request: Request, 
    token: str = Query(None, description="Token JWT para autenticación alternativa"),
    user = Depends(get_current_user)
):
    """
    Inicia el flujo OAuth de Fitbit.
    Acepta autenticación tanto por header como por parámetro de query 'token'.
    """
    # Si no hay usuario autenticado por el middleware, intentar autenticar con el token en URL
    if not user and token:
        try:
            # Verificar el token de la URL
            payload = verify_token(token)
            if payload and payload.get("sub"):
                # Buscar usuario por ID
                user_id = int(payload.get("sub"))
                user = get_user_by_id(user_id)
                logger.info(f"Usuario ID={user_id} autenticado vía token en URL")
        except Exception as e:
            logger.error(f"Error verificando token JWT en URL: {e}")
    
    # Verificar que tengamos un usuario válido
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = str(user['id'])
    state = secrets.token_urlsafe(16)

    auth_params = {
        "response_type": "code",
        "client_id": FITBIT_CLIENT_ID,
        "redirect_uri": FITBIT_REDIRECT_URI,
        "scope": "activity heartrate location nutrition profile settings sleep weight",
        "state": state,
    }
    fitbit_auth_full_url = f"{FITBIT_AUTH_URL}?{urlencode(auth_params)}"

    response = RedirectResponse(url=fitbit_auth_full_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # Establecer cookies para state y user_id pendiente
    secure_cookie = request.url.scheme == "https"
    max_age_seconds = 600  # 10 min

    response.set_cookie(key="fitbit_oauth_state", value=state, httponly=True, samesite="lax", secure=secure_cookie, max_age=max_age_seconds, path="/")
    response.set_cookie(key="fitbit_user_id_pending", value=user_id, httponly=True, samesite="lax", secure=secure_cookie, max_age=max_age_seconds, path="/")

    logger.info(f"Redirigiendo usuario {user_id} a Fitbit. State: {state[:5]}...")
    return response

@router.get('/connect-url', name="fitbit_connect_url")
async def get_fitbit_connect_url(request: Request, user = Depends(get_current_user)):
    """Devuelve la URL de conexión a Fitbit sin redirigir."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = str(user['id'])
    state = secrets.token_urlsafe(16)

    auth_params = {
        "response_type": "code",
        "client_id": FITBIT_CLIENT_ID,
        "redirect_uri": FITBIT_REDIRECT_URI,
        "scope": "activity heartrate location nutrition profile settings sleep weight",
        "state": state,
    }
    fitbit_auth_full_url = f"{FITBIT_AUTH_URL}?{urlencode(auth_params)}"

    # Deberíamos almacenar el estado para validación posterior
    # Asumimos que la cookie no estará disponible si usamos esta estrategia
    
    return JSONResponse(content={"success": True, "redirect_url": fitbit_auth_full_url})

@router.get('/callback', name="fitbit_callback")
async def fitbit_callback_handler(request: Request, code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    """Callback de Fitbit. Valida estado, intercambia código, guarda tokens y redirige al frontend."""
    logger.info(f"Callback Fitbit. Code: {'Sí' if code else 'No'}, State: {state[:5] if state else 'N/A'}..., Error: {error}")

    expected_state = request.cookies.get('fitbit_oauth_state')
    user_id_pending = request.cookies.get('fitbit_user_id_pending')

    # Construir URLs de redirección al frontend
    base_url = FRONTEND_APP_URL.rstrip('/')
    success_path = FRONTEND_FITBIT_SUCCESS_PATH.lstrip('/')
    error_path = FRONTEND_FITBIT_ERROR_PATH.lstrip('/')
    success_redirect_url = f"{base_url}/{success_path}"
    error_redirect_url_base = f"{base_url}/{error_path}"

    # Helper para redirigir al frontend
    def create_frontend_redirect(base_url, message=None, is_error=True):
        final_url = base_url
        if message:
            separator = '&' if '?' in final_url else '?'
            final_url += f"{separator}{urlencode({'message': message})}"
        response = RedirectResponse(final_url, status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie("fitbit_oauth_state", path="/", httponly=True, samesite="lax")
        response.delete_cookie("fitbit_user_id_pending", path="/", httponly=True, samesite="lax")
        logger.info(f"Redirigiendo a Frontend: {final_url}. Error: {is_error}")
        return response

    # Validaciones
    if error:
        logger.error(f"Error explícito de Fitbit: {error}")
        return create_frontend_redirect(error_redirect_url_base, f"Fitbit denegó acceso: {error}")
    if not state or state != expected_state:
        logger.error(f"Error de State CSRF. Esperado: {expected_state[:5] if expected_state else 'N/A'}..., Recibido: {state[:5] if state else 'N/A'}...")
        return create_frontend_redirect(error_redirect_url_base, "Error de seguridad. Intenta conectar de nuevo.")
    if not code:
        logger.error("No se recibió código de autorización de Fitbit.")
        return create_frontend_redirect(error_redirect_url_base, "No se recibió código de autorización.")
    if not user_id_pending:
        logger.error("Error crítico: Falta cookie 'fitbit_user_id_pending'.")
        return create_frontend_redirect(error_redirect_url_base, "Error interno: No se pudo identificar al usuario.")

    # Intercambiar código por tokens
    auth_string = f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"client_id": FITBIT_CLIENT_ID, "grant_type": "authorization_code", "code": code, "redirect_uri": FITBIT_REDIRECT_URI}

    try:
        logger.info(f"Intercambiando código Fitbit por tokens para usuario pendiente: {user_id_pending}")
        token_response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data, timeout=20)

        if token_response.status_code != 200:
            logger.error(f"Error al intercambiar código Fitbit ({token_response.status_code}): {token_response.text[:200]}")
            return create_frontend_redirect(error_redirect_url_base, f"Error ({token_response.status_code}) al finalizar conexión.")

        tokens = token_response.json()
        logger.info(f"Tokens Fitbit recibidos para usuario pendiente: {user_id_pending}")

        # Guardar Tokens
        if save_fitbit_tokens_to_db(user_id_pending, FITBIT_CLIENT_ID, tokens):
            logger.info(f"Tokens Fitbit guardados para usuario: {user_id_pending}")
            return create_frontend_redirect(success_redirect_url, message="¡Fitbit conectado!", is_error=False)
        else:
            logger.error(f"FALLO Crítico al guardar tokens Fitbit para usuario {user_id_pending}.")
            return create_frontend_redirect(error_redirect_url_base, "Error interno al guardar conexión Fitbit.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red/timeout en callback Fitbit para usuario {user_id_pending}: {e}")
        return create_frontend_redirect(error_redirect_url_base, "Error de red/timeout al conectar con Fitbit.")
    except Exception as e:
        logger.exception(f"Error inesperado en callback Fitbit para usuario {user_id_pending}: {e}")
        return create_frontend_redirect(error_redirect_url_base, "Error inesperado durante conexión Fitbit.")

@router.get("/data", name="fitbit_data", response_class=JSONResponse)
async def get_fitbit_data_api(
    request: Request,
    data_type: str = Query(..., description="Tipo de dato a obtener",
                           enum=['profile', 'devices', 'activity_summary', 'sleep_log', 'heart_rate_intraday', 'cardio_score']),
    date: str = Query(None, description="Fecha (YYYY-MM-DD). Por defecto: hoy para la mayoría."),
    detail_level: str = Query(None, description="Detalle para intradía ('1sec', '1min')"),
    user = Depends(get_current_user)
):
    """API: Obtiene datos específicos de Fitbit para el usuario autenticado."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = user['id']

    access_token = get_valid_access_token(user_id)
    if not access_token:
        # Comprobar si debería estar conectado
        is_supposed_to_be_connected = get_fitbit_tokens_from_db(user_id).get("is_connected", False)
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE if is_supposed_to_be_connected else status.HTTP_403_FORBIDDEN
        message = "Error al acceder a Fitbit (token inválido/expirado)." if status_code == 503 else "Usuario no conectado a Fitbit."
        raise HTTPException(status_code=status_code, detail=message, headers={"X-Fitbit-Connected": "false"})

    # Construir URL y llamar a Fitbit API
    headers = {"Authorization": f"Bearer {access_token}", "Accept-Language": "es_ES"}
    base_fitbit_api_url = "https://api.fitbit.com"
    api_path = None
    target_date = date if date else datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    try:
        # Mapeo de data_type a path
        if data_type == 'profile': api_path = "/1/user/-/profile.json"
        elif data_type == 'devices': api_path = "/1/user/-/devices.json"
        elif data_type == 'activity_summary': api_path = f"/1/user/-/activities/date/{target_date}.json"
        elif data_type == 'sleep_log': api_path = f"/1.2/user/-/sleep/date/{target_date}.json"
        elif data_type == 'cardio_score': api_path = f"/1/user/-/cardioscore/date/{date if date else yesterday}.json"
        elif data_type == 'heart_rate_intraday':
             detail = detail_level if detail_level in ['1sec', '1min'] else '1min'
             api_path = f"/1/user/-/activities/heart/date/{target_date}/1d/{detail}.json"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tipo de dato Fitbit '{data_type}' no soportado.")

        fitbit_api_url = f"{base_fitbit_api_url}{api_path}"
        logger.info(f"Solicitando datos Fitbit: {data_type} para usuario {user_id}")

        response = requests.get(fitbit_api_url, headers=headers, timeout=20)

        # Procesar respuesta de Fitbit
        if response.status_code == 200:
            return JSONResponse(content={"success": True, "data_type": data_type, "data": response.json(), "is_connected": True})
        elif response.status_code == 401:
             logger.warning(f"Error 401 de Fitbit API para usuario {user_id}.")
             delete_fitbit_tokens(user_id)
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acceso denegado por Fitbit. Vuelve a conectar.", headers={"X-Fitbit-Connected": "false"})
        elif response.status_code == 429:
             logger.warning(f"Error 429 (Rate Limit) de Fitbit API para usuario {user_id}.")
             raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Límite de solicitudes a Fitbit excedido.")
        else:
            logger.error(f"Error {response.status_code} al obtener datos Fitbit ({data_type}) para usuario {user_id}: {response.text[:200]}")
            error_details = response.text[:200]
            try: error_details = json.dumps(response.json().get('errors', error_details))
            except: pass
            raise HTTPException(status_code=response.status_code, detail=f"Error de Fitbit al obtener '{data_type}': {error_details}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red/timeout obteniendo datos Fitbit ({data_type}) para usuario {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Error de red o timeout contactando con Fitbit.")
    except Exception as e:
        logger.exception(f"Error inesperado obteniendo datos Fitbit ({data_type}) para usuario {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno procesando solicitud Fitbit.")

@router.post("/disconnect", name="fitbit_disconnect", response_class=JSONResponse)
async def disconnect_fitbit_api(request: Request, user = Depends(get_current_user)):
    """API: Desconecta la cuenta de Fitbit eliminando los tokens."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = user['id']
    logger.info(f"Intentando desconectar Fitbit para usuario: {user_id}")

    # Opcional: Revocar token en Fitbit antes de borrarlo localmente

    if delete_fitbit_tokens(user_id):
        return JSONResponse(content={"success": True, "message": "Cuenta de Fitbit desconectada."})
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al intentar desconectar la cuenta de Fitbit.")