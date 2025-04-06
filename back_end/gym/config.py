import os
import logging
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek # Asegúrate que está instalado

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

# Deshabilitar tracing de Langchain si no se usa explícitamente
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
if os.environ["LANGCHAIN_TRACING_V2"] == "true":
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "")
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "")
    logger.info("LangChain tracing habilitado.")
else:
    os.environ["LANGCHAIN_ENDPOINT"] = ""
    os.environ["LANGCHAIN_API_KEY"] = ""
    os.environ["LANGCHAIN_PROJECT"] = ""
    logger.info("LangChain tracing deshabilitado.")

# Cargar las variables del archivo .env
# load_dotenv() buscará .env en el directorio actual o directorios padre
if load_dotenv():
    logger.info("Variables de entorno cargadas desde archivo .env")
else:
    logger.warning("Archivo .env no encontrado o vacío. Usando variables de entorno del sistema.")

# Configuración de la base de datos usando las variables de entorno
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'postgres_gymdb'), # Default para Docker Compose?
    'port': os.getenv('DB_PORT', '5432'),
    'options': f'-c search_path={os.getenv("DB_SCHEMA", "gym")},public' # Esquema configurable
}

# Verificar que las variables esenciales de DB estén presentes
if not all([DB_CONFIG['dbname'], DB_CONFIG['user'], DB_CONFIG['password'], DB_CONFIG['host'], DB_CONFIG['port']]):
    logger.error("Faltan variables de entorno esenciales para la base de datos (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT).")
    # Considera lanzar un error si la BD es indispensable: raise EnvironmentError("Faltan variables de BD")

# Configuración de Fitbit
FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID')
FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET')
FITBIT_REDIRECT_URI = os.getenv('FITBIT_REDIRECT_URI') # Ej: http://localhost:5050/api/fitbit/callback
FITBIT_CONFIG = {
    'client_id': FITBIT_CLIENT_ID,
    'client_secret': FITBIT_CLIENT_SECRET,
    'auth_url': os.getenv('FITBIT_AUTH_URL', 'https://www.fitbit.com/oauth2/authorize'),
    'token_url': os.getenv('FITBIT_TOKEN_URL', 'https://api.fitbit.com/oauth2/token'),
    'profile_url': os.getenv('FITBIT_PROFILE_URL', 'https://api.fitbit.com/1/user/-/profile.json'),
    'redirect_uri': FITBIT_REDIRECT_URI
}
if not all([FITBIT_CONFIG['client_id'], FITBIT_CONFIG['client_secret'], FITBIT_CONFIG['redirect_uri']]):
     logger.warning("Faltan variables de entorno para Fitbit (FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET, FITBIT_REDIRECT_URI). La integración con Fitbit podría no funcionar.")

# Configuración de Google OAuth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI') # Ej: http://localhost:5050/api/auth/google/callback (si usaras flujo server-side completo)
GOOGLE_CONFIG = {
    'client_id': GOOGLE_CLIENT_ID,
    'client_secret': GOOGLE_CLIENT_SECRET,
    'redirect_uri': GOOGLE_REDIRECT_URI, # No usado en flujo de token ID desde frontend
    'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
    'token_url': 'https://oauth2.googleapis.com/token'
}
if not GOOGLE_CONFIG['client_id']:
     logger.warning("Falta variable de entorno GOOGLE_CLIENT_ID. El login con Google no funcionará.")

# Lista de ejercicios conocidos (en minúsculas y sin acentos)
# Considera cargar esto desde un archivo o base de datos si la lista crece mucho
KNOWN_EXERCISES = {
    # Ejercicios originales
    "natacion": "natacion",
    "piscina": "piscina", # Podría mapear a natacion?
    "correr": "correr",
    "dominadas": "dominadas",
    "jalon agarre estrecho": "jalon agarre estrecho",
    "maquina dominadas": "maquina dominadas",
    "remo en maquina": "remo en maquina",
    "remo agarre estrecho": "remo agarre estrecho",
    "press banca": "press banca",
    "contractor pecho": "contractor pecho", # o Pec Deck, Aperturas en máquina
    "press militar": "press militar", # o press de hombros con barra
    "triceps en polea": "triceps en polea", # o extensión de tríceps en polea
    "elevaciones frontales": "elevaciones frontales",
    "maquina de biceps": "maquina de biceps", # o curl de bíceps en máquina
    "press banca inclinado": "press banca inclinado",
    "deltoides": "deltoides", # Muy genérico, ¿se refiere a elevaciones laterales?
    "biceps": "biceps",       # Muy genérico, ¿se refiere a curl con barra/mancuernas?
    # Añadir más ejercicios aquí si es necesario
}
logger.info(f"Cargados {len(KNOWN_EXERCISES)} ejercicios conocidos.")

# Configuración del LLM con DeepSeek usando las variables de entorno
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-chat') # Modelo por defecto
llm = None
if LLM_API_KEY:
    try:
        llm = ChatDeepSeek(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            temperature=float(os.getenv('LLM_TEMPERATURE', 0.2)),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', 1024)),
            # El timeout por defecto en httpx es 5 segundos, puede ser poco
            # request_timeout=int(os.getenv('LLM_TIMEOUT', 30)), # Ajustado en versiones recientes? Verificar doc
            max_retries=int(os.getenv('LLM_MAX_RETRIES', 2)) # Reducir retries por defecto
        )
        logger.info(f"LLM ({LLM_MODEL}) configurado correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar el LLM ({LLM_MODEL}): {e}", exc_info=True)
        llm = None # Asegurar que llm es None si falla la inicialización
else:
    logger.warning("LLM_API_KEY no encontrada en .env. Las funciones de IA no estarán disponibles.")
    llm = None


# Clave secreta para SessionMiddleware
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    logger.warning("SECRET_KEY no definida en .env. Usando valor temporal (inseguro para producción).")
    SECRET_KEY = os.urandom(24).hex() # Genera una temporal si no existe