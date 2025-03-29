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
        # Public paths that do not require authentication
        public_paths = ['/login', '/google-callback', '/auth/google/verify', 
                        '/api/verify-link-code', '/static']
        
        # Check if current path is public
        current_path = request.url.path
        is_public = any(current_path.startswith(path) for path in public_paths)
        
        # Get user_id from cookies
        user_id = request.cookies.get("user_id")
        
        # If user_id exists, try to get user data
        if user_id:
            try:
                user = get_user_by_id(int(user_id))
                request.state.user = user
            except Exception as e:
                print(f"Error in AuthenticationMiddleware: {str(e)}")
                request.state.user = None
        else:
            request.state.user = None
        
        # If not a public path and user is not authenticated, redirect to login
        if not is_public and request.state.user is None:
            return RedirectResponse(url=f"/login?redirect_url={current_path}")
            
        # Continue with the request
        response = await call_next(request)
        return response