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

load_dotenv()

templates = Jinja2Templates(directory="templates")
router = APIRouter()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'dbname': os.getenv('DB_NAME'),
}

FITBIT_AUTH_URL = os.getenv("FITBIT_AUTH_URL", "https://www.fitbit.com/oauth2/authorize")
FITBIT_TOKEN_URL = os.getenv("FITBIT_TOKEN_URL", "https://api.fitbit.com/oauth2/token")
FITBIT_PROFILE_URL = os.getenv("FITBIT_PROFILE_URL", "https://api.fitbit.com/1/user/-/profile.json")

def get_fitbit_credentials():
    return {
        'client_id': os.getenv('FITBIT_CLIENT_ID'),
        'client_secret': os.getenv('FITBIT_CLIENT_SECRET'),
        'redirect_uri': os.getenv('FITBIT_REDIRECT_URI')
    }

@router.get('/profile', response_class=HTMLResponse)
async def profile(request: Request, user_id: str = Query("3892415")):
    return templates.TemplateResponse('profile.html', {"request": request, "user_id": user_id})

@router.get('/connect-fitbit')
async def connect_fitbit(request: Request, response: Response, user_id: str = Query("3892415")):
    credentials = get_fitbit_credentials()
    state = secrets.token_urlsafe(16)
    response.set_cookie(key="oauth_state", value=state, httponly=True)
    response.set_cookie(key="user_id", value=user_id, httponly=True)

    auth_url = (
        f"{FITBIT_AUTH_URL}?response_type=code"
        f"&client_id={credentials['client_id']}"
        f"&redirect_uri={credentials['redirect_uri']}"
        f"&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20weight"
        f"&state={state}"
    )
    return RedirectResponse(auth_url)

@router.get('/fitbit-callback')
async def fitbit_callback(request: Request, code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    expected_state = request.cookies.get('oauth_state')
    user_id = request.cookies.get('user_id', "3892415")

    if error:
        return templates.TemplateResponse('profile_callback.html', {"request": request, "success": False, "message": error})

    if expected_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    tokens = exchange_code_for_tokens(code)

    if tokens:
        success = save_fitbit_tokens(user_id, tokens)
        message = "Cuenta de Fitbit conectada correctamente" if success else "Error al guardar tokens"
    else:
        success = False
        message = "Error al obtener tokens de acceso"

    response = templates.TemplateResponse('profile_callback.html', {"request": request, "success": success, "message": message})
    response.delete_cookie('oauth_state')
    response.delete_cookie('user_id')

    return response

@router.get('/api/fitbit-data')
async def get_fitbit_data(user_id: str = Query("3892415"), type: str = Query('profile')):
    return JSONResponse({"success": True, "data": {"type_requested": type}})

@router.post('/disconnect-fitbit')
async def disconnect_fitbit(user_id: str = Form("3892415")):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM fitbit_tokens WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return RedirectResponse(url=f'/profile?user_id={user_id}', status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desconectar cuenta: {str(e)}")

def exchange_code_for_tokens(code):
    credentials = get_fitbit_credentials()
    auth_string = f"{credentials['client_id']}:{credentials['client_secret']}"
    headers = {"Authorization": f"Basic {base64.b64encode(auth_string.encode()).decode()}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"client_id": credentials['client_id'], "grant_type": "authorization_code", "code": code, "redirect_uri": credentials['redirect_uri']}
    response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data)
    return response.json() if response.status_code == 200 else None

def save_fitbit_tokens(user_id, tokens):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        expires_at = datetime.now() + timedelta(seconds=tokens.get('expires_in', 28800))
        cur.execute("DELETE FROM fitbit_tokens WHERE user_id = %s", (user_id,))
        cur.execute("""INSERT INTO fitbit_tokens (user_id, access_token, refresh_token, expires_at)
                    VALUES (%s, %s, %s, %s)""",
                    (user_id, tokens['access_token'], tokens['refresh_token'], expires_at))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except:
        return False
