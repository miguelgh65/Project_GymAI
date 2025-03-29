import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from services.langgraph_agent.agent import process_message
from workflows.gym.middlewares import get_current_user

router = APIRouter()
# Use absolute path for templates
templates = Jinja2Templates(directory="/app/workflows/gym/templates")

@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request, user_id: str = "3892415", user = Depends(get_current_user)):
    """Página principal del chatbot."""
    return templates.TemplateResponse("chatbot.html", {"request": request, "user_id": user_id, "user": user})


@router.post("/api/chatbot/send", response_class=JSONResponse)
async def chatbot_send(request: Request, user = Depends(get_current_user)):
    """API para enviar mensajes al chatbot."""
    data = await request.json()
    if not data or "message" not in data:
        raise HTTPException(status_code=400, detail="No se proporcionó un mensaje")
    
    user_id = data.get("user_id", "3892415")
    message = data.get("message", "")
    
    # Procesar el mensaje con el agente
    responses = process_message(user_id, message)
    
    return {"success": True, "responses": responses}

@router.get("/api/chatbot/history", response_class=JSONResponse)
async def chatbot_history(user_id: str = "3892415", user = Depends(get_current_user)):
    """API para obtener el historial de conversación."""
    # Por ahora se retorna un historial vacío
    return {"success": True, "history": []}