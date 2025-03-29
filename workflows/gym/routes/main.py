import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from services.database import get_exercise_logs, insert_into_db
from services.prompt_service import format_for_postgres
from utils.formatting import clean_input
from fastapi import Depends
from workflows.gym.middlewares import get_current_user

router = APIRouter()

# Create a local templates instance
templates = Jinja2Templates(directory="/app/workflows/gym/templates")

# Endpoint GET para renderizar la plantilla index.html
@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request, user = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})
# Endpoint POST para procesar el formulario
@router.post("/", response_class=JSONResponse)
async def post_index(
    request: Request,
    user_id: str = Form("3892415"),
    exercise_data: str = Form(...)
):
    if not exercise_data:
        return JSONResponse(content={"success": False, "message": "No se proporcionó información de ejercicios."})
    
    cleaned_text = clean_input(exercise_data)
    formatted_json = format_for_postgres(cleaned_text)
    if formatted_json is None:
        return JSONResponse(content={"success": False, "message": "Error en el procesamiento del LLM."})
    
    success = insert_into_db(formatted_json, user_id)
    return JSONResponse(content={
        "success": success,
        "message": "Datos insertados correctamente." if success else "Error al insertar en la base de datos."
    })

# Endpoint GET para obtener los logs
@router.get("/logs", response_class=JSONResponse)
async def get_logs_endpoint(
    user_id: str = Query("3892415"),
    days: int = Query(7)
):
    try:
        days_int = int(days)
    except ValueError:
        raise HTTPException(status_code=400, detail="El parámetro 'days' debe ser un entero.")
    
    logs = get_exercise_logs(user_id, days_int)
    if logs is None:
        raise HTTPException(status_code=500, detail="Error al obtener los logs.")
    
    return logs