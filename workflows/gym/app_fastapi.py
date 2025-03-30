import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import logging
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

# Importar middleware de autenticación
from workflows.gym.middlewares import AuthenticationMiddleware

# Disable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGCHAIN_PROJECT"] = ""
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

load_dotenv()

# Import the Fitbit scheduler
from services.fitbit_scheduler import start_scheduler

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code (runs before app startup)
    try:
        scheduler = start_scheduler()
        logging.info("Fitbit scheduler started successfully")
    except Exception as e:
        logging.error(f"Error starting Fitbit scheduler: {str(e)}")
    
    yield  # This is where the app runs
    
    # Shutdown code (runs when app is shutting down)
    # Add any cleanup code here if needed
    pass

# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan)

# Configurar middleware de sesiones
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('SECRET_KEY', os.urandom(24).hex())
)

# Añadir middleware de autenticación
app.add_middleware(AuthenticationMiddleware)

# Mount static files directory
app.mount("/static", StaticFiles(directory="/app/workflows/gym/static"), name="static")

# Import routes after static files are mounted
from routes.main import router as main_router
from routes.routine import router as routine_router
from routes.dashboard import router as dashboard_router
from routes.profile import router as profile_router
from routes.chatbot import router as chatbot_router
from routes.auth import router as auth_router

# Include all routers
app.include_router(main_router)
app.include_router(routine_router)
app.include_router(dashboard_router)
app.include_router(profile_router)
app.include_router(chatbot_router)
app.include_router(auth_router)  # Añadir el router de autenticación

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app_fastapi:app", host="0.0.0.0", port=5050, reload=True)