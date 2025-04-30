# fitness_agent/agent/utils/llm_utils.py
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fitness_agent")

# Try to import language model libraries
try:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_core.output_parsers import StrOutputParser
    
    HAS_LANGCHAIN = True
    logger.info("Successfully imported LangChain for LLM utilities")
except ImportError:
    HAS_LANGCHAIN = False
    logger.warning("LangChain not available, using fallback LLM implementation")

try:
    from langchain_deepseek import ChatDeepSeek
    HAS_DEEPSEEK = True
    logger.info("DeepSeek integration available")
except ImportError:
    HAS_DEEPSEEK = False
    logger.warning("DeepSeek not available")

class FallbackLLM:
    """Simple fallback LLM when actual LLM libraries aren't available."""
    
    def __init__(self):
        pass
        
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """
        Invokes the fallback LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Object with a content attribute containing a response
        """
        # Extract the user's message for a simple response
        user_message = "Unknown message"
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "Unknown message")
                break
                
        # Simple response that acknowledges the message
        response_content = (
            f"I received your message: '{user_message}'. "
            "I'm currently operating in fallback mode as the main language model "
            "is not available. Please try again later when the system is fully operational."
        )
        
        # Create a response object with a content attribute
        class Response:
            def __init__(self, content):
                self.content = content
                
        return Response(response_content)

def get_llm() -> Any:
    """
    Gets an instance of the language model.
    
    Returns:
        An LLM instance that can process messages
    """
    try:
        if HAS_LANGCHAIN and HAS_DEEPSEEK:
            # Try to get credentials from environment variables
            # First check for DEEPSEEK_API_KEY, then fallback to LLM_API_KEY
            api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
            
            # Get model from environment, with fallback
            model = os.getenv("DEEPSEEK_MODEL") or os.getenv("LLM_MODEL", "deepseek-chat")
            
            # Get other parameters
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
            max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))
            
            if api_key:
                logger.info(f"Initializing DeepSeek LLM with model: {model}")
                return ChatDeepSeek(
                    model=model,
                    api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                logger.warning("No DeepSeek API key found, using fallback LLM")
                return FallbackLLM()
        else:
            logger.warning("Required LLM libraries not available, using fallback LLM")
            return FallbackLLM()
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}")
        return FallbackLLM()

def format_llm_response(content: str) -> str:
    """
    Formats the LLM response for better readability.
    
    Args:
        content: The raw response content from the LLM
        
    Returns:
        str: Formatted response content
    """
    # Strip unnecessary whitespace
    formatted = content.strip()
    
    # Remove any leading/trailing markdown-style code blocks
    if formatted.startswith("```") and formatted.endswith("```"):
        # Extract the language if specified
        if "\n" in formatted:
            first_line = formatted.split("\n", 1)[0]
            if len(first_line) > 3:  # More than just ```
                language = first_line[3:].strip()
                formatted = formatted.split("\n", 1)[1]
            else:
                formatted = formatted.split("\n", 1)[1]
        
        # Remove the trailing ```
        if formatted.endswith("```"):
            formatted = formatted[:-3].strip()
    
    return formatted