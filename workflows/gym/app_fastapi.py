import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import logging

# Disable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGCHAIN_PROJECT"] = ""

load_dotenv()

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="/app/workflows/gym/static"), name="static")

# Import routes after static files are mounted
from routes.main import router as main_router
from routes.routine import router as routine_router
from routes.dashboard import router as dashboard_router
from routes.profile import router as profile_router
from routes.chatbot import router as chatbot_router

# Include all routers
app.include_router(main_router)
app.include_router(routine_router)
app.include_router(dashboard_router)
app.include_router(profile_router)
app.include_router(chatbot_router)

# Import and start the Fitbit scheduler
from services.fitbit_scheduler import start_scheduler

@app.on_event("startup")
async def startup_event():
    """Run when the application starts up"""
    # Start the Fitbit token refresh scheduler
    try:
        scheduler = start_scheduler()
        logging.info("Fitbit scheduler started successfully")
    except Exception as e:
        logging.error(f"Error starting Fitbit scheduler: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app_fastapi:app", host="0.0.0.0", port=5050, reload=True)