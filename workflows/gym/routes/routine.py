import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Request, Query, HTTPException, Depends, Form, Response
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import psycopg2
import requests
import base64
import secrets
from datetime import datetime, timedelta
from services.database import get_routine, save_routine, get_today_routine
from workflows.gym.middlewares import get_current_user
# Add this import for DB_CONFIG
from config import DB_CONFIG

# Make sure to load environment variables
load_dotenv()
# Use absolute path for templates
templates = Jinja2Templates(directory="/app/workflows/gym/templates")
router = APIRouter()

def get_fitbit_credentials():
    """
    Load Fitbit credentials from environment variables.
    """
    # Print all environment variables to debug
    print("Loading Fitbit credentials from environment variables")
    print(f"FITBIT_CLIENT_ID: {os.getenv('FITBIT_CLIENT_ID')}")
    print(f"FITBIT_REDIRECT_URI: {os.getenv('FITBIT_REDIRECT_URI')}")
    print(f"FITBIT_AUTH_URL: {os.getenv('FITBIT_AUTH_URL')}")
    
    return {
        'client_id': os.getenv('FITBIT_CLIENT_ID'),
        'client_secret': os.getenv('FITBIT_CLIENT_SECRET'),
        'redirect_uri': os.getenv('FITBIT_REDIRECT_URI'),
        'auth_url': os.getenv('FITBIT_AUTH_URL'),
        'token_url': os.getenv('FITBIT_TOKEN_URL'),
        'profile_url': os.getenv('FITBIT_PROFILE_URL')
    }

@router.get("/rutina_hoy", response_class=HTMLResponse)
async def rutina_hoy(request: Request, format: str = Query(None), user = Depends(get_current_user)):
    """Página de rutina del día."""
    # Asegurar que tenemos un usuario autenticado
    if not user or not user.get('google_id'):
        if format == "json":
            return JSONResponse(content={
                "success": False,
                "message": "Usuario no autenticado o sin ID válido."
            }, status_code=401)
        return templates.TemplateResponse("rutina_hoy.html", {
            "request": request, 
            "user": user,
            "error": "Debes iniciar sesión para ver tu rutina."
        })
    
    # Usar exclusivamente el ID de Google
    user_id = user['google_id']
    
    # Check if the request is for JSON format
    if format == "json":
        result = get_today_routine(user_id)
        return JSONResponse(content=result)
    
    # Return HTML response
    return templates.TemplateResponse("rutina_hoy.html", {"request": request, "user": user})

@router.get("/rutina", response_class=HTMLResponse)
async def rutina(request: Request, format: str = Query(None), user = Depends(get_current_user)):
    """Página de configuración de rutina."""
    # Asegurar que tenemos un usuario autenticado
    if not user or not user.get('google_id'):
        if format == "json":
            return JSONResponse(content={
                "success": False,
                "message": "Usuario no autenticado o sin ID válido."
            }, status_code=401)
        return templates.TemplateResponse("rutina.html", {
            "request": request, 
            "user": user,
            "error": "Debes iniciar sesión para ver tu rutina."
        })
    
    # Usar exclusivamente el ID de Google
    user_id = user['google_id']
    
    # Check if the request is for JSON format
    if format == "json":
        rutina_data = get_routine(user_id)
        return JSONResponse(content={"success": True, "rutina": rutina_data})
    
    # Return HTML response
    return templates.TemplateResponse("rutina.html", {"request": request, "user": user})

@router.post("/rutina", response_class=JSONResponse)
async def save_rutina(request: Request, user = Depends(get_current_user)):
    """Guarda la configuración de rutina."""
    try:
        # Asegurar que tenemos un usuario autenticado
        if not user or not user.get('google_id'):
            return JSONResponse(content={
                "success": False,
                "message": "Usuario no autenticado o sin ID válido."
            }, status_code=401)
        
        # Usar exclusivamente el ID de Google
        user_id = user['google_id']
        
        data = await request.json()
        rutina_data = data.get("rutina", {})
        
        print(f"Guardando rutina para usuario con Google ID: {user_id}")
        success = save_routine(user_id, rutina_data)
        
        return JSONResponse(content={
            "success": success,
            "message": "Rutina actualizada correctamente" if success else "Error al guardar la rutina"
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": f"Error: {str(e)}"
        }, status_code=500)

