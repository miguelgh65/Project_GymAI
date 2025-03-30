# workflows/gym/routes/chatbot.py
import sys
import os
import logging

# Añadir la ruta al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)
    logging.info(f"Added {project_root} to Python path")

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from workflows.gym.middlewares import get_current_user

# Configurar LangSmith si está disponible
try:
    import langsmith
    HAS_LANGSMITH = True
    logging.info("Successfully imported LangSmith for chatbot integration")
except ImportError:
    HAS_LANGSMITH = False
    logging.warning("LangSmith not available, continuing without tracing")

# Importar el módulo del agente
try:
    # Importar desde la nueva ubicación
    from fitness_agent.agent.nodes.router_node import process_message
    logging.info("Successfully imported process_message from fitness_agent.agent.nodes.router_node")
except ImportError:
    # Fallback a la ubicación anterior
    try:
        from fitness_agent.agent.core.decisor import process_message
        logging.info("Fallback: imported process_message from fitness_agent.agent.core.decisor")
    except ImportError as e:
        logging.error(f"Error importing process_message: {e}")
        raise

router = APIRouter()
# Use absolute path for templates
templates = Jinja2Templates(directory="/app/workflows/gym/templates")

@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request, user = Depends(get_current_user)):
    """Página principal del chatbot."""
    if not user:
        return HTMLResponse(
            content="Debe iniciar sesión para acceder al chatbot",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Usar el ID interno del usuario (que debe ser un entero)
    user_id = str(user["id"])
    return templates.TemplateResponse("chatbot.html", {"request": request, "user_id": user_id, "user": user})


@router.post("/api/chatbot/send", response_class=JSONResponse)
async def chatbot_send(request: Request, user = Depends(get_current_user)):
    """API para enviar mensajes al chatbot."""
    # Verificar que el usuario esté autenticado
    if not user:
        return JSONResponse(
            content={"success": False, "message": "Usuario no autenticado"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Extraer data del request
    try:
        data = await request.json()
        if not data or "message" not in data:
            raise HTTPException(status_code=400, detail="No se proporcionó un mensaje")
        
        message = data.get("message", "")
        
        # Usar el ID interno del usuario en lugar del ID de Telegram
        user_id = str(user["id"])
        logging.info(f"Processing message for user {user_id}")
        
        # Configurar LangSmith
        if HAS_LANGSMITH:
            try:
                project_name = os.getenv("LANGSMITH_PROJECT", "gym")
                langsmith.set_project(project_name)
                langsmith.set_tags(["chatbot_api", f"user:{user_id}"])
            except Exception as e:
                logging.error(f"Error configuring LangSmith: {e}")
        
        # Procesar el mensaje con el agente
        response = process_message(user_id, message)
        
        # Adaptar la respuesta al formato esperado por el frontend
        responses = [{
            "role": "assistant",
            "content": response.content
        }]
        
        return {"success": True, "responses": responses}
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return JSONResponse(
            content={"success": False, "message": "Error procesando el mensaje"},
            status_code=500
        )

@router.get("/api/chatbot/history", response_class=JSONResponse)
async def chatbot_history(request: Request, user = Depends(get_current_user)):
    """API para obtener el historial de conversación."""
    # Verificar que el usuario esté autenticado
    if not user:
        return JSONResponse(
            content={"success": False, "message": "Usuario no autenticado"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Usar el ID interno del usuario
    user_id = str(user["id"])
    
    # Aquí implementarías la lógica para obtener el historial
    # Por ahora retornamos un historial vacío
    return {"success": True, "history": [], "user_id": user_id}