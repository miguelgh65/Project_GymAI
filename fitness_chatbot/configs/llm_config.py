# Archivo: fitness_chatbot/configs/llm_config.py (Corregido)
import os
import logging
from typing import Dict, Any

from langchain_deepseek import ChatDeepSeek

logger = logging.getLogger("fitness_chatbot")

# Configuración por defecto para DeepSeek
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024

# ¡IMPORTANTE! Clave API hardcodeada ELIMINADA.
# En producción, siempre debe usar variables de entorno
# HARDCODED_API_KEY = "sk-289660c5a8524bc8af1c9ea38f9368c1" # <--- ELIMINADA

def get_config() -> Dict[str, Any]:
    """
    Obtiene la configuración para el LLM desde variables de entorno.

    Returns:
        Dict con la configuración del LLM
    """
    # Intentar obtener la API key de variable de entorno directa
    api_key = os.getenv("LLM_API_KEY")

    # Si no existe, intentar cargar de forma explícita del archivo .env en diversos lugares
    if not api_key:
        logger.warning("LLM_API_KEY no encontrada en variables de entorno. Buscando en archivos .env")
        try:
            # Importar dotenv solo si es necesario
            from dotenv import load_dotenv
            # Buscar el archivo .env en varios directorios relativos al WORKDIR /app
            possible_paths = [
                '.env',                         # Raíz del proyecto (/app/.env)
                '../.env',                      # Un nivel arriba (no aplica en /app)
                '../../.env',                   # Dos niveles arriba (no aplica en /app)
                'fitness_chatbot/.env',         # Dentro del chatbot (/app/fitness_chatbot/.env)
                os.path.join(os.getcwd(), '.env') # Path absoluto al WORKDIR (/app/.env)
            ]
            # Filtrar duplicados y rutas no existentes fuera de /app si es relevante
            checked_paths = set()
            loaded_env = False
            for env_path in possible_paths:
                # Asegurarse de que la ruta es absoluta y dentro de lo esperado
                abs_env_path = os.path.abspath(env_path)
                if abs_env_path in checked_paths:
                    continue # Evitar revisar el mismo path dos veces
                checked_paths.add(abs_env_path)

                if os.path.exists(abs_env_path) and os.path.isfile(abs_env_path):
                    logger.info(f"Intentando cargar .env desde: {abs_env_path}")
                    # load_dotenv sobrescribe por defecto; override=True asegura que .env > entorno
                    if load_dotenv(abs_env_path, override=True):
                        logger.info(f".env cargado desde: {abs_env_path}")
                        # Volver a intentar obtener la clave DESPUÉS de cargar
                        api_key_from_env = os.getenv("LLM_API_KEY")
                        if api_key_from_env:
                            api_key = api_key_from_env # Asignar si se encontró
                            logger.info("API key cargada correctamente desde .env")
                            loaded_env = True
                            break # Salir si encontramos la clave
                        else:
                             logger.warning(f"Archivo .env encontrado en {abs_env_path}, pero no contiene LLM_API_KEY.")
                    else:
                         logger.warning(f"No se pudo cargar el archivo .env desde {abs_env_path} (puede estar vacío o tener errores).")
                else:
                    logger.debug(f"Archivo .env no encontrado o no es un fichero en: {abs_env_path}")

            if not loaded_env and not api_key: # Si ni .env ni variable de entorno funcionaron
                 logger.warning("No se encontró archivo .env válido con LLM_API_KEY en las rutas buscadas.")

        except ImportError:
            logger.warning("'python-dotenv' no instalado. No se puede buscar archivos .env.")
        except Exception as e:
            logger.error(f"Error cargando .env: {e}", exc_info=True)

    # ELIMINADO: Bloque que usaba la clave hardcodeada

    # Registrar información útil para depuración
    if api_key:
        # Mostrar sólo una parte de la clave por seguridad
        logger.info(f"API KEY encontrada (parcial): '{api_key[:4]}...{api_key[-4:]}'")
    else:
        # Advertencia MUY importante si no hay clave
        logger.error("🚨 ¡ALERTA! No se encontró LLM_API_KEY. El chatbot NO funcionará.")

    return {
        "model": os.getenv("LLM_MODEL", DEFAULT_MODEL),
        "api_key": api_key, # Devolver la clave (o None si no se encontró)
        "temperature": float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE)),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
        "timeout": int(os.getenv("LLM_TIMEOUT", 60)), # Aumentado timeout por defecto
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", 2)) # Reducido retries por defecto
    }

def get_llm():
    """
    Obtiene una instancia configurada del LLM.

    Returns:
        Instancia de ChatDeepSeek configurada o None si falta la API key.
    """
    config = get_config()
    api_key = config.get("api_key") # Usar .get() para evitar KeyError si no está

    if not api_key:
        logger.error("⚠️ LLM_API_KEY no está configurada. No se puede inicializar el LLM.")
        # Considera si quieres devolver None o lanzar una excepción
        # Devolver None permite que la aplicación arranque pero falle en tiempo de ejecución
        # Lanzar excepción detiene el arranque si el LLM es esencial
        # raise ValueError("LLM_API_KEY no está configurada. No se puede inicializar el LLM.")
        return None # Devolvemos None para permitir el arranque pero indicar fallo

    try:
        # No pasar api_key en config si es None, aunque ChatDeepSeek podría manejarlo
        llm_config = {k: v for k, v in config.items() if k != "api_key" and v is not None}
        logger.info(f"Inicializando ChatDeepSeek con configuración: model={llm_config.get('model')}, temp={llm_config.get('temperature')}, timeout={llm_config.get('timeout')}")
        # Asegúrate de que langchain_deepseek está instalado (debería estar por requirements.txt)
        return ChatDeepSeek(
            api_key=api_key,
            **llm_config
        )
    except NameError:
         logger.error("Error: ChatDeepSeek no está definido. ¿Falta 'pip install langchain-deepseek' o hay un error de importación?", exc_info=True)
         return None
    except Exception as e:
        logger.error(f"Error al inicializar ChatDeepSeek: {str(e)}", exc_info=True)
        # Puedes devolver None o relanzar la excepción
        # raise e
        return None