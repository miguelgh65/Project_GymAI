import os
import logging
from typing import Dict, Any

from langchain_deepseek import ChatDeepSeek

logger = logging.getLogger("fitness_chatbot")

# Configuración por defecto para DeepSeek
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024

# ¡IMPORTANTE! Esta clave API está hardcodeada SOLO PARA PRUEBAS
# En producción, siempre debe usar variables de entorno
HARDCODED_API_KEY = "sk-289660c5a8524bc8af1c9ea38f9368c1"

def get_config() -> Dict[str, Any]:
    """
    Obtiene la configuración para el LLM desde variables de entorno.
    
    Returns:
        Dict con la configuración del LLM
    """
    # Intentar obtener la API key de varias fuentes
    # 1. Primero de variable de entorno directa
    api_key = os.getenv("LLM_API_KEY")
    
    # 2. Si no existe, intentar cargar de forma explícita del archivo .env en diversos lugares
    if not api_key:
        logger.warning("LLM_API_KEY no encontrada en variables de entorno. Buscando en archivos .env")
        try:
            from dotenv import load_dotenv
            # Buscar el archivo .env en varios directorios
            possible_paths = [
                '.env',                         # Directorio actual
                '../.env',                      # Directorio padre
                '../../.env',                   # Dos directorios arriba
                'fitness_chatbot/.env',         # Dentro del directorio del chatbot
                os.path.join(os.getcwd(), '.env')  # Path absoluto al directorio actual
            ]
            
            for env_path in possible_paths:
                if os.path.exists(env_path):
                    logger.info(f"Cargando .env desde: {os.path.abspath(env_path)}")
                    load_dotenv(env_path)
                    api_key = os.getenv("LLM_API_KEY")
                    if api_key:
                        logger.info("API key cargada correctamente desde .env")
                        break
            
        except Exception as e:
            logger.error(f"Error cargando .env: {e}")
    
    # 3. Si aún no hay clave, usar la hardcodeada
    if not api_key:
        logger.warning("No se encontró API key en variables de entorno. Usando clave hardcodeada para pruebas.")
        api_key = HARDCODED_API_KEY
    
    # Registrar información útil para depuración
    if api_key:
        # Mostrar clave completa para diagnóstico (⚠️ solo en desarrollo)
        logger.info(f"API KEY que se usará: '{api_key}'")
    
    return {
        "model": os.getenv("LLM_MODEL", DEFAULT_MODEL),
        "api_key": api_key,
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
        logger.warning("⚠️ LLM_API_KEY no está configurada. Las llamadas al LLM fallarán.")
    
    try:
        logger.info(f"Inicializando ChatDeepSeek con configuración: {config}")
        return ChatDeepSeek(
            api_key=api_key,
            **{k: v for k, v in config.items() if k != "api_key"}
        )
    except Exception as e:
        logger.error(f"Error al inicializar ChatDeepSeek: {str(e)}")
        raise