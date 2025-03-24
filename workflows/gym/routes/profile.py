import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
import json
import psycopg2
import requests
import base64
import secrets
from datetime import datetime, timedelta
from config import DB_CONFIG

# Crear blueprint
profile_bp = Blueprint('profile', __name__)

# Endpoints de Fitbit
FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_PROFILE_URL = "https://api.fitbit.com/1/user/-/profile.json"

# Obtener credenciales de Fitbit desde variables de entorno
def get_fitbit_credentials():
    """Obtiene las credenciales de Fitbit desde variables de entorno."""
    return {
        'client_id': os.getenv('FITBIT_CLIENT_ID', '23Q3W4'),
        'client_secret': os.getenv('FITBIT_CLIENT_SECRET', '8eff8678e33a3443676fadc6c3f726c4'),
        'redirect_uri': os.getenv('FITBIT_REDIRECT_URI', 'http://localhost:5050/fitbit-callback')
    }

@profile_bp.route('/profile', methods=['GET'])
def profile():
    """Página del perfil del usuario."""
    # Obtener user_id de la URL o usar valor predeterminado
    user_id = request.args.get('user_id', "3892415")
    
    # Comprobar si el usuario tiene tokens de Fitbit asociados
    fitbit_data = get_fitbit_tokens(user_id)
    is_connected = fitbit_data.get('is_connected', False)
    
    # Si está conectado, obtener datos del perfil de Fitbit
    fitbit_profile = None
    health_metrics = None
    
    if is_connected:
        # Intentar obtener perfil de Fitbit con el token actual
        access_token = fitbit_data.get('access_token')
        
        # Verificar si el token ha expirado
        expires_at = fitbit_data.get('expires_at')
        if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
            # Refrescar token
            refresh_token = fitbit_data.get('refresh_token')
            
            new_tokens = refresh_fitbit_tokens(refresh_token)
            if new_tokens:
                access_token = new_tokens.get('access_token')
        
        # Obtener datos usando el token
        fitbit_profile = get_fitbit_profile(access_token)
        health_metrics = get_health_metrics(access_token)
    
    return render_template('profile.html', 
                          user_id=user_id,
                          is_connected=is_connected,
                          fitbit_profile=fitbit_profile,
                          health_metrics=health_metrics)

@profile_bp.route('/connect-fitbit', methods=['GET'])
def connect_fitbit():
    """Inicia el proceso de conexión con Fitbit."""
    # Obtener user_id
    user_id = request.args.get('user_id', "3892415")
    
    # Obtener credenciales
    credentials = get_fitbit_credentials()
    
    # Generar state para seguridad
    state = secrets.token_urlsafe(16)
    
    # Guardar en sesión
    session['oauth_state'] = state
    session['user_id'] = user_id
    
    # Construir URL de redirección
    redirect_uri = request.host_url.rstrip('/') + url_for('profile.fitbit_callback')
    
    # Construir URL de autorización
    auth_url = (
        f"{FITBIT_AUTH_URL}?"
        f"response_type=code&"
        f"client_id={credentials['client_id']}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20weight&"
        f"state={state}"
    )
    
    return redirect(auth_url)

@profile_bp.route('/fitbit-callback', methods=['GET'])
def fitbit_callback():
    """Callback para recibir el código de autorización de Fitbit."""
    # Obtener parámetros
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    # Recuperar datos de sesión
    expected_state = session.get('oauth_state')
    user_id = session.get('user_id', "3892415")
    
    # Limpiar sesión
    if 'oauth_state' in session:
        session.pop('oauth_state')
    if 'user_id' in session:
        session.pop('user_id')
    
    # Verificar errores
    if error:
        return render_template('profile_callback.html', 
                              success=False, 
                              message=f"Error durante la autorización: {error}")
    
    # Verificar state para seguridad
    if expected_state and state != expected_state:
        return render_template('profile_callback.html', 
                              success=False, 
                              message="Error de seguridad: State inválido")
    
    if not code:
        return render_template('profile_callback.html', 
                              success=False, 
                              message="No se recibió código de autorización")
    
    # Obtener URL de redirección exacta
    redirect_uri = request.host_url.rstrip('/') + url_for('profile.fitbit_callback')
    
    # Intercambiar código por tokens
    tokens = exchange_code_for_tokens(code, redirect_uri)
    
    if not tokens:
        return render_template('profile_callback.html', 
                              success=False, 
                              message="Error al obtener tokens de acceso")
    
    # Guardar tokens en base de datos
    credentials = get_fitbit_credentials()
    success = save_fitbit_tokens(user_id, credentials['client_id'], tokens)
    
    return render_template('profile_callback.html', 
                          success=success, 
                          message="Cuenta de Fitbit conectada correctamente" if success else "Error al guardar tokens")

@profile_bp.route('/api/fitbit-data', methods=['GET'])
def get_fitbit_data():
    """API para obtener datos de Fitbit."""
    user_id = request.args.get('user_id', "3892415")
    data_type = request.args.get('type', 'profile')  # profile, activity, sleep, etc.
    
    # Obtener tokens de Fitbit
    fitbit_data = get_fitbit_tokens(user_id)
    
    if not fitbit_data.get('is_connected', False):
        return jsonify({
            "success": False,
            "message": "Usuario no conectado a Fitbit"
        })
    
    # Verificar si el token ha expirado
    access_token = fitbit_data.get('access_token')
    expires_at = fitbit_data.get('expires_at')
    
    if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
        # Refrescar token
        refresh_token = fitbit_data.get('refresh_token')
        
        new_tokens = refresh_fitbit_tokens(refresh_token)
        if new_tokens:
            access_token = new_tokens.get('access_token')
        else:
            return jsonify({
                "success": False,
                "message": "Error al refrescar token de Fitbit"
            })
    
    # Obtener datos según el tipo solicitado
    if data_type == 'profile':
        data = get_fitbit_profile(access_token)
    elif data_type == 'activity':
        data = get_fitbit_activity(access_token)
    elif data_type == 'sleep':
        data = get_fitbit_sleep(access_token)
    else:
        data = {"message": "Tipo de datos no soportado"}
    
    return jsonify({
        "success": True,
        "data": data
    })

@profile_bp.route('/disconnect-fitbit', methods=['POST'])
def disconnect_fitbit():
    """Desconectar cuenta de Fitbit."""
    user_id = request.form.get('user_id', "3892415")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            "DELETE FROM fitbit_tokens WHERE user_id = %s",
            (user_id,)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return redirect(url_for('profile.profile', user_id=user_id))
    except Exception as e:
        print(f"Error al desconectar cuenta: {e}")
        return render_template('profile_callback.html', 
                              success=False, 
                              message=f"Error al desconectar cuenta: {str(e)}")

# Funciones utilitarias
def get_fitbit_tokens(user_id):
    """Obtiene los tokens de Fitbit para un usuario."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT client_id, access_token, refresh_token, expires_at FROM fitbit_tokens WHERE user_id = %s",
            (user_id,)
        )
        
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
        # Obtener credenciales
        credentials = get_fitbit_credentials()
        
        # Crear encabezado de autorización
        auth_string = f"{credentials['client_id']}:{credentials['client_secret']}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "client_id": credentials['client_id'],
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
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
        # Obtener credenciales
        credentials = get_fitbit_credentials()
        
        # Crear encabezado de autorización
        auth_string = f"{credentials['client_id']}:{credentials['client_secret']}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            
            # Guardar nuevos tokens
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