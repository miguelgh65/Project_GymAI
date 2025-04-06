# Imports (Python Standard Library)
import os
import sys
import base64
import json
import secrets
import logging # Añadido para logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

# --- Ajuste de Ruta del Proyecto (Revisar según tu estructura) ---
# Añade el directorio raíz si es necesario para encontrar 'config', 'services', etc.
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")) # Ejemplo
# if project_root not in sys.path:
#     sys.path.append(project_root)
#     logging.info(f"Añadido {project_root} a Python path")

# Imports (External Libraries)
import psycopg2
import requests
from dotenv import load_dotenv
from fastapi import (APIRouter, Depends, Form, HTTPException, Query, Request,
                     Response, status) # Añadido status
# Eliminado HTMLResponse y Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates # Eliminado

# --- Carga de Variables de Entorno ---
load_dotenv() # Carga desde .env en la raíz o directorios padre

# --- Importaciones del Proyecto (¡¡¡DEBES AJUSTAR ESTAS RUTAS!!!) ---
try:
    # Asumiendo que config.py y middlewares.py están accesibles
    from config import DB_CONFIG # Asegúrate que DB_CONFIG se carga bien
    # Asumiendo que tu middleware está en workflows.gym.middlewares
    from back_end.gym.middlewares import get_current_user # ¡¡¡Ajusta esta ruta!!!

    # --- Placeholder para get_current_user (si no puedes importarlo directamente) ---
    # async def get_current_user(request: Request): # Placeholder
    #     user_id = request.cookies.get("user_id")
    #     if user_id:
    #         try:
    #             # Simula búsqueda de usuario (reemplaza con tu lógica real)
    #             return {"id": int(user_id), "google_id": f"google_{user_id}", "email": "test@example.com"}
    #         except ValueError: return None
    #     return None
    # --- Fin Placeholder ---

except ImportError as e:
    logging.critical(f"Error Crítico: No se pudieron importar módulos esenciales: {e}. Revisa las rutas.")
    # Podrías querer que la aplicación no inicie si faltan dependencias clave
    sys.exit(f"Error de importación: {e}")

# --- Configuración de Logging Básico ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Router de FastAPI ---
router = APIRouter(
    prefix="/api/fitbit", # Prefijo para todas las rutas de Fitbit
    tags=["fitbit"],      # Etiqueta para Swagger UI
)

# --- Configuración Leída Estrictamente desde el Entorno ---

# Fitbit Credentials & URLs (Sin valores por defecto para secretos)
FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID')
FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET') # ¡Sin valor predeterminado!
FITBIT_REDIRECT_URI = os.getenv('FITBIT_REDIRECT_URI') # URL de tu endpoint /api/fitbit/callback
FITBIT_AUTH_URL = os.getenv('FITBIT_AUTH_URL')
FITBIT_TOKEN_URL = os.getenv('FITBIT_TOKEN_URL')
FITBIT_PROFILE_URL = os.getenv('FITBIT_PROFILE_URL')

# URLs del Frontend (Cargadas desde el entorno)
FRONTEND_APP_URL = os.getenv('FRONTEND_APP_URL', 'http://localhost:3000') # URL base de tu app React
FRONTEND_FITBIT_SUCCESS_PATH = os.getenv('FRONTEND_FITBIT_SUCCESS_PATH', '/profile?fitbit_status=success')
FRONTEND_FITBIT_ERROR_PATH = os.getenv('FRONTEND_FITBIT_ERROR_PATH', '/profile?fitbit_status=error')

# --- Verificación de Variables Esenciales de Fitbit ---
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
    # Lanza un error si faltan variables críticas al iniciar la aplicación
    raise EnvironmentError(f"Error Crítico: Faltan variables de entorno esenciales para Fitbit: {', '.join(missing_vars)}. Verifica tu archivo .env.")

# --- Funciones de Utilidad para la Base de Datos de Fitbit (Reutilizadas) ---

def _execute_db_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Función auxiliar genérica para ejecutar consultas a la BD."""
    conn = None
    cur = None
    result = None
    try:
        conn = psycopg2.connect(**DB_CONFIG) # Usa DB_CONFIG importado
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
        logging.error(f"Error de base de datos: {db_err}", exc_info=True)
        if conn: conn.rollback()
        raise # Relanzar para manejo específico o error 500 genérico
    except Exception as e:
        logging.error(f"Error inesperado en la base de datos: {e}", exc_info=True)
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return result

def get_fitbit_tokens_from_db(user_id):
    """Obtiene los tokens de Fitbit para un user_id específico desde la BD."""
    query = "SELECT client_id, access_token, refresh_token, expires_at FROM fitbit_tokens WHERE user_id = %s"
    try:
        # Asume que user_id en la tabla es VARCHAR, ajusta si es INTEGER
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
        logging.error(f"Error al obtener tokens Fitbit para usuario {user_id}: {e}")
        return {"is_connected": False, "error": "Error de base de datos"}

def save_fitbit_tokens_to_db(user_id, client_id, tokens):
    """Guarda o actualiza los tokens de Fitbit en la base de datos usando UPSERT."""
    expires_in = tokens.get('expires_in', 28800)
    expires_at = datetime.now() + timedelta(seconds=expires_in) # Considerar UTC: datetime.utcnow()
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    user_id_str = str(user_id) # Asegurar tipo string si la columna es VARCHAR

    # Crear tabla si no existe (Idealmente manejado por migraciones)
    create_table_query = """
        CREATE TABLE IF NOT EXISTS fitbit_tokens (
            id SERIAL PRIMARY KEY, user_id VARCHAR(255) NOT NULL UNIQUE, client_id VARCHAR(255) NOT NULL,
            access_token TEXT NOT NULL, refresh_token TEXT NOT NULL, expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- Usar TIMESTAMPTZ
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        ); CREATE INDEX IF NOT EXISTS idx_fitbit_user_id ON fitbit_tokens(user_id);
    """
    try: _execute_db_query(create_table_query, commit=True)
    except Exception as e:
        if "already exists" not in str(e): logging.warning(f"Error al intentar crear tabla fitbit_tokens: {e}")

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
        if success: logging.info(f"Tokens Fitbit guardados/actualizados para usuario {user_id_str}")
        return success
    except Exception as e:
        logging.error(f"Error al guardar tokens Fitbit para usuario {user_id_str}: {e}", exc_info=True)
        return False

def delete_fitbit_tokens(user_id):
    """Elimina los tokens de Fitbit para un usuario de la BD."""
    query = "DELETE FROM fitbit_tokens WHERE user_id = %s"
    try:
        success = _execute_db_query(query, (str(user_id),), commit=True)
        if success: logging.info(f"Tokens Fitbit eliminados para usuario {user_id}")
        return success
    except Exception as e:
        logging.error(f"Error al eliminar tokens Fitbit para usuario {user_id}: {e}", exc_info=True)
        return False

# --- Funciones de Utilidad para la API de Fitbit (Reutilizadas) ---

def refresh_fitbit_tokens(refresh_token, user_id):
    """Refresca los tokens de Fitbit y guarda los nuevos."""
    auth_string = f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    try:
        logging.info(f"Intentando refrescar token Fitbit para usuario {user_id}")
        response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data, timeout=15)
        if response.status_code == 200:
            new_tokens = response.json()
            logging.info(f"Refresco de token exitoso para usuario {user_id}")
            if save_fitbit_tokens_to_db(user_id, FITBIT_CLIENT_ID, new_tokens):
                logging.info(f"Tokens refrescados guardados para usuario {user_id}")
                return new_tokens
            else:
                logging.error(f"FALLO al guardar tokens refrescados para usuario {user_id}")
                return None
        else:
            logging.error(f"Error al refrescar token Fitbit para usuario {user_id}: {response.status_code}, {response.text[:200]}")
            if response.status_code in [400, 401]:
                 logging.warning(f"Refresh token inválido para usuario {user_id}. Eliminando tokens.")
                 delete_fitbit_tokens(user_id)
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de red/timeout durante refresco token Fitbit para usuario {user_id}: {e}")
        return None
    except Exception as e:
        logging.exception(f"Error inesperado durante refresco token Fitbit para usuario {user_id}: {e}")
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
        # Asumiendo que expires_at se guarda como TIMESTAMPTZ (con zona horaria)
        expires_at = datetime.fromisoformat(expires_at_str)
        # Compara con la hora actual consciente de la zona horaria
        now_aware = datetime.now(expires_at.tzinfo)
    except ValueError:
         logging.error(f"Error al parsear timestamp de expiración '{expires_at_str}' para usuario {user_id}.")
         return None

    if now_aware + timedelta(minutes=5) >= expires_at: # Margen de 5 min
        logging.info(f"Token Fitbit expirado/por expirar para usuario {user_id}. Refrescando...")
        new_tokens = refresh_fitbit_tokens(refresh_token, user_id)
        return new_tokens.get('access_token') if new_tokens else None
    else:
        return access_token

# --- Endpoints de la API de Fitbit ---

# Endpoint /profile eliminado

@router.get('/connect', name="fitbit_connect")
async def connect_fitbit_start(request: Request, user = Depends(get_current_user)):
    """Inicia el flujo OAuth de Fitbit. Requiere usuario autenticado."""
    if not user or not user.get('id'):
        # Ahora que es una API, devolver error JSON claro
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = str(user['id']) # Usar ID interno
    state = secrets.token_urlsafe(16)

    auth_params = {
        "response_type": "code",
        "client_id": FITBIT_CLIENT_ID,
        "redirect_uri": FITBIT_REDIRECT_URI, # Usar la URI de env
        "scope": "activity heartrate location nutrition profile settings sleep weight", # Alcances deseados
        "state": state,
    }
    fitbit_auth_full_url = f"{FITBIT_AUTH_URL}?{urlencode(auth_params)}"

    response = RedirectResponse(url=fitbit_auth_full_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # Establecer cookies para state y user_id pendiente
    secure_cookie = request.url.scheme == "https"
    max_age_seconds = 600 # 10 min

    response.set_cookie(key="fitbit_oauth_state", value=state, httponly=True, samesite="lax", secure=secure_cookie, max_age=max_age_seconds, path="/")
    response.set_cookie(key="fitbit_user_id_pending", value=user_id, httponly=True, samesite="lax", secure=secure_cookie, max_age=max_age_seconds, path="/")

    logging.info(f"Redirigiendo usuario {user_id} a Fitbit. State: {state[:5]}...")
    return response

@router.get('/callback', name="fitbit_callback")
async def fitbit_callback_handler(request: Request, code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    """Callback de Fitbit. Valida estado, intercambia código, guarda tokens y redirige al frontend."""
    logging.info(f"Callback Fitbit. Code: {'Sí' if code else 'No'}, State: {state[:5] if state else 'N/A'}..., Error: {error}")

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
        logging.info(f"Redirigiendo a Frontend: {final_url}. Error: {is_error}")
        return response

    # Validaciones
    if error:
        logging.error(f"Error explícito de Fitbit: {error}")
        return create_frontend_redirect(error_redirect_url_base, f"Fitbit denegó acceso: {error}")
    if not state or state != expected_state:
        logging.error(f"Error de State CSRF. Esperado: {expected_state[:5] if expected_state else 'N/A'}..., Recibido: {state[:5] if state else 'N/A'}...")
        return create_frontend_redirect(error_redirect_url_base, "Error de seguridad. Intenta conectar de nuevo.")
    if not code:
        logging.error("No se recibió código de autorización de Fitbit.")
        return create_frontend_redirect(error_redirect_url_base, "No se recibió código de autorización.")
    if not user_id_pending:
        logging.error("Error crítico: Falta cookie 'fitbit_user_id_pending'.")
        return create_frontend_redirect(error_redirect_url_base, "Error interno: No se pudo identificar al usuario.")

    # Intercambiar código por tokens (Inline para claridad, podría ser helper)
    auth_string = f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"client_id": FITBIT_CLIENT_ID, "grant_type": "authorization_code", "code": code, "redirect_uri": FITBIT_REDIRECT_URI}

    try:
        logging.info(f"Intercambiando código Fitbit por tokens para usuario pendiente: {user_id_pending}")
        token_response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data, timeout=20)

        if token_response.status_code != 200:
            logging.error(f"Error al intercambiar código Fitbit ({token_response.status_code}): {token_response.text[:200]}")
            return create_frontend_redirect(error_redirect_url_base, f"Error ({token_response.status_code}) al finalizar conexión.")

        tokens = token_response.json()
        logging.info(f"Tokens Fitbit recibidos para usuario pendiente: {user_id_pending}")

        # Guardar Tokens
        if save_fitbit_tokens_to_db(user_id_pending, FITBIT_CLIENT_ID, tokens):
            logging.info(f"Tokens Fitbit guardados para usuario: {user_id_pending}")
            return create_frontend_redirect(success_redirect_url, message="¡Fitbit conectado!", is_error=False)
        else:
            logging.error(f"FALLO Crítico al guardar tokens Fitbit para usuario {user_id_pending}.")
            return create_frontend_redirect(error_redirect_url_base, "Error interno al guardar conexión Fitbit.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error de red/timeout en callback Fitbit para usuario {user_id_pending}: {e}")
        return create_frontend_redirect(error_redirect_url_base, "Error de red/timeout al conectar con Fitbit.")
    except Exception as e:
        logging.exception(f"Error inesperado en callback Fitbit para usuario {user_id_pending}: {e}")
        return create_frontend_redirect(error_redirect_url_base, "Error inesperado durante conexión Fitbit.")

# Endpoint /api/fitbit-data renombrado a /data y mejorado
@router.get("/data", name="fitbit_data", response_class=JSONResponse)
async def get_fitbit_data_api(
    request: Request,
    data_type: str = Query(..., description="Tipo de dato a obtener", # Hacerlo requerido
                           enum=['profile', 'devices', 'activity_summary', 'sleep_log', 'heart_rate_intraday', 'cardio_score']), # Enum con tipos soportados
    date: str = Query(None, description="Fecha (YYYY-MM-DD). Por defecto: hoy para la mayoría."),
    # Añadir más query params si son necesarios para ciertos data_type
    detail_level: str = Query(None, description="Detalle para intradía ('1sec', '1min')"),
    user = Depends(get_current_user)
):
    """API: Obtiene datos específicos de Fitbit para el usuario autenticado."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = user['id'] # Usar ID interno

    access_token = get_valid_access_token(user_id) # Maneja refresco
    if not access_token:
        # Comprobar si debería estar conectado
        is_supposed_to_be_connected = get_fitbit_tokens_from_db(user_id).get("is_connected", False)
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE if is_supposed_to_be_connected else status.HTTP_403_FORBIDDEN
        message = "Error al acceder a Fitbit (token inválido/expirado)." if status_code == 503 else "Usuario no conectado a Fitbit."
        raise HTTPException(status_code=status_code, detail=message, headers={"X-Fitbit-Connected": "false"})

    # Construir URL y llamar a Fitbit API (lógica similar a la respuesta anterior completa)
    headers = {"Authorization": f"Bearer {access_token}", "Accept-Language": "es_ES"}
    base_fitbit_api_url = "https://api.fitbit.com"
    api_path = None
    target_date = date if date else datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') # Para datos como cardio

    try:
        # Mapeo de data_type a path (expandir según necesites)
        if data_type == 'profile': api_path = "/1/user/-/profile.json"
        elif data_type == 'devices': api_path = "/1/user/-/devices.json"
        elif data_type == 'activity_summary': api_path = f"/1/user/-/activities/date/{target_date}.json"
        elif data_type == 'sleep_log': api_path = f"/1.2/user/-/sleep/date/{target_date}.json"
        elif data_type == 'cardio_score': api_path = f"/1/user/-/cardioscore/date/{date if date else yesterday}.json" # Usar yesterday por defecto
        elif data_type == 'heart_rate_intraday':
             detail = detail_level if detail_level in ['1sec', '1min'] else '1min'
             api_path = f"/1/user/-/activities/heart/date/{target_date}/1d/{detail}.json" # Simplificado, ajustar si necesitas time range
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tipo de dato Fitbit '{data_type}' no soportado.")

        fitbit_api_url = f"{base_fitbit_api_url}{api_path}"
        logging.info(f"Solicitando datos Fitbit: {data_type} para usuario {user_id}")

        response = requests.get(fitbit_api_url, headers=headers, timeout=20)

        # Procesar respuesta de Fitbit
        if response.status_code == 200:
            return JSONResponse(content={"success": True, "data_type": data_type, "data": response.json(), "is_connected": True})
        elif response.status_code == 401:
             logging.warning(f"Error 401 de Fitbit API para usuario {user_id}.")
             delete_fitbit_tokens(user_id)
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acceso denegado por Fitbit. Vuelve a conectar.", headers={"X-Fitbit-Connected": "false"})
        elif response.status_code == 429:
             logging.warning(f"Error 429 (Rate Limit) de Fitbit API para usuario {user_id}.")
             raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Límite de solicitudes a Fitbit excedido.")
        else:
            logging.error(f"Error {response.status_code} al obtener datos Fitbit ({data_type}) para usuario {user_id}: {response.text[:200]}")
            error_details = response.text[:200]
            try: error_details = json.dumps(response.json().get('errors', error_details)) # Intenta obtener error específico
            except: pass
            raise HTTPException(status_code=response.status_code, detail=f"Error de Fitbit al obtener '{data_type}': {error_details}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error de red/timeout obteniendo datos Fitbit ({data_type}) para usuario {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Error de red o timeout contactando con Fitbit.")
    except Exception as e:
        logging.exception(f"Error inesperado obteniendo datos Fitbit ({data_type}) para usuario {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno procesando solicitud Fitbit.")


# Endpoint /disconnect-fitbit renombrado a /disconnect
@router.post("/disconnect", name="fitbit_disconnect", response_class=JSONResponse)
async def disconnect_fitbit_api(request: Request, user = Depends(get_current_user)):
    """API: Desconecta la cuenta de Fitbit eliminando los tokens."""
    if not user or not user.get('id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    user_id = user['id'] # Usar ID interno
    logging.info(f"Intentando desconectar Fitbit para usuario: {user_id}")

    # Opcional: Revocar token en Fitbit antes de borrarlo localmente

    if delete_fitbit_tokens(user_id):
        return JSONResponse(content={"success": True, "message": "Cuenta de Fitbit desconectada."})
    else:
        # El error ya debería haberse loggeado
        # Devolver error 500 porque la acción falló en el backend
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al intentar desconectar la cuenta de Fitbit.")