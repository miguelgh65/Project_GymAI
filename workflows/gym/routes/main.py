import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from services.database import get_exercise_logs, insert_into_db
from services.prompt_service import format_for_postgres
from utils.formatting import clean_input

from workflows.gym.middlewares import get_current_user

router = APIRouter()

# Create a local templates instance
templates = Jinja2Templates(directory="/app/front_end/templates")

@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@router.post("/", response_class=JSONResponse)
async def post_index(
    request: Request,
    user = Depends(get_current_user)
):
    # Asegurar que tenemos un usuario autenticado
    if not user or not user.get('google_id'):
        return JSONResponse(content={
            "success": False, 
            "message": "Usuario no autenticado o sin ID válido."
        }, status_code=401)
    
    # Usar exclusivamente el ID de Google
    user_id = user['google_id']
    
    # Obtener los datos del formulario
    exercise_data = (await request.form())['exercise_data']
    
    cleaned_text = clean_input(exercise_data)
    formatted_json = format_for_postgres(cleaned_text)
    
    if formatted_json is None:
        return JSONResponse(content={
            "success": False, 
            "message": "Error en el procesamiento del LLM."
        })
    
    success = insert_into_db(formatted_json, user_id)
    return JSONResponse(content={
        "success": success,
        "message": "Datos insertados correctamente." if success else "Error al insertar en la base de datos."
    })

@router.get("/logs", response_class=JSONResponse)
async def get_logs_endpoint(
    days: int = Query(7),
    user = Depends(get_current_user)
):
    if not user or not user.get('google_id'):
        return JSONResponse(content={
            "success": False, 
            "message": "Usuario no autenticado o sin ID válido."
        }, status_code=401)
    
    # Usar exclusivamente el ID de Google
    user_id = user['google_id']
    
    try:
        days_int = int(days)
    except ValueError:
        raise HTTPException(status_code=400, detail="El parámetro 'days' debe ser un entero.")
    
    logs = get_exercise_logs(user_id, days_int)
    if logs is None:
        raise HTTPException(status_code=500, detail="Error al obtener los logs.")
    
    return logs