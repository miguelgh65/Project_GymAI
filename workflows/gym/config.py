import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

# Cargar las variables del archivo .env
load_dotenv()
# Configuración de la base de datos usando las variables de entorno
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'postgres_gymdb'),
    'port': os.getenv('DB_PORT', '5432')
}

# Configuración de Fitbit
FITBIT_CONFIG = {
    'client_id': os.getenv('FITBIT_CLIENT_ID'),
    'client_secret': os.getenv('FITBIT_CLIENT_SECRET'),
    'auth_url': 'https://www.fitbit.com/oauth2/authorize',
    'token_url': 'https://api.fitbit.com/oauth2/token',
    'profile_url': 'https://api.fitbit.com/1/user/-/profile.json',
    'redirect_uri': os.getenv('FITBIT_REDIRECT_URI', 'http://localhost:5050/fitbit-callback')
}

# Lista de ejercicios conocidos (en minúsculas y sin acentos)
KNOWN_EXERCISES = {
    # Ejercicios originales
    "natacion": "natacion",
    "piscina": "piscina",
    "correr": "correr",
    "dominadas": "dominadas",
    "jalon agarre estrecho": "jalon agarre estrecho",
    "maquina dominadas": "maquina dominadas",
    "remo en maquina": "remo en maquina",
    "remo agarre estrecho": "remo agarre estrecho",
    "press banca": "press banca",
    "contractor pecho": "contractor pecho",
    "press militar": "press militar",
    "triceps en polea": "triceps en polea",
    "elevaciones frontales": "elevaciones frontales",
    "maquina de biceps": "maquina de biceps",
    "press banca inclinado": "press banca inclinado",
    "deltoides": "deltoides",
    "biceps": "biceps",
    
    # Resto de ejercicios...
}

# Configuración del LLM con DeepSeek usando las variables de entorno
llm = ChatDeepSeek(
    model=os.getenv('LLM_MODEL'),
    api_key=os.getenv('LLM_API_KEY'),
    temperature=float(os.getenv('LLM_TEMPERATURE', 0.2)),
    max_tokens=int(os.getenv('LLM_MAX_TOKENS', 1024)),
    timeout=int(os.getenv('LLM_TIMEOUT', 30)),
    max_retries=int(os.getenv('LLM_MAX_RETRIES', 5))
)

# Clave secreta para Flask (si no la tienes ya configurada en otro lugar)
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())