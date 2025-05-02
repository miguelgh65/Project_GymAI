# back_end/gym/routes/chatbot.py
import logging
import os
import json
import requests
import asyncio
from typing import Dict, Any, List, AsyncIterable

# Configuración de logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.responses import Response

# Importaciones para la autenticación
from back_end.gym.middlewares import get_current_user

# Importamos el LLM del config para usarlo como respaldo
from back_end.gym.config import llm

# URL del servicio LangGraph (intentar primero host.docker.internal)
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://host.docker.internal:8000")
LANGGRAPH_ENDPOINT = os.getenv("LANGGRAPH_ENDPOINT", "/api/chat")
USE_FALLBACK = os.getenv("USE_FALLBACK", "true").lower() == "true"  # Por defecto, usar fallback

# Configure LangSmith if available
try:
    import langsmith
    HAS_LANGSMITH = True
    logger.info("Successfully imported LangSmith for chatbot integration")
except ImportError:
    HAS_LANGSMITH = False
    logger.warning("LangSmith not available, continuing without tracing")

router = APIRouter(
    prefix="/api/chatbot",
    tags=["chatbot"],
)

async def stream_generator(user_id: str, message: str):
    """
    Generador de streaming mejorado para respuestas del chatbot.
    Envía cada token a medida que lo genera para un streaming real.
    """
    logger.info(f"Iniciando streaming para usuario {user_id}")
    
    try:
        # Prompt con contexto de fitness
        system_prompt = """Eres un asistente de fitness y entrenamiento personal. Ofrece consejos útiles, 
        información sobre ejercicios, técnicas correctas, nutrición deportiva y rutinas de entrenamiento. 
        Mantén un tono motivador pero basado en evidencia científica. Si no estás seguro de algo, 
        indícalo claramente y sugiere consultar con un profesional.
        
        El usuario está interesado en mejorar su condición física y busca orientación práctica.
        """
        
        # Preparar mensajes para el LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Versión con streaming
        if hasattr(llm, 'stream') or hasattr(llm, 'astream'):
            # Usar streaming nativo si está disponible
            if hasattr(llm, 'astream'):
                # Versión asíncrona - mejor para servidores web
                accumulated_text = ""
                
                # Forzar un delay inicial para establecer la conexión
                yield "data: {}\n\n"
                await asyncio.sleep(0.05)
                
                # Usar astream para procesar token por token
                async for chunk in llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        # Acumular texto para mostrar lo generado hasta ahora
                        accumulated_text += chunk.content
                        yield f"data: {json.dumps({'content': accumulated_text})}\n\n"
                        # Un pequeño delay ayuda a que el streaming sea visible
                        await asyncio.sleep(0.01)
            else:
                # Versión síncrona (menos recomendada)
                accumulated_text = ""
                for chunk in llm.stream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        accumulated_text += chunk.content
                        yield f"data: {json.dumps({'content': accumulated_text})}\n\n"
                        await asyncio.sleep(0.01)
        else:
            # Simulación para LLMs sin streaming nativo
            response = llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Dividir en palabras/caracteres para simular streaming
            full_text = ""
            for i in range(len(content)):
                full_text += content[i]
                if i % 3 == 0:  # Cada 3 caracteres
                    yield f"data: {json.dumps({'content': full_text})}\n\n"
                    await asyncio.sleep(0.03)  # Pausa para simular un streaming realista
        
        # Evento final
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        logger.exception(f"Error en stream_generator: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

def fallback_chatbot_response(user_id: str, message: str) -> Dict[str, Any]:
    """
    Función de respaldo que usa el LLM configurado directamente para responder 
    cuando LangGraph no está disponible.
    """
    logger.info(f"Usando respuesta de respaldo para usuario {user_id}")
    
    try:
        # Prompt con contexto de fitness
        system_prompt = """Eres un asistente de fitness y entrenamiento personal. Ofrece consejos útiles, 
        información sobre ejercicios, técnicas correctas, nutrición deportiva y rutinas de entrenamiento. 
        Mantén un tono motivador pero basado en evidencia científica. Si no estás seguro de algo, 
        indícalo claramente y sugiere consultar con un profesional.
        
        El usuario está interesado en mejorar su condición física y busca orientación práctica.
        """
        
        # Preparar mensajes para el LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Invocamos el LLM directamente desde el config
        response = llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Estructura de respuesta similar a LangGraph
        return {
            "messages": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": content}
            ]
        }
    except Exception as e:
        logger.exception(f"Error en respuesta de respaldo: {e}")
        return {
            "messages": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "Lo siento, estoy experimentando dificultades técnicas. Por favor, inténtalo de nuevo más tarde."}
            ]
        }

