from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from services.auth_service import get_user_by_id

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
            # Añadir más rutas públicas si es necesario
            '/favicon.ico',
            '/favicon.svg'
        ]
        
        # También considerar como públicas todas las rutas que empiecen con estos prefijos
        public_prefixes = ['/static/', '/api/', '/auth/']
        
        # Verificar si la ruta actual es pública
        current_path = request.url.path
        is_public = any(current_path.startswith(path) for path in public_paths) or \
                   any(current_path.startswith(prefix) for prefix in public_prefixes)
        
        # Obtener user_id de las cookies
        user_id = request.cookies.get("user_id")
        
        # Imprimir información de depuración
        print(f"DEBUG - Path: {current_path}, Public: {is_public}, User ID: {user_id}")
        
        # Si hay user_id, intentar obtener datos del usuario
        user = None
        if user_id:
            try:
                user = get_user_by_id(int(user_id))
                request.state.user = user
                print(f"DEBUG - User found: {user}")
            except Exception as e:
                print(f"ERROR en AuthenticationMiddleware: {str(e)}")
                request.state.user = None
        
        # Si no es una ruta pública y no hay usuario, redirigir al login
        if not is_public and not user:
            print("DEBUG - Redirecting to login (no user)")
            return RedirectResponse(url="/login")
        
        # Si está en login y tiene usuario, redirigir a la página principal
        if current_path == '/login' and user:
            print("DEBUG - Redirecting to home from login")
            return RedirectResponse(url="/")
        
        # Continuar con la solicitud
        response = await call_next(request)
        
        # Mantener la sesión del usuario como cookie (añadir nuevamente la cookie a la respuesta)
        if user_id and current_path != '/logout':
            # Asegurar que la cookie se mantenga con cada respuesta
            cookie_max_age = 60 * 60 * 24 * 30  # 30 días
            response.set_cookie(
                key="user_id",
                value=str(user_id),
                max_age=cookie_max_age,
                httponly=True,
                samesite="lax",
                path="/"
            )
        
        return response