# Profile and Fitbit routes
@router.get('/profile', response_class=HTMLResponse)
async def profile(request: Request, user_id: str = Query("3892415"), user = Depends(get_current_user)):
    """Página del perfil del usuario."""
    try:
        # Use the authenticated user's ID instead of the query parameter
        actual_user_id = str(user["id"]) if user else user_id
        
        # Check if this user has Fitbit tokens in the database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Query for tokens - try both string ID and integer ID
        print(f"Checking Fitbit tokens for user ID: {actual_user_id}")
        cur.execute(
            """
            SELECT access_token, refresh_token, expires_at 
            FROM fitbit_tokens 
            WHERE user_id = %s OR user_id = %s
            """,
            (actual_user_id, user_id)
        )
        
        result = cur.fetchone()
        is_connected = result is not None
        
        fitbit_profile = None
        health_metrics = None
        
        # If connected, get Fitbit profile data
        if is_connected:
            print(f"User {actual_user_id} is connected to Fitbit!")
            access_token = result[0]
            refresh_token = result[1]
            expires_at = result[2]
            
            # Check if token is expired
            if expires_at and datetime.now() > expires_at:
                print("Token is expired, refreshing...")
                # Implement token refresh logic here if needed
                # For now, just continue with what we have
            
            # Get Fitbit profile if we have a token
            if access_token:
                try:
                    credentials = get_fitbit_credentials()
                    headers = {"Authorization": f"Bearer {access_token}"}
                    profile_url = credentials.get('profile_url')
                    
                    print(f"Fetching profile from: {profile_url}")
                    profile_response = requests.get(profile_url, headers=headers)
                    
                    if profile_response.status_code == 200:
                        fitbit_profile = profile_response.json()
                        print("Successfully fetched Fitbit profile!")
                    else:
                        print(f"Error fetching profile: {profile_response.status_code}, {profile_response.text}")
                except Exception as e:
                    print(f"Error getting Fitbit profile: {str(e)}")
        else:
            print(f"User {actual_user_id} is NOT connected to Fitbit")
        
        cur.close()
        conn.close()
        
        return templates.TemplateResponse('profile.html', {
            "request": request, 
            "user_id": actual_user_id,
            "is_connected": is_connected,
            "fitbit_profile": fitbit_profile,
            "health_metrics": health_metrics,
            "user": user
        })
    except Exception as e:
        print(f"Error in profile page: {str(e)}")
        return templates.TemplateResponse('profile.html', {
            "request": request, 
            "user_id": user_id,
            "is_connected": False,
            "error_message": str(e),
            "user": user
        })

@router.get('/connect-fitbit')
async def connect_fitbit(request: Request, user_id: str = Query("3892415"), user = Depends(get_current_user)):
    """Iniciar proceso de conexión con Fitbit."""
    try:
        # Use authenticated user ID if available
        actual_user_id = str(user["id"]) if user else user_id
        
        # Get credentials from environment variables
        credentials = get_fitbit_credentials()
        state = secrets.token_urlsafe(16)
        
        # For debugging
        print(f"Using redirect URI: {credentials['redirect_uri']}")
        
        # Create a response that will set cookies first
        response = RedirectResponse(url='')
        response.set_cookie(key="oauth_state", value=state, httponly=True, samesite="lax")
        response.set_cookie(key="fitbit_user_id", value=actual_user_id, httponly=True, samesite="lax")
        
        # Build the authorization URL
        auth_url = (
            f"{credentials['auth_url']}?"
            f"response_type=code&"
            f"client_id={credentials['client_id']}&"
            f"redirect_uri={credentials['redirect_uri']}&"
            f"scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20weight&"
            f"state={state}"
        )
        
        # Set the redirect URL
        response = RedirectResponse(url=auth_url)
        
        # Debug
        print(f"Redirecting to: {auth_url}")
        return response
    except Exception as e:
        print(f"Error in connect_fitbit: {str(e)}")
        return templates.TemplateResponse('profile_callback.html', {
            "request": request,
            "success": False,
            "message": f"Error al iniciar autenticación: {str(e)}",
            "user": user
        })

