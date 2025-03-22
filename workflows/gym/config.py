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
    
    # Ejercicios de fuerza/resistencia adicionales
    "sentadillas": "sentadillas",
    "peso muerto": "peso muerto",
    "prensa de piernas": "prensa de piernas",
    "extensiones de piernas": "extensiones de piernas",
    "curl de piernas": "curl de piernas",
    "abdominales": "abdominales",
    "elevaciones laterales": "elevaciones laterales",
    "face pulls": "face pulls",
    "remo con barra": "remo con barra",
    "press de hombros": "press de hombros",
    "fondos de triceps": "fondos de triceps",
    "encogimientos de hombros": "encogimientos de hombros",
    "elevaciones de gemelos": "elevaciones de gemelos",
    "hip thrust": "hip thrust",
    "peso muerto rumano": "peso muerto rumano",
    "peso muerto sumo": "peso muerto sumo",
    "good mornings": "good mornings",
    "planchas": "planchas",
    "burpees": "burpees",
    "box jumps": "box jumps",
    "saltos de cuerda": "saltos de cuerda",
    "bicicleta estacionaria": "bicicleta estacionaria",
    "escaladora": "escaladora",
    "eliptica": "eliptica",
    "zancadas": "zancadas",
    "step-ups": "step-ups",
    "aductores": "aductores",
    "curl femoral": "curl femoral",
    "press de pecho en maquina": "press de pecho en maquina",
    "pec fly": "pec fly",
    "elevaciones posteriores": "elevaciones posteriores",
    "remo con mancuerna": "remo con mancuerna",
    "crunch inverso": "crunch inverso",
    "plancha lateral": "plancha lateral",
    
    # Ejercicios de cardio
    "caminata": "caminata",
    "spinning": "spinning",
    "carrera en cinta": "carrera en cinta",
    "aerobicos": "aerobicos",
    "kickboxing": "kickboxing",
    "bicicleta al aire libre": "bicicleta al aire libre",
    "futbol": "futbol",
    "sprints": "sprints",
    "ciclismo": "ciclismo",
    "step aerobics": "step aerobics",
    "intervalos de alta intensidad": "intervalos de alta intensidad"
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
