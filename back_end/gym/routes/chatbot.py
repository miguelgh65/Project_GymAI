# workflows/gym/routes/chatbot.py
import logging
import os
import sys

# Add the project root to the path
# Asegúrate que esta lógica de path funcione correctamente en tu despliegue
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)
    logging.info(f"Added {project_root} to Python path")

from fastapi import APIRouter, Depends, HTTPException, Request, status
# Se elimina HTMLResponse y Jinja2Templates
from fastapi.responses import JSONResponse
# from fastapi.templating import Jinja2Templates # Eliminado

# Asumiendo que middlewares está accesible
# Ajusta la ruta si es necesario, p.ej., from ...middlewares import get_current_user
from back_end.gym.middlewares import get_current_user

# Configure LangSmith if available (logging ya está configurado)
try:
    import langsmith
    HAS_LANGSMITH = True
    logging.info("Successfully imported LangSmith for chatbot integration")
except ImportError:
    HAS_LANGSMITH = False
    logging.warning("LangSmith not available, continuing without tracing")

router = APIRouter(
    prefix="/api/chatbot", # Añadir prefijo a las rutas de este router
    tags=["chatbot"],      # Etiqueta para Swagger UI
)
# Instancia de Templates eliminada
# templates = Jinja2Templates(directory="/app/front_end/templates") # Eliminado

# Import the fitness agent module - now that we've created the utils module
# (La lógica de importación y fallback se mantiene)
try:
    # Asegúrate que la ruta de importación sea correcta para tu estructura
    from fitness_agent.agent.nodes.router_node import process_message
    logging.info("Successfully imported process_message from fitness_agent.agent.nodes.router_node")
except ImportError as e:
    logging.error(f"Error importing process_message: {e}")

    # Simple message response class to maintain compatibility if import fails
    class MessageResponse:
        """Class to hold the agent's response."""
        def __init__(self, content: str):
            self.content = content

    # Fallback process message function if the import fails
    def process_message(user_id: str, message: str) -> MessageResponse:
        """
        Fallback implementation if the import fails.

        Args:
            user_id: ID of the user
            message: Message from the user

        Returns:
            MessageResponse: Object with the response content
        """
        # If we have LangSmith, configure tags
        if HAS_LANGSMITH:
            try:
                project_name = os.getenv("LANGSMITH_PROJECT", "gym")
                langsmith.set_project(project_name)
                langsmith.set_tags([f"user:{user_id}"])
            except Exception as e:
                logging.error(f"Error configuring LangSmith: {e}")

        try:
            # Return a message that explains we're in fallback mode
            response_content = f"Received: '{message}'. (Fallback mode: AI agent not fully loaded)."
            logging.info(f"Generated fallback response for user {user_id}")
            return MessageResponse(response_content)
        except Exception as e:
            logging.error(f"Error in fallback process_message: {e}")
            return MessageResponse("Sorry, an error occurred while processing your message.")

# --- Endpoint de Página Eliminado ---
# La ruta GET /chatbot que renderizaba HTML se ha eliminado.
# React se encargará de mostrar la interfaz del chatbot.

# --- Endpoints API para el Chatbot ---

@router.post("/send", response_class=JSONResponse) # Ruta relativa al prefijo: /api/chatbot/send
async def chatbot_send(request: Request, user = Depends(get_current_user)):
    """API endpoint to send messages to the chatbot"""
    # Verify user authentication
    if not user or not user.get('id'): # Verificar que 'id' existe en el objeto user
        return JSONResponse(
            content={"success": False, "message": "User not authenticated"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Extract data from request
    try:
        data = await request.json()
        # Validar que 'message' existe y no está vacío
        message = data.get("message", "").strip()
        if not message:
            # Usar HTTPException para errores de cliente claros
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty."
            )

        # Use the internal user ID (asegurarse que es el tipo correcto, ej: string)
        user_id = str(user["id"])
        logging.info(f"Processing message for user {user_id}")

        # Process the message using the imported (or fallback) function
        # Asume que process_message devuelve un objeto con atributo 'content'
        response_obj = process_message(user_id=user_id, message=message)

        # Format the response for the frontend
        # Asegurarse que response_obj.content existe
        response_content = getattr(response_obj, 'content', "Error: No content in response object.")

        responses = [{
            "role": "assistant",
            "content": response_content
        }]

        return JSONResponse(content={"success": True, "responses": responses})

    except json.JSONDecodeError:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail="Invalid JSON format in request body."
         )
    except HTTPException as http_exc:
         # Re-lanzar HTTPException para que FastAPI la maneje
         raise http_exc
    except AttributeError as attr_err:
         logging.error(f"Attribute error processing message (likely response object issue): {attr_err}")
         return JSONResponse(
             content={"success": False, "message": "Error formatting the response."},
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
         )
    except Exception as e:
        logging.exception(f"Error processing message for user {user.get('id', 'N/A')}: {e}") # Log completo del error
        # Devolver un error genérico al cliente
        return JSONResponse(
            content={"success": False, "message": "An internal error occurred while processing the message."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/history", response_class=JSONResponse) # Ruta relativa al prefijo: /api/chatbot/history
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
        # Aquí es donde conectarías con tu base de datos o sistema de almacenamiento
        # para recuperar el historial de conversaciones del user_id.
        # Ejemplo simulado:
        logging.info(f"Fetching conversation history for user {user_id} (currently returning empty).")
        # history_from_db = tu_funcion_para_obtener_historial(user_id)
        history_from_db = [] # Placeholder

        return JSONResponse(content={"success": True, "history": history_from_db, "user_id": user_id})

    except Exception as e:
        logging.exception(f"Error fetching history for user {user_id}: {e}") # Log completo del error
        return JSONResponse(
             content={"success": False, "message": "An internal error occurred while fetching history."},
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )