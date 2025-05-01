# simple_app.py - Versión que usa EXCLUSIVAMENTE la API de DeepSeek
import os
import logging
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fitness_chatbot")

# API Key hardcodeada - exactamente como aparece en el panel de DeepSeek
DEEPSEEK_API_KEY = "sk-289660c5a8524bc8af1c9ea38f9368c1"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Corregido con /v1/

# Crear la aplicación FastAPI
app = FastAPI(title="Fitness AI Assistant")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint de verificación de funcionamiento"""
    # Hacer una llamada de prueba rápida para verificar la API
    test_result = "No probada"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hi"}
                    ],
                    "max_tokens": 50
                }
            )
            
            if response.status_code == 200:
                test_result = "✅ API funciona correctamente"
            else:
                test_result = f"❌ Error API: {response.status_code} - {response.text}"
    except Exception as e:
        test_result = f"❌ Error de conexión: {str(e)}"
    
    return {
        "status": "online", 
        "message": "Fitness AI Assistant está funcionando",
        "api_test": test_result,
        "api_key_length": len(DEEPSEEK_API_KEY)
    }

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Endpoint de chat que usa EXCLUSIVAMENTE la API de DeepSeek.
    No hay respuestas predefinidas o fallbacks.
    """
    try:
        # Extraer datos de la solicitud
        data = await request.json()
        message = data.get("message", "")
        user_id = data.get("user_id", "default_user")
        
        if not message:
            return JSONResponse(
                status_code=400,
                content={"error": "Se requiere un mensaje para procesar"}
            )
        
        logger.info(f"Mensaje recibido de usuario {user_id}: {message[:50]}...")
        
        # Determinar si es una consulta sobre fitness específica
        if "bíceps" in message.lower() or "biceps" in message.lower():
            system_prompt = "Eres un entrenador personal especializado en desarrollo muscular, especialmente en bíceps. Da respuestas detalladas sobre ejercicios, series y técnicas."
        else:
            system_prompt = "Eres un asistente de fitness experto que proporciona información precisa sobre entrenamiento, nutrición deportiva y progreso físico."
        
        # Hacer llamada directa a la API de DeepSeek
        logger.info(f"Haciendo llamada a DeepSeek API con mensaje: {message[:50]}...")
        
        # Usar un timeout más largo (120 segundos) y desactivar el streaming para evitar el timeout
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800,
                    "stream": False  # Desactivar streaming para evitar problemas de timeout
                }
            )
        
        # Procesar respuesta
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"Respuesta exitosa de DeepSeek API: {len(ai_response)} caracteres")
            
            return JSONResponse(content={
                "response": ai_response,
                "intent": "ai_generated"
            })
        else:
            logger.error(f"Error de API DeepSeek: {response.status_code} - {response.text}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Error en API de DeepSeek: {response.status_code}",
                    "details": response.text
                }
            )
            
    except httpx.ReadTimeout:
        logger.error("Timeout al leer respuesta de DeepSeek API")
        return JSONResponse(
            status_code=504,
            content={
                "error": "La respuesta de la API tardó demasiado tiempo (timeout)",
                "response": "Lo siento, la API de asistente está tardando demasiado en responder. Por favor, intenta con una pregunta más corta o específica."
            }
        )
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Error interno del servidor: {str(e)}"}
        )

# Punto de entrada principal
if __name__ == "__main__":
    import uvicorn
    print("🤖 Iniciando servidor 100% basado en DeepSeek API...")
    uvicorn.run("simple_app:app", host="0.0.0.0", port=8000, reload=True)