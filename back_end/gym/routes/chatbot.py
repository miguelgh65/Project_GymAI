# back_end/gym/routes/chatbot.py
import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterable

# Configuración de logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.responses import Response

# Importaciones para la autenticación
from back_end.gym.middlewares import get_current_user

# Importamos el LLM del config para usarlo como respaldo
from back_end.gym.config import llm

# Intentar importar el grafo de chatbot avanzado
CHATBOT_AVAILABLE = False
try:
    # Importación directa de la función process_message
    from fitness_chatbot.nodes.router_node import process_message
    CHATBOT_AVAILABLE = True
    logger.info("✅ Fitness Chatbot (LangGraph) disponible")
except ImportError as e:
    logger.warning(f"⚠️ Fitness Chatbot (LangGraph) no disponible, usando fallback: {e}")
except Exception as e:
    logger.error(f"❌ Error inicializando Fitness Chatbot: {e}")

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

async def stream_generator(user_id: str, message: str, auth_token: Optional[str] = None):
    """
    Generador de streaming mejorado para respuestas del chatbot.
    """
    logger.info(f"Iniciando streaming para usuario {user_id}")
    
    try:
        # Comprobar si debemos usar el chatbot avanzado 
        if CHATBOT_AVAILABLE:
            # Usar el chatbot avanzado
            try:
                # Procesar el mensaje pasando el token JWT
                response = await process_message(user_id, message, auth_token)
                
                # Simular streaming para el contenido
                content = response.content if hasattr(response, 'content') else str(response)
                chunks = [content[i:i+3] for i in range(0, len(content), 3)]
                
                full_text = ""
                for chunk in chunks:
                    full_text += chunk
                    yield f"data: {json.dumps({'content': full_text})}\n\n"
                    await asyncio.sleep(0.01)
                
                # Evento final
                yield f"data: {json.dumps({'done': True})}\n\n"
                return
            except Exception as e:
                logger.error(f"Error usando el chatbot avanzado: {e}")
                # Si falla, continuamos con el fallback
        
        # Fallback: Usar LLM directamente
        system_prompt = """Eres un asistente de fitness y entrenamiento personal."""
        
        # Preparar mensajes para el LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Versión con streaming
        if hasattr(llm, 'astream'):
            # Versión asíncrona
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
            # Simulación para LLMs sin streaming nativo
            response = llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Dividir en caracteres para simular streaming
            full_text = ""
            for i in range(len(content)):
                full_text += content[i]
                if i % 3 == 0:  # Cada 3 caracteres
                    yield f"data: {json.dumps({'content': full_text})}\n\n"
                    await asyncio.sleep(0.03)
        
        # Evento final
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        logger.exception(f"Error en stream_generator: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

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

    try:
        # Extraer datos del request
        data = await request.json()
        message = data.get("message", "").strip()
        stream = data.get("stream", False)  # Parámetro para activar streaming
        
        if not message:
            logger.warning("Mensaje vacío recibido")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty."
            )

        # Usar Google ID en lugar del ID interno
        user_id = str(user.get('google_id', user.get('id')))
        logger.info(f"Usando ID para consultas de ejercicios: {user_id} (Google ID si está disponible)")
        logger.info(f"Info de usuario: id={user.get('id')}, google_id={user.get('google_id', 'No disponible')}")

        # Verificar si se solicitó streaming
        if stream:
            logger.info(f"Usando modo streaming para usuario {user_id}")
            
            # Obtener el token JWT del encabezado Authorization
            auth_header = request.headers.get("Authorization")
            auth_token = None
            if auth_header and auth_header.startswith("Bearer "):
                auth_token = auth_header.replace("Bearer ", "")
                logger.info("Token JWT obtenido del encabezado Authorization")
            
            # Usar StreamingResponse
            return StreamingResponse(
                stream_generator(user_id, message, auth_token),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-transform",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        
        # Si no es streaming, procesar normalmente
        auth_header = request.headers.get("Authorization")
        auth_token = None
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header.replace("Bearer ", "")
            
        # Intentar usar el chatbot avanzado
        if CHATBOT_AVAILABLE:
            try:
                # Procesar el mensaje con LangGraph
                response = await process_message(user_id, message, auth_token)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Crear resultado
                return JSONResponse(content={
                    "success": True,
                    "responses": [{"role": "assistant", "content": content}]
                })
                
            except Exception as e:
                logger.error(f"Error usando LangGraph: {e}")
                # Si falla, usar fallback
        
        # Fallback: Usar LLM directamente
        system_prompt = """Eres un asistente de fitness y entrenamiento personal."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        response = llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        return JSONResponse(content={
            "success": True,
            "responses": [{"role": "assistant", "content": content}]
        })
    except HTTPException: # Añadido para relanzar HTTPException explícitamente
        raise # FastAPI manejará esto y devolverá el código de estado correcto (ej. 400)
    except Exception as e:
        logger.exception(f"Error procesando mensaje: {e}")
        # Este bloque ahora solo capturará otras excepciones no esperadas
        return JSONResponse(
            content={"success": False, "message": f"Error interno del servidor: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )