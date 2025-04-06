import os
import sys


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Importar middleware de autenticación
from back_end.gym.middlewares import AuthenticationMiddleware

# Cargar variables de entorno
load_dotenv()

# Configuración de logging más detallada
logging.basicConfig(
    level=logging.INFO,  # Cambia a logging.DEBUG para más detalle
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Muestra logs en consola
        logging.FileHandler('app.log', encoding='utf-8')  # Guardar en archivo
    ]
)

# Configurar logging para librerías externas (opcional)
logging.getLogger('uvicorn').setLevel(logging.WARNING)
logging.getLogger('fastapi').setLevel(logging.WARNING)

# Deshabilitar LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGCHAIN_PROJECT"] = ""

# Importar el scheduler de Fitbit
from services.fitbit_scheduler import start_scheduler

# Definir contexto de vida
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        scheduler = start_scheduler()
        logging.info("Fitbit scheduler started successfully")
    except Exception as e:
        logging.error(f"Error starting Fitbit scheduler: {str(e)}")
    
    yield
    # Código de cierre si es necesario

# Inicializar FastAPI
app = FastAPI(lifespan=lifespan)

# Configurar CORS desde las variables de entorno
cors_origins = os.getenv('CORS_ORIGINS', 'https://localhost:3000,https://localhost:5050').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de sesiones
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SECRET_KEY', os.urandom(24).hex())
)

# Middleware de autenticación
app.add_middleware(AuthenticationMiddleware)

# Importar routers
from routes.auth import router as auth_router
from routes.chatbot import router as chatbot_router
from routes.dashboard import router as dashboard_router
from routes.main import router as main_router
from routes.profile import router as profile_router
from routes.routine import router as routine_router

# Incluir routers
app.include_router(main_router)
app.include_router(routine_router)
app.include_router(dashboard_router)
app.include_router(profile_router)
app.include_router(chatbot_router)
app.include_router(auth_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app_fastapi:app", host="0.0.0.0", port=5050, reload=True)