@router.post("/send", response_class=JSONResponse)
async def chatbot_send(request: Request, user = Depends(get_current_user)):
    """API endpoint para enviar mensajes al chatbot"""
    
    # Verificar autenticación
    if not user or not user.get('id'):
        logger.warning("Intento de acceso a chatbot sin autenticación")
        return JSONResponse(
            content={"success": False, "message": "Usuario no autenticado"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Extraer datos del request
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        stream = data.get("stream", False)  # Parámetro para activar streaming
        
        if not message:
            logger.warning("Mensaje vacío recibido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty."
            )

        # Usar ID de usuario 
        user_id = str(user["id"])
        logger.info(f"Procesando mensaje para usuario {user_id}: '{message[:50]}...'")

        # Verificar si se solicitó streaming
        if stream:
            logger.info(f"Usando modo streaming para usuario {user_id}")
            
            # Usar StreamingResponse con los headers correctos para SSE
            return StreamingResponse(
                stream_generator(user_id, message),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-transform",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                    "X-Accel-Buffering": "no",  # Importante para Nginx
                    "Access-Control-Allow-Origin": "*",  # Permitir CORS para este endpoint
                }
            )
        
        # Si no es streaming, seguir con el flujo normal
        # Configurar LangSmith si está disponible
        if HAS_LANGSMITH:
            try:
                project_name = os.getenv("LANGSMITH_PROJECT", "gym")
                langsmith.set_project(project_name)
                langsmith.set_tags([f"user:{user_id}"])
            except Exception as e:
                logger.error(f"Error configuring LangSmith: {e}")

        # Intentar usar LangGraph primero, si no está forzado el fallback
        result = None
        if not USE_FALLBACK:
            try:
                langgraph_url = f"{LANGGRAPH_URL}{LANGGRAPH_ENDPOINT}"
                payload = {
                    "user_id": user_id,
                    "message": message
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "X-API-Key": os.getenv("LANGGRAPH_API_KEY", ""),
                }
                
                logger.info(f"Intentando conectar a LangGraph: {langgraph_url}")
                timeout = int(os.getenv("LANGGRAPH_TIMEOUT", "5"))  # Timeout corto para probar rápido
                
                response = requests.post(
                    langgraph_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                    verify=os.getenv("LANGGRAPH_VERIFY_SSL", "true").lower() == "true"
                )
                
                response.raise_for_status()
                result = response.json()
                logger.info(f"Respuesta recibida de LangGraph correctamente")
                
            except requests.exceptions.RequestException as req_err:
                logger.warning(f"Error conectando a LangGraph, usando respaldo: {req_err}")
                # Si falla LangGraph, usamos el respaldo pero no elevamos el error
                result = None
        
        # Si no tenemos resultado de LangGraph, usamos el respaldo
        if result is None:
            result = fallback_chatbot_response(user_id, message)
            
        # Extraer la respuesta del resultado
        messages = result.get("messages", [])
        response_message = next((msg for msg in messages if msg.get("role") == "assistant"), None)
        
        if not response_message:
            logger.error(f"No se encontró respuesta del asistente en el resultado.")
            # Respuesta alternativa si no se puede extraer
            responses = [{
                "role": "assistant",
                "content": "Lo siento, no pude procesar tu consulta correctamente. Por favor, inténtalo de nuevo."
            }]
        else:
            responses = [{
                "role": "assistant",
                "content": response_message.get("content", "")
            }]

        return JSONResponse(content={"success": True, "responses": responses})

    except json.JSONDecodeError:
        logger.error("Error al decodificar JSON en solicitud")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format in request body."
        )
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP para que FastAPI las maneje
        raise http_exc
    except Exception as e:
        logger.exception(f"Error procesando mensaje para usuario {user.get('id', 'N/A')}: {e}")
        return JSONResponse(
            content={"success": False, "message": "Error interno del servidor al procesar la solicitud."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Endpoint para historial (sin cambios)
@router.get("/history", response_class=JSONResponse)
async def chatbot_history(request: Request, user = Depends(get_current_user)):
    """API endpoint to get conversation history"""
    # Verify user authentication
    if not user or not user.get('id'):
        return JSONResponse(
            content={"success": False, "message": "User not authenticated"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Use the internal user ID
    user_id = str(user["id"])

    try:
        # --- Implementación del historial ---
        # Ejemplo simulado:
        logger.info(f"Fetching conversation history for user {user_id} (currently returning empty).")
        history_from_db = []  # Placeholder

        return JSONResponse(content={"success": True, "history": history_from_db, "user_id": user_id})

    except Exception as e:
        logger.exception(f"Error fetching history for user {user_id}: {e}")
        return JSONResponse(
             content={"success": False, "message": "An internal error occurred while fetching history."},
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )