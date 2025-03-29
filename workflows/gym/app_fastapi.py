import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
from fastapi import FastAPI
from routes.main import router as main_router
from routes.routine import router as routine_router
from routes.dashboard import router as dashboard_router
from routes.profile import router as profile_router
from routes.chatbot import router as chatbot_router

load_dotenv()

app = FastAPI()

app.include_router(main_router)
app.include_router(routine_router)
app.include_router(dashboard_router)
app.include_router(profile_router)
app.include_router(chatbot_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app_fastapi:app", host="0.0.0.0", port=5050, reload=True)
