# back_end/gym/routes/login_handler.py
import logging
from fastapi import APIRouter, Query, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse

router = APIRouter(tags=["authentication"])
logger = logging.getLogger(__name__)

@router.get("/login")
async def login_get(request: Request, redirect_url: str = Query(None)):
    """Página de login con redirección opcional"""
    logger.info(f"GET /login con redirect_url: {redirect_url}")
    # Solo renderiza HTML básico, el frontend React manejará la verdadera UI
    return HTMLResponse("<html><body>Redirigiendo a página de login...</body></html>")

@router.post("/login")
async def login_post(request: Request, redirect_url: str = Query(None)):
    """Maneja POST a /login redirigiendo al formulario GET"""
    logger.info(f"POST /login recibido con redirect_url: {redirect_url}")
    # Redirige a la versión GET del login
    redirect_to = f"/login?redirect_url={redirect_url}" if redirect_url else "/login"
    logger.info(f"Redirigiendo a: {redirect_to}")
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)