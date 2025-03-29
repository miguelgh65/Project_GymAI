import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Request, HTTPException, Form, Query
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import psycopg2
import requests
import base64
import secrets
from datetime import datetime, timedelta
from config import DB_CONFIG

load_dotenv()
templates = Jinja2Templates(directory="templates")
router = APIRouter()

# Endpoints de Fitbit
FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_PROFILE_URL = "https://api.fitbit.com/1/user/-/profile.json"

def get_fitbit_credentials():
    """Obtiene las credenciales de Fitbit desde variables de entorno."""
    return {
        'client_id': os.getenv('FITBIT_CLIENT_ID', '23Q3W4'),
        'client_secret': os.getenv('FITBIT_CLIENT_SECRET', '8eff8678e33a3443676fadc6c3f726c4'),
        'redirect_uri': os.getenv('FITBIT_REDIRECT_URI', 'http://localhost:5050/fitbit-callback')
    }

@router.get('/profile', response_class=HTMLResponse)
async def profile(request: Request, user_id: str = Query("3892415")):
    """Página del perfil del usuario."""
    # Aquí podrías consultar en la BD para saber si el usuario tiene tokens asociados.
    # Se usará una función get_fitbit_tokens() similar a la implementada en Flask.
    fitbit_data = get_fitbit_tokens(user_id)
    is_connected = fitbit_data.get('is_connected', False)
    fitbit_profile = None
    health_metrics = None

    if is_connected:
        access_token = fitbit_data.get('access_token')
        expires_at = fitbit_data.get('expires_at')
        if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
            refresh_token = fitbit_data.get('refresh_token')
            new_tokens = refresh_fitbit_tokens(refresh_token)
            if new_tokens:
                access_token = new_tokens.get('access_token')
        fitbit_profile = get_fitbit_profile(access_token)
        health_metrics = get_health_metrics(access_token)
    
    return templates.TemplateResponse('profile.html', {
        "request": request,
        "user_id": user_id,
        "is_connected": is_connected,
        "fitbit_profile": fitbit_profile,
        "health_metrics": health_metrics
    })

@router.get('/connect-fitbit')
async def connect_fitbit(request: Request, user_id: str = Query("3892415")):
    """Inicia el proceso de conexión con Fitbit."""
    credentials = get_fitbit_credentials()
    state = secrets.token_urlsafe(16)
    # En FastAPI no existe 'session' como en Flask; para mantener el state podrías usar cookies o algún almacenamiento temporal.
    # Aquí, por simplicidad, redirigimos incluyendo el state en la URL (no es lo ideal para producción).
    redirect_uri = request.url_for('profile_callback')
    auth_url = (
        f"{FITBIT_AUTH_URL}?"
        f"response_type=code&"
        f"client_id={credentials['client_id']}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20weight&"
        f"state={state}"
    )
    return RedirectResponse(auth_url)

@router.get('/fitbit-callback', response_class=HTMLResponse)
async def profile_callback(request: Request, code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    """Callback para recibir el código de autorización de Fitbit."""
    # En ausencia de un sistema de sesiones, se asume que el state es correcto
    if error:
        return templates.TemplateResponse('profile_callback.html', {"request": request, "success": False, "message": f"Error durante la autorización: {error}"})
    if not code:
        return templates.TemplateResponse('profile_callback.html', {"request": request, "success": False, "message": "No se recibió código de autorización"})
    redirect_uri = request.url_for('profile_callback')
    tokens = exchange_code_for_tokens(code, redirect_uri)
    if not tokens:
        return templates.TemplateResponse('profile_callback.html', {"request": request, "success": False, "message": "Error al obtener tokens de acceso"})
    credentials = get_fitbit_credentials()
    # Se asume que user_id se conoce (podrías obtenerlo de otra forma en producción)
    user_id = "3892415"
    success = save_fitbit_tokens(user_id, credentials['client_id'], tokens)
    return templates.TemplateResponse('profile_callback.html', {"request": request, "success": success, "message": "Cuenta de Fitbit conectada correctamente" if success else "Error al guardar tokens"})

@router.get('/api/fitbit-data', response_class=JSONResponse)
async def get_fitbit_data(user_id: str = Query("3892415"), type: str = Query('profile')):
    """API para obtener datos de Fitbit."""
    fitbit_data = get_fitbit_tokens(user_id)
    if not fitbit_data.get('is_connected', False):
        return JSONResponse(content={"success": False, "message": "Usuario no conectado a Fitbit"})
    access_token = fitbit_data.get('access_token')
    expires_at = fitbit_data.get('expires_at')
    if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
        refresh_token = fitbit_data.get('refresh_token')
        new_tokens = refresh_fitbit_tokens(refresh_token)
        if new_tokens:
            access_token = new_tokens.get('access_token')
        else:
            return JSONResponse(content={"success": False, "message": "Error al refrescar token de Fitbit"})
    if type == 'profile':
        data = get_fitbit_profile(access_token)
    elif type == 'activity':
        data = get_fitbit_activity(access_token)
    elif type == 'sleep':
        data = get_fitbit_sleep(access_token)
    else:
        data = {"message": "Tipo de datos no soportado"}
    return JSONResponse(content={"success": True, "data": data})

@router.post('/disconnect-fitbit')
async def disconnect_fitbit(user_id: str = Form("3892415")):
    """Desconectar cuenta de Fitbit."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM fitbit_tokens WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return RedirectResponse(url=f"/profile?user_id={user_id}", status_code=302)
    except Exception as e:
        return templates.TemplateResponse('profile_callback.html', {"request": request, "success": False, "message": f"Error al desconectar cuenta: {str(e)}"})

# Funciones utilitarias

def get_fitbit_tokens(user_id):
    """Obtiene los tokens de Fitbit para un usuario."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT client_id, access_token, refresh_token, expires_at FROM fitbit_tokens WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            return {
                "is_connected": True,
                "client_id": result[0],
                "access_token": result[1],
                "refresh_token": result[2],
                "expires_at": result[3].isoformat()
            }
        else:
            return {"is_connected": False}
    except Exception as e:
        print(f"Error al obtener tokens de Fitbit: {e}")
        return {"is_connected": False, "error": str(e)}

