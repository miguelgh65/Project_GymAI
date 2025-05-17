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
# Lista de ejercicios conocidos (en minúsculas y sin acentos)
KNOWN_EXERCISES = {
    # Ejercicios de pecho
    "press banca": "press banca",
    "press banca inclinado": "press banca inclinado",
    "press banca declinado": "press banca declinado",
    "aperturas con mancuernas": "aperturas con mancuernas",
    "aperturas inclinadas": "aperturas inclinadas",
    "contractor pecho": "contractor pecho",
    "pec deck": "contractor pecho",
    "aperturas en maquina": "contractor pecho",
    "pullover": "pullover",
    "flexiones": "flexiones",
    "fondos en paralelas": "fondos en paralelas",
    "press mancuernas": "press mancuernas",
    "press mancuernas inclinado": "press mancuernas inclinado",
    "press mancuernas plano": "press mancuernas plano",
    "crossover cables": "crossover cables",
    "press en maquina": "press en maquina",
    "press hammer": "press hammer",
    
    # Ejercicios de espalda
    "dominadas": "dominadas",
    "jalon al pecho": "jalon al pecho",
    "jalon agarre estrecho": "jalon agarre estrecho",
    "jalon al pecho agarre cerrado": "jalon agarre estrecho",
    "jalon al pecho agarre abierto": "jalon al pecho",
    "maquina dominadas": "maquina dominadas",
    "remo en maquina": "remo en maquina",
    "remo con barra": "remo con barra",
    "remo mancuerna": "remo mancuerna",
    "remo en t": "remo en t",
    "remo agarre estrecho": "remo agarre estrecho",
    "peso muerto": "peso muerto",
    "peso muerto rumano": "peso muerto rumano",
    "buenos dias": "buenos dias",
    "hiperextensiones": "hiperextensiones",
    "pull ups": "dominadas",
    "remo con polea baja": "remo con polea baja",
    "batman": "batman",
    "pull down": "jalon al pecho",
    "face pull": "face pull",
    
    # Ejercicios de hombros
    "press militar": "press militar",
    "press de hombros": "press militar",
    "press hombros": "press militar",
    "press arnold": "press arnold",
    "elevaciones laterales": "elevaciones laterales",
    "elevaciones frontales": "elevaciones frontales",
    "elevaciones posteriores": "elevaciones posteriores",
    "pajaro": "elevaciones posteriores",
    "remo alto": "remo alto",
    "encogimientos": "encogimientos",
    "encogimientos de hombros": "encogimientos",
    "press militar con mancuernas": "press militar con mancuernas",
    "elevaciones 180": "elevaciones 180",
    "deltoides": "elevaciones laterales",
    "press sentado": "press sentado",
    "press hombros maquina": "press hombros maquina",
    
    # Ejercicios de brazos
    "biceps": "biceps",
    "curl biceps": "curl biceps",
    "curl de biceps con barra": "curl biceps con barra",
    "curl con barra": "curl biceps con barra",
    "curl martillo": "curl martillo",
    "martillo": "curl martillo",
    "curl predicador": "curl predicador",
    "predicador": "curl predicador",
    "curl concentrado": "curl concentrado",
    "maquina de biceps": "maquina de biceps",
    "biceps en maquina": "maquina de biceps",
    "biceps en polea": "biceps en polea",
    "curl scott": "curl scott",
    "scott": "curl scott",
    "curl 21": "curl 21",
    "curl de biceps con polea": "curl de biceps con polea",
    "curl spider": "curl spider",
    "triceps": "triceps",
    "triceps en polea": "triceps en polea",
    "trices en polea": "triceps en polea",
    "extension triceps polea": "triceps en polea",
    "press frances": "press frances",
    "frances": "press frances",
    "fondos": "fondos",
    "patada de triceps": "patada de triceps",
    "extension de triceps": "extension de triceps",
    "triceps en banco": "triceps en banco",
    "triceps con mancuernas": "triceps con mancuernas",
    "triceps en maquina": "triceps en maquina",
    "press cerrado": "press cerrado",
    "skull crusher": "skull crusher",
    "extension vertical": "extension vertical",
    "overhead extension": "extension vertical",
    "barras paralelas": "barras paralelas",
    "kickback": "patada de triceps",
    
    # Ejercicios de piernas
    "sentadilla": "sentadilla",
    "squat": "sentadilla",
    "prensa": "prensa",
    "leg press": "prensa",
    "sentadilla hack": "sentadilla hack",
    "hack": "sentadilla hack",
    "extension de cuadriceps": "extension de cuadriceps",
    "curl femoral": "curl femoral",
    "curl de femoral": "curl femoral",
    "femoral": "curl femoral",
    "femoral tumbado": "femoral tumbado",
    "femoral sentado": "femoral sentado",
    "gemelos": "gemelos",
    "elevacion de gemelos": "elevacion de gemelos",
    "elevacion de talones": "elevacion de talones",
    "pantorrillas": "gemelos",
    "extensiones de gemelos": "gemelos",
    "aductores": "aductores",
    "abductores": "abductores",
    "gluteos": "gluteos",
    "hip thrust": "hip thrust",
    "peso muerto sumo": "peso muerto sumo",
    "lunges": "lunges",
    "zancadas": "zancadas",
    "sentadilla bulgara": "sentadilla bulgara",
    "pistol squat": "pistol squat",
    "split squat": "split squat",
    "sentadilla frontal": "sentadilla frontal",
    "front squat": "sentadilla frontal",
    "sissy squat": "sissy squat",
    "goblet squat": "goblet squat",
    "leg extension": "extension de cuadriceps",
    "extension de piernas": "extension de cuadriceps",
    "leg curl": "curl femoral",
    "buenos dias": "buenos dias",
    "tijeras": "zancadas",
    
    # Ejercicios de abdominales
    "abdominales": "abdominales",
    "crunch": "crunch",
    "crunch abdominal": "crunch",
    "elevacion de piernas": "elevacion de piernas",
    "hanging leg raises": "elevacion de piernas",
    "russian twist": "russian twist",
    "plancha": "plancha",
    "plank": "plancha",
    "plancha lateral": "plancha lateral",
    "side plank": "plancha lateral",
    "abs": "abdominales",
    "rueda abdominal": "rueda abdominal",
    "rueda": "rueda abdominal",
    "mountain climbers": "mountain climbers",
    "escaladores": "mountain climbers",
    "v ups": "v ups",
    "abdominal v": "v ups",
    "dragon flag": "dragon flag",
    "ab roller": "rueda abdominal",
    "abdominal en maquina": "abdominal en maquina",
    "hollow hold": "hollow hold",
    "scissors": "tijeras abdominales",
    "tijeras abdominales": "tijeras abdominales",
    "abdominals": "abdominales",
    "crunches": "crunch",
    "lower abs": "lower abs",
    "sit ups": "sit ups",
    
    # Ejercicios de cardio
    "natacion": "natacion",
    "piscina": "natacion",
    "correr": "correr",
    "running": "correr",
    "trote": "correr",
    "footing": "correr",
    "carrera": "correr",
    "bicicleta": "bicicleta",
    "cycling": "bicicleta",
    "ciclismo": "bicicleta",
    "spinning": "spinning",
    "boxeo": "boxeo",
    "boxing": "boxeo",
    "cuerda": "cuerda",
    "salto cuerda": "salto cuerda",
    "jump rope": "salto cuerda",
    "eliptica": "eliptica",
    "remo cardio": "remo cardio",
    "rowing": "remo cardio",
    "sprints": "sprints",
    "hiit": "hiit",
    "steps": "steps",
    "zumba": "zumba",
    "aerobics": "aerobics",
    "caminar": "caminar",
    "walking": "caminar",
    "cinta": "cinta",
    "treadmill": "cinta",
    "burpees": "burpees",
    "stairmaster": "stairmaster",
    "escalones": "stairmaster",
    "skipping": "skipping",
    "aerobic": "aerobic",
    "jumping jacks": "jumping jacks",
    "mountain climbers": "mountain climbers",
    
    # Ejercicios funcionales
    "kettelbell swing": "kettelbell swing",
    "kettelbell": "kettelbell",
    "battle rope": "battle rope",
    "landmine": "landmine",
    "clean": "clean",
    "clean and jerk": "clean and jerk",
    "snatch": "snatch",
    "arrancada": "snatch",
    "dos tiempos": "clean and jerk",
    "thruster": "thruster",
    "wall ball": "wall ball",
    "ball slams": "ball slams",
    "slams": "ball slams",
    "tire flip": "tire flip",
    "box jumps": "box jumps",
    "salto al cajon": "box jumps",
    "pull ups": "pull ups",
    "muscle up": "muscle up",
    "handstand": "handstand",
    "pino": "handstand",
    "squat jumps": "squat jumps",
    "saltos": "squat jumps",
    "farmer walk": "farmer walk",
    "caminata del granjero": "farmer walk",
    "turkish get up": "turkish get up",
    "get up": "turkish get up",
    "overhead press": "overhead press",
    "overhead squat": "overhead squat",
    "prowler": "prowler",
    "bear crawl": "bear crawl",
    "trx": "trx",
    "suspension": "trx",
    "battle rope": "battle rope",
    "medicine ball": "medicine ball",
    "plyo push up": "plyo push up",
    "flexiones pliometricas": "plyo push up"
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