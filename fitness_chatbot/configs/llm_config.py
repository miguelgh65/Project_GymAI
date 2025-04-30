import os
import logging
from typing import Dict, Any

from langchain_deepseek import ChatDeepSeek

logger = logging.getLogger("fitness_chatbot")

# Configuración por defecto para DeepSeek
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024

def get_config() -> Dict[str, Any]:
    """
    Obtiene la configuración para el LLM desde variables de entorno.
    
    Returns:
        Dict con la configuración del LLM
    """
    return {
        "model": os.getenv("LLM_MODEL", DEFAULT_MODEL),
        "api_key": os.getenv("LLM_API_KEY"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
        "timeout": int(os.getenv("LLM_TIMEOUT", 30)),
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", 3))
    }

def get_llm():
    """
    Obtiene una instancia configurada del LLM.
    
    Returns:
        Instancia de ChatDeepSeek configurada
    """
    config = get_config()
    api_key = config.pop("api_key", None)
    
    if not api_key:
        logger.warning("LLM_API_KEY no está configurada en las variables de entorno.")
        # Podrías lanzar una excepción aquí si prefieres que falle explícitamente
    
    try:
        return ChatDeepSeek(
            api_key=api_key,
            **{k: v for k, v in config.items() if k != "api_key"}
        )
    except Exception as e:
        logger.error(f"Error al inicializar ChatDeepSeek: {str(e)}")
        raise