@router.get('/fitbit-callback')
async def fitbit_callback(
    request: Request, 
    code: str = Query(None), 
    state: str = Query(None), 
    error: str = Query(None),
    user = Depends(get_current_user)
):
    """Callback para recibir el código de autorización de Fitbit."""
    print(f"Fitbit callback received - code: {'present' if code else 'missing'}, state: {state}")
    print(f"Request cookies: {request.cookies}")
    
    # Get state and user_id from cookies
    expected_state = request.cookies.get('oauth_state')
    
    # Use the specific fitbit_user_id cookie if available, or fallback to user_id cookie
    # Also use the authenticated user's ID if available
    cookie_user_id = request.cookies.get('fitbit_user_id') or request.cookies.get('user_id', "3892415")
    actual_user_id = str(user["id"]) if user else cookie_user_id
    
    print(f"Expected state: {expected_state}, User ID from cookie: {cookie_user_id}, Actual User ID: {actual_user_id}")
    
    # Handle error from Fitbit
    if error:
        return templates.TemplateResponse('profile_callback.html', {
            "request": request,
            "success": False,
            "message": f"Error de autorización: {error}",
            "user": user
        })
    
    # Continue even if state doesn't match (for debugging)
    if expected_state != state:
        print(f"WARNING: State mismatch. Expected {expected_state}, got {state}")
        # We'll continue anyway for debugging purposes
    
    # Make sure we have the code
    if not code:
        return templates.TemplateResponse('profile_callback.html', {
            "request": request,
            "success": False,
            "message": "No se recibió el código de autorización",
            "user": user
        })
    
    try:
        # Get credentials for token exchange
        credentials = get_fitbit_credentials()
        
        # Build authorization header
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
            "redirect_uri": credentials['redirect_uri']
        }
        
        # Debug info
        print(f"Exchanging code for tokens with redirect_uri: {credentials['redirect_uri']}")
        print(f"Token URL: {credentials['token_url']}")
        
        # Make the token request
        response = requests.post(credentials['token_url'], headers=headers, data=data)
        
        # Check response
        if response.status_code != 200:
            print(f"Error getting tokens: {response.status_code}, {response.text}")
            return templates.TemplateResponse('profile_callback.html', {
                "request": request,
                "success": False,
                "message": f"Error al intercambiar tokens: {response.status_code}, {response.text[:100]}",
                "user": user
            })
        
        tokens = response.json()
        print("Tokens received successfully")
        
        # Save tokens to database
        try:
            # Create database connection
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Check if table exists and create if needed
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'fitbit_tokens'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                print("Creating fitbit_tokens table")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS fitbit_tokens (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL UNIQUE,
                        client_id VARCHAR(255) NOT NULL,
                        access_token TEXT NOT NULL,
                        refresh_token TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Calculate token expiration
            expires_in = tokens.get('expires_in', 28800)  # Default 8 hours
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Remove any existing tokens for this user (using both IDs to be safe)
            cur.execute("DELETE FROM fitbit_tokens WHERE user_id = %s OR user_id = %s", (actual_user_id, cookie_user_id))
            
            # Insert new tokens - use the actual_user_id which should be the internal user ID
            print(f"Saving Fitbit tokens for user ID: {actual_user_id}")
            cur.execute(
                """
                INSERT INTO fitbit_tokens 
                (user_id, client_id, access_token, refresh_token, expires_at) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    actual_user_id, 
                    credentials['client_id'], 
                    tokens.get('access_token'), 
                    tokens.get('refresh_token'),
                    expires_at
                )
            )
            
            conn.commit()
            cur.close()
            conn.close()
            
            print("Tokens saved to database")
            
            # Success response
            return templates.TemplateResponse('profile_callback.html', {
                "request": request,
                "success": True,
                "message": "¡Cuenta de Fitbit conectada correctamente!",
                "user": user
            })
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            return templates.TemplateResponse('profile_callback.html', {
                "request": request,
                "success": False,
                "message": f"Error al guardar tokens: {str(db_error)}",
                "user": user
            })
    except Exception as e:
        print(f"Error in Fitbit callback: {str(e)}")
        return templates.TemplateResponse('profile_callback.html', {
            "request": request,
            "success": False,
            "message": f"Error inesperado: {str(e)}",
            "user": user
        })