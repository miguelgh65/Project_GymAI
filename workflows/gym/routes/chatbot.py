# workflows/gym/routes/chatbot.py
import logging
import os
import sys

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)
    logging.info(f"Added {project_root} to Python path")

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from workflows.gym.middlewares import get_current_user

# Configure LangSmith if available
try:
    import langsmith
    HAS_LANGSMITH = True
    logging.info("Successfully imported LangSmith for chatbot integration")
except ImportError:
    HAS_LANGSMITH = False
    logging.warning("LangSmith not available, continuing without tracing")

router = APIRouter()
templates = Jinja2Templates(directory="/app/front_end/templates")

# Import the fitness agent module - now that we've created the utils module
try:
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
            response_content = f"I received your message: '{message}'. The AI trainer is currently in fallback mode, but I've created the utility modules that should fix the connections."
            logging.info(f"Generated fallback response for user {user_id}")
            return MessageResponse(response_content)
        except Exception as e:
            logging.error(f"Error in fallback process_message: {e}")
            return MessageResponse("Sorry, I'm having trouble processing your message. Please try again later.")

@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request, user = Depends(get_current_user)):
    """Main chatbot page"""
    # Check if user is authenticated
    if not user:
        return HTMLResponse(
            content="You must be logged in to access the chatbot",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Use the internal user ID (integer)
    user_id = str(user["id"])
    return templates.TemplateResponse("chatbot.html", {"request": request, "user_id": user_id, "user": user})

@router.post("/api/chatbot/send", response_class=JSONResponse)
async def chatbot_send(request: Request, user = Depends(get_current_user)):
    """API endpoint to send messages to the chatbot"""
    # Verify user authentication
    if not user:
        return JSONResponse(
            content={"success": False, "message": "User not authenticated"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Extract data from request
    try:
        data = await request.json()
        if not data or "message" not in data:
            raise HTTPException(status_code=400, detail="No message provided")
        
        message = data.get("message", "")
        
        # Use the internal user ID instead of Telegram ID
        user_id = str(user["id"])
        logging.info(f"Processing message for user {user_id}")
        
        # Process the message with our simple function
        response = process_message(user_id, message)
        
        # Format the response for the frontend
        responses = [{
            "role": "assistant",
            "content": response.content
        }]
        
        return {"success": True, "responses": responses}
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return JSONResponse(
            content={"success": False, "message": "Error processing the message"},
            status_code=500
        )

@router.get("/api/chatbot/history", response_class=JSONResponse)
async def chatbot_history(request: Request, user = Depends(get_current_user)):
    """API endpoint to get conversation history"""
    # Verify user authentication
    if not user:
        return JSONResponse(
            content={"success": False, "message": "User not authenticated"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Use the internal user ID
    user_id = str(user["id"])
    
    # For now, return an empty history
    # You could implement actual history storage and retrieval here
    return {"success": True, "history": [], "user_id": user_id}