def exchange_code_for_tokens(code, redirect_uri):
    """Intercambia el código de autorización por tokens."""
    try:
        credentials = get_fitbit_credentials()
        auth_string = f"{credentials['client_id']}:{credentials['client_secret']}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"client_id": credentials['client_id'], "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
        print(f"Enviando solicitud a {FITBIT_TOKEN_URL} con code={code[:10]}... (truncado)")
        response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al intercambiar código: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error en solicitud de tokens: {e}")
        return None

def refresh_fitbit_tokens(refresh_token):
    """Refresca los tokens de Fitbit."""
    try:
        credentials = get_fitbit_credentials()
        auth_string = f"{credentials['client_id']}:{credentials['client_secret']}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data)
        if response.status_code == 200:
            tokens = response.json()
            user_id = get_user_id_by_refresh_token(refresh_token)
            if user_id:
                save_fitbit_tokens(user_id, credentials['client_id'], tokens)
            return tokens
        else:
            print(f"Error al refrescar tokens: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error en solicitud de refresh: {e}")
        return None

def save_fitbit_tokens(user_id, client_id, tokens):
    """Guarda los tokens de Fitbit en la base de datos."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Calcular cuando expira el token
        expires_in = tokens.get('expires_in', 28800)  # 8 horas por defecto
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # Eliminar tokens anteriores
        cur.execute(
            "DELETE FROM fitbit_tokens WHERE user_id = %s",
            (user_id,)
        )
        
        # Insertar nuevos tokens
        cur.execute(
            """
            INSERT INTO fitbit_tokens 
            (user_id, client_id, access_token, refresh_token, expires_at) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id, 
                client_id, 
                tokens.get('access_token'), 
                tokens.get('refresh_token'),
                expires_at
            )
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error al guardar tokens: {e}")
        return False

def get_user_id_by_refresh_token(refresh_token):
    """Obtiene el user_id asociado a un refresh_token."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT user_id FROM fitbit_tokens WHERE refresh_token = %s",
            (refresh_token,)
        )
        
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error al obtener user_id por refresh_token: {e}")
        return None

def get_fitbit_profile(access_token):
    """Obtiene el perfil de usuario de Fitbit."""
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(FITBIT_PROFILE_URL, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al obtener perfil: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error en solicitud de perfil: {e}")
        return None

def get_fitbit_activity(access_token):
    """Obtiene los datos de actividad de Fitbit."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://api.fitbit.com/1/user/-/activities/date/{today}.json"
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al obtener actividad: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error en solicitud de actividad: {e}")
        return None

def get_fitbit_sleep(access_token):
    """Obtiene los datos de sueño de Fitbit."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{today}.json"
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al obtener sueño: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error en solicitud de sueño: {e}")
        return None

def get_health_metrics(access_token):
    """Obtiene métricas de salud adicionales de Fitbit."""
    metrics = {}
    
    # Obtener fecha de ayer (más probable que tenga datos completos)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        # Obtener datos de frecuencia cardíaca
        url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{yesterday}/1d.json"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            heart_data = response.json()
            metrics['heart_rate'] = heart_data.get('activities-heart', [{}])[0].get('value', {})
        
        # Obtener datos de sueño
        url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{yesterday}.json"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            sleep_data = response.json()
            metrics['sleep'] = sleep_data.get('summary', {})
        
        # Intentar obtener VO2 Max si está disponible
        url = f"https://api.fitbit.com/1/user/-/cardioscore/date/{yesterday}.json"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            cardio_data = response.json()
            metrics['cardio_score'] = cardio_data.get('cardioScore', [{}])[0] if cardio_data.get('cardioScore') else {}
        
        return metrics
    except Exception as e:
        print(f"Error al obtener métricas de salud: {e}")
        return {}