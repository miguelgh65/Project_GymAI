# telegram/gym/config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'postgres_gymdb'),
    'port': os.getenv('DB_PORT', '5432'),
    'options': f'-c search_path=gym,public'  # Añadir búsqueda en esquema 'gym'
}

# URL base para la API
BASE_URL = os.getenv('API_BASE_URL', "http://localhost:5050")

# ID por defecto (solo para casos extremos donde no se puede obtener ningún ID)
DEFAULT_USER_ID = os.getenv('DEFAULT_USER_ID', "unknown_user")

# Rutas de archivos
WHITELIST_PATH = os.path.join(os.path.dirname(__file__), "whitelist.txt")
PETICIONES_PATH = os.path.join(os.path.dirname(__file__), "peticiones.txt")

# Frases motivacionales al estilo de Ronnie Coleman
MOTIVATIONAL_PHRASES = [
    "¡YEAH BUDDY! ¡LIGHTWEIGHT BABY!",
    "¡BOOM! ¡AIN'T NOTHIN' BUT A PEANUT!",
    "¡WHOOOOOO! ¡EVERYBODY WANNA BE A BODYBUILDER!",
    "¡BRUTAL! ¡LIGHTWEIGHT, BABY, LIGHTWEIGHT!",
    "¡NADIE QUIERE LEVANTAR ESTE PESO PESADO PERO YO SÍ!",
    "¡TIME TO BLEED! ¡NO PAIN, NO GAIN!",
    "¡BOOM! ¡HICISTE ESO! ¡NO EXCUSES, ONLY RESULTS!",
    "¡OOOH YEAH! ¡ERES UNA MÁQUINA!",
    "¡YEP YEP! ¡NOTHING TO IT BUT TO DO IT!",
]

# Frases para errores
ERROR_PHRASES = [
    "¡WHOOPS! ¡ESO FUE MÁS PESADO DE LO ESPERADO! Error al registrar. ¡VAMOS A INTENTARLO DE NUEVO, BABY!",
    "¡OOOH! ¡PARECE QUE NECESITAMOS MÁS FUERZA PARA ESTE REGISTRO!",
    "¡UH OH! ¡ESTE PESO SE RESISTE! No se pudo registrar tu ejercicio. ¡VAMOS DE NUEVO!",
    "¡EVERYBODY WANTS TO REGISTER, BUT SOMETIMES THE SERVER SAYS NO!",
    "¡AIN'T NOTHING BUT A SERVER ERROR, BABY! Intentémoslo de nuevo. ¡LIGHTWEIGHT!",
]

class UserID:
    """Clase para manejar ambos tipos de IDs: Telegram y Google"""
    def __init__(self, telegram_id, google_id=None):
        self.telegram_id = telegram_id  # Para comunicación con Telegram
        self.google_id = google_id      # Para comunicación con la API interna
        
    def __str__(self):
        """Para usar el ID en la API interna"""
        return self.google_id if self.google_id else self.telegram_id
        
    def get_telegram_id(self):
        """Obtiene el ID para usar con Telegram"""
        return self.telegram_id