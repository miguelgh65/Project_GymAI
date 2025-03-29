import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telegram.gym.utils import log_to_console  # Importar desde la ubicación correcta
from fastapi import APIRouter, Request, Response, HTTPException, Form, Query, Cookie, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import secrets
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from services.auth_service import (
    verify_google_token, 
    get_or_create_user, 
    migrate_user_data,
    get_user_by_id,
    get_user_id_by_telegram,
    get_user_id_by_google,
    generate_link_code,  # Añadido
    verify_link_code     # Añadido
)
from config import GOOGLE_CONFIG

# Cargar variables de entorno
load_dotenv()

# Configuración para Google Auth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5050/google-callback')

# Configuración de plantillas
templates = Jinja2Templates(directory="/app/workflows/gym/templates")
router = APIRouter()
# Añadir a routes/auth.py (después de las importaciones existentes)
import random
import string

# Añadir la nueva ruta para generar códigos de vinculación
@router.post("/api/generate-link-code", response_class=JSONResponse)
async def generate_link_code_route(request: Request):
    """Genera un código para vincular una cuenta de Telegram."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return JSONResponse(
            content={"success": False, "message": "Usuario no autenticado"},
            status_code=401
        )
    
    try:
        user = get_user_by_id(int(user_id))
        if not user:
            return JSONResponse(
                content={"success": False, "message": "Usuario no encontrado"},
                status_code=404
            )
        
        # Generar nuevo código de vinculación
        code = generate_link_code(user["id"])
        
        if not code:
            return JSONResponse(
                content={"success": False, "message": "Error al generar código"},
                status_code=500
            )
        
        return JSONResponse(content={"success": True, "code": code})
    except Exception as e:
        print(f"Error en generate_link_code_route: {str(e)}")
        return JSONResponse(
            content={"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )

@router.post("/api/verify-link-code", response_class=JSONResponse)
async def verify_link_code_route(request: Request):
    """Verifica un código de vinculación desde el bot de Telegram."""
    try:
        data = await request.json()
        code = data.get("code")
        telegram_id = data.get("telegram_id")
        
        if not code or not telegram_id:
            return JSONResponse(
                content={"success": False, "message": "Faltan parámetros requeridos"},
                status_code=400
            )
        
        # Verificar el código y vincular cuenta
        success = verify_link_code(code, telegram_id)
        
        if success:
            return JSONResponse(content={"success": True, "message": "Cuentas vinculadas correctamente"})
        else:
            return JSONResponse(
                content={"success": False, "message": "Código inválido o expirado"},
                status_code=400
            )
    except Exception as e:
        print(f"Error en verify_link_code_route: {str(e)}")
        return JSONResponse(
            content={"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )
# Página de inicio de sesión
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, redirect_url: str = "/"):
    """Página de inicio de sesión con Google."""
    # Si el usuario ya está autenticado, redirigir directamente
    user = getattr(request.state, "user", None)
    if user:
        return RedirectResponse(url=redirect_url)
        
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request, 
            "google_client_id": GOOGLE_CLIENT_ID,
            "redirect_url": redirect_url
        }
    )
# Ruta para manejar el callback de Google
@router.get("/google-callback", response_class=HTMLResponse)
async def google_callback(request: Request):
    """Maneja el callback de Google después de la autenticación."""
    return templates.TemplateResponse(
        "google_callback.html", 
        {"request": request}
    )

@router.post("/auth/google/verify", response_class=JSONResponse)
async def verify_google_signin(request: Request, response: Response):
    try:
        # Obtener el token del cuerpo de la solicitud
        data = await request.json()
        token = data.get("id_token")
        telegram_id = data.get("telegram_id")
        
        print(f"DEBUG - Token received: {bool(token)}")
        
        if not token:
            return JSONResponse(
                content={"success": False, "message": "Token no proporcionado"},
                status_code=400
            )
        
        # Verificar el token con Google
        user_info = verify_google_token(token)
        
        print(f"DEBUG - User info: {user_info}")
        
        if not user_info:
            return JSONResponse(
                content={"success": False, "message": "Token inválido"},
                status_code=400
            )
        
        # Obtener información del usuario de Google
        google_id = user_info.get("sub")
        email = user_info.get("email")
        display_name = user_info.get("name")
        profile_picture = user_info.get("picture")
        
        # Crear o actualizar el usuario
        user_id = get_or_create_user(
            google_id=google_id,
            telegram_id=telegram_id,
            email=email,
            display_name=display_name,
            profile_picture=profile_picture
        )
        
        print(f"DEBUG - User ID created: {user_id}")
        
        if not user_id:
            return JSONResponse(
                content={"success": False, "message": "Error al crear/actualizar usuario"},
                status_code=500
            )
        
        # Si se proporcionó un Telegram ID y es diferente al que tiene el usuario,
        # migrar los datos del usuario de Telegram al nuevo usuario unificado
        if telegram_id:
            old_user_id = get_user_id_by_telegram(telegram_id)
            if old_user_id and old_user_id != user_id:
                migrate_user_data(telegram_id, user_id)
        
        # Establecer una cookie con el ID del usuario
        # IMPORTANTE: Usar response.headers para establecer la cookie manualmente
        response.set_cookie(
            key="user_id",
            value=str(user_id),
            httponly=True,
            secure=False,  # Cambiar a True en producción con HTTPS
            samesite="lax",
            max_age=86400 * 30,  # 30 días
            path="/"  # Especificar path explícitamente
        )
        
        # Establecer también en los headers para asegurar su establecimiento
        response.headers["Set-Cookie"] = f"user_id={user_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age={86400 * 30}"
        
        print(f"DEBUG - Cookie set for user {user_id}")
        
        # Devolver información básica del usuario con éxito
        return JSONResponse(
            content={
                "success": True,
                "user_id": user_id,
                "redirect": "/"  # Redirigir siempre a la página principal
            },
            headers={"Set-Cookie": f"user_id={user_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age={86400 * 30}"}
        )
    
    except Exception as e:
        print(f"ERROR en verify_google_signin: {str(e)}")
        return JSONResponse(
            content={"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )

# Ruta para cerrar sesión
@router.get("/logout")
async def logout(
    response: Response,
    redirect_url: str = "/",
    user_id: str = Cookie(None)
):
    """Cierra la sesión del usuario."""
    # Eliminar la cookie de user_id
    response.delete_cookie(key="user_id")
    
    # Redirigir a la página principal o a la URL especificada
    return RedirectResponse(url=redirect_url)
@router.get("/verify-telegram", response_class=HTMLResponse)
async def verify_telegram_page(request: Request, email: str = Query(None)):
    """
    Página de verificación de Telegram para usuarios con cuenta de Google.
    """
    if not email:
        return JSONResponse(
            content={"success": False, "message": "Email no proporcionado"},
            status_code=400
        )
    
    # Buscar usuario por email
    user = get_user_by_email(email)
    
    if not user or user.get('telegram_id'):
        return JSONResponse(
            content={
                "success": False, 
                "message": "Usuario no encontrado o ya tiene Telegram vinculado",
                "telegram_url": "https://t.me/RoonieColemAi_dev_bot"
            },
            status_code=404
        )
    
    # Generar código de vinculación
    link_code = generate_link_code(user['id'])
    
    return templates.TemplateResponse(
        "telegram_verify.html", 
        {
            "request": request, 
            "email": email,
            "link_code": link_code
        }
    )
# Ruta para obtener información del usuario actual
@router.get("/api/current-user", response_class=JSONResponse)
async def get_current_user(user_id: str = Cookie(None)):
    """Obtiene la información del usuario actual."""
    if not user_id:
        return JSONResponse(content={"success": False, "message": "No hay sesión activa"})
    
    try:
        user_info = get_user_by_id(int(user_id))
        if not user_info:
            return JSONResponse(content={"success": False, "message": "Usuario no encontrado"})
        
        # No devolver información sensible
        safe_user_info = {
            "id": user_info["id"],
            "display_name": user_info["display_name"],
            "email": user_info["email"],
            "profile_picture": user_info["profile_picture"],
            "has_telegram": user_info["telegram_id"] is not None,
            "has_google": user_info["google_id"] is not None
        }
        
        return JSONResponse(content={"success": True, "user": safe_user_info})
    except Exception as e:
        print(f"Error en get_current_user: {str(e)}")
        return JSONResponse(
            content={"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )

# Ruta para vincular una cuenta de Telegram a una cuenta de Google
@router.post("/api/link-telegram", response_class=JSONResponse)
async def link_telegram_account(
    request: Request,
    telegram_id: str = Form(...)
):
    """Vincula una cuenta de Telegram a la cuenta actual."""
    # Obtener el user_id de las cookies
    user_id = request.cookies.get("user_id")
    if not user_id:
        return JSONResponse(
            content={"success": False, "message": "Usuario no autenticado"},
            status_code=401
        )
    
    try:
        # Obtener los datos del usuario actual
        user = get_user_by_id(int(user_id))
        if not user:
            return JSONResponse(
                content={"success": False, "message": "Usuario no encontrado"},
                status_code=404
            )
        
        # Comprobar si el Telegram ID ya está vinculado a otro usuario
        existing_user_id = get_user_id_by_telegram(telegram_id)
        if existing_user_id and existing_user_id != user["id"]:
            # Migrar los datos del usuario de Telegram al usuario actual
            success = migrate_user_data(telegram_id, user["id"])
            if not success:
                return JSONResponse(
                    content={"success": False, "message": "Error al migrar datos de usuario"},
                    status_code=500
                )
        
        # Añadir a la whitelist de Telegram
        whitelist_path = os.path.join(os.path.dirname(__file__), "..", "..", "telegram", "gym", "whitelist.txt")
        try:
            with open(whitelist_path, "a") as f:
                f.write(f"\n{telegram_id}")
        except Exception as e:
            print(f"Error al añadir a whitelist: {e}")
        
        # Actualizar el Telegram ID del usuario actual
        updated_user_id = get_or_create_user(
            google_id=user["google_id"],
            telegram_id=telegram_id,
            email=user["email"],
            display_name=user["display_name"],
            profile_picture=user["profile_picture"]
        )
        
        if not updated_user_id:
            return JSONResponse(
                content={"success": False, "message": "Error al actualizar usuario"},
                status_code=500
            )
        
        return JSONResponse(content={
            "success": True, 
            "message": "Cuenta de Telegram vinculada correctamente",
            "telegram_url": "https://t.me/RoonieColemAi_dev_bot"
        })
    
    except Exception as e:
        print(f"Error en link_telegram_account: {str(e)}")
        return JSONResponse(
            content={"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )
