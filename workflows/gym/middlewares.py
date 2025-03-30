from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from services.auth_service import (
    get_user_by_id, 
    get_user_id_by_telegram, 
    get_user_id_by_google
)

async def get_current_user(request: Request):
    """
    Dependency to get the currently authenticated user.
    Can be used in endpoints with Depends(get_current_user).
    """
    return getattr(request.state, "user", None)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add authenticated user information to all requests
    and redirect unauthenticated users to the login page.
    """
    async def dispatch(self, request: Request, call_next):
        # Rutas públicas
        public_paths = [
            '/login', 
            '/google-callback', 
            '/auth/google/verify', 
            '/api/verify-link-code', 
            '/static',
            '/favicon.ico',
            '/favicon.svg'
        ]
        
        # También considerar como públicas todas las rutas que empiecen con estos prefijos
        public_prefixes = ['/static/', '/api/', '/auth/']
        
        # Verificar si es una petición del bot de Telegram
        is_telegram_bot_request = False
        resolved_user_id = None
        user_id_from_query = request.query_params.get('user_id')
        
        if user_id_from_query:
            try:
                # Intentar primero obtener el Google ID
                google_user_id = get_user_id_by_google(user_id_from_query)
                if google_user_id:
                    resolved_user_id = google_user_id
                else:
                    # Si no se encuentra el Google ID, intentar convertir el valor a entero
                    try:
                        resolved_user_id = int(user_id_from_query)
                    except ValueError:
                        # Si falla la conversión, buscar por Telegram
                        telegram_user_id = get_user_id_by_telegram(user_id_from_query)
                        resolved_user_id = telegram_user_id
                
                if resolved_user_id:
                    is_telegram_bot_request = True
                    print(f"DEBUG - Telegram/Google request detected. Resolved User ID: {resolved_user_id}")
            except Exception as e:
                print(f"ERROR resolving user ID: {str(e)}")
        
        # Verificar si la ruta actual es pública o es una petición del bot
        current_path = request.url.path
        is_public = (
            any(current_path.startswith(path) for path in public_paths) or
            any(current_path.startswith(prefix) for prefix in public_prefixes) or
            is_telegram_bot_request
        )
        
        # Obtener user_id de las cookies (si existe)
        cookie_user_id = request.cookies.get("user_id")
        
        # Imprimir información de depuración
        print(f"DEBUG - Path: {current_path}")
        print(f"DEBUG - Public: {is_public}")
        print(f"DEBUG - Cookie User ID: {cookie_user_id}")
        print(f"DEBUG - Resolved User ID: {resolved_user_id}")
        print(f"DEBUG - Telegram Bot Request: {is_telegram_bot_request}")
        
        # Determinar qué user_id usar: prioridad al ID resuelto vía query (bot) o bien a la cookie
        user_id_to_use = resolved_user_id or (int(cookie_user_id) if cookie_user_id else None)
        
        # Si hay user_id, intentar obtener datos del usuario
        user = None
        if user_id_to_use:
            try:
                user = get_user_by_id(user_id_to_use)
                request.state.user = user
                print(f"DEBUG - User found: {user}")
            except Exception as e:
                print(f"ERROR en AuthenticationMiddleware: {str(e)}")
                request.state.user = None
        
        # Si es una petición del bot, se espera que ya se haya resuelto el usuario con el Google ID
        if is_telegram_bot_request:
            print("DEBUG - Request authenticated as Telegram bot with Google ID")
        # Si no es una ruta pública y no hay usuario, redirigir al login
        elif not is_public and not user:
            print("DEBUG - Redirecting to login (no user)")
            return RedirectResponse(url="/login")
        
        # Si el usuario ya está autenticado y se encuentra en la ruta de login, redirigir al home
        if current_path == '/login' and user:
            print("DEBUG - Redirecting to home from login")
            return RedirectResponse(url="/")
        
        # Continuar con la solicitud
        response = await call_next(request)
        
        # Mantener la sesión del usuario como cookie (añadir nuevamente la cookie a la respuesta)
        if user_id_to_use and current_path != '/logout':
            cookie_max_age = 60 * 60 * 24 * 30  # 30 días
            response.set_cookie(
                key="user_id",
                value=str(user_id_to_use),
                max_age=cookie_max_age,
                httponly=True,
                samesite="lax",
                path="/"
            )
        
        return response
