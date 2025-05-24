# telegram/gym/handlers/base_handlers.py
import os
import logging
import psycopg2
import requests
from datetime import datetime
from dotenv import load_dotenv
from config import COLORS, LOG_COLORS, WHITELIST_PATH, PETICIONES_PATH, DB_CONFIG

# Cargar variables de entorno
load_dotenv()

# Obtener el token de autenticación para el bot
TELEGRAM_BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
if not TELEGRAM_BOT_API_TOKEN:
    logging.warning("⚠️ TELEGRAM_BOT_API_TOKEN no está configurado en el archivo .env")

def get_google_id(telegram_id):
    """
    Retrieves the Google ID for a given Telegram ID by querying the users table.
    
    Args:
        telegram_id (str): Telegram user ID
    
    Returns:
        str: Google ID or Telegram ID if no match found
    """
    try:
        # Establish a connection to the database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Query to find the Google ID for the given Telegram ID
        query = """
        SELECT google_id 
        FROM users 
        WHERE telegram_id = %s
        """
        
        cursor.execute(query, (str(telegram_id),))
        
        # Fetch the result
        result = cursor.fetchone()
        
        # Close database connections
        cursor.close()
        conn.close()

        # Return Google ID if found, otherwise return Telegram ID
        return result[0] if result and result[0] else str(telegram_id)

    except (psycopg2.Error, Exception) as e:
        # Log the error and return Telegram ID as fallback
        log_to_console(f"Error retrieving Google ID: {str(e)}", "ERROR")
        return str(telegram_id)

def register_middleware(bot):
    """
    Registra middleware para logging y autenticación
    """
    # Middleware de depuración y verificación de whitelist
    @bot.middleware_handler(update_types=['message'])
    def debug_whitelist_middleware(bot_instance, message):
        try:
            # Registro de depuración
            print(f"🔍 Mensaje recibido: {message.text if hasattr(message, 'text') else 'Sin texto'}")
            print(f"👤 Usuario: {message.from_user.id if hasattr(message, 'from_user') and message.from_user else 'Unknown'}")
            log_to_console(f"Mensaje recibido: {message.text if hasattr(message, 'text') else 'Sin texto'} de usuario {message.from_user.id if hasattr(message, 'from_user') and message.from_user else 'Unknown'}")
            
            # NO HACER VERIFICACIÓN DE WHITELIST AQUÍ
            # La verificación solo debe hacerse en cada handler
        except Exception as e:
            log_to_console(f"Error en middleware: {e}", "ERROR")

def get_telegram_id(message):
    """Obtiene el ID de chat de Telegram del mensaje"""
    return message.chat.id if hasattr(message, 'chat') else None

def get_api_user_id(message):
    """
    Obtiene el ID para usar en la API (Google ID si está vinculado,
    de lo contrario, el ID de Telegram).
    """
    # Primero intentamos obtener el Google ID
    chat_id = get_telegram_id(message)
    if not chat_id:
        log_to_console("No se pudo obtener chat_id del mensaje", "ERROR")
        return None
        
    google_id = get_google_id(chat_id)
    
    # Registrar información en logs para depuración
    log_to_console(f"get_api_user_id - Telegram ID: {chat_id}, Google ID: {google_id}", "INFO")
    
    # Si no se encuentra el Google ID, usamos el ID de Telegram
    return str(google_id)

def get_telegram_headers():
    """Devuelve las cabeceras necesarias para autenticarse como bot de Telegram."""
    if not TELEGRAM_BOT_API_TOKEN:
        log_to_console("Token de Telegram no configurado", "ERROR")
    
    headers = {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Token': TELEGRAM_BOT_API_TOKEN
    }
    
    # Log para verificar que el token se está enviando (sin mostrar el token completo)
    if TELEGRAM_BOT_API_TOKEN:
        token_preview = TELEGRAM_BOT_API_TOKEN[:5] + "..." + TELEGRAM_BOT_API_TOKEN[-5:] if len(TELEGRAM_BOT_API_TOKEN) > 10 else "***"
        log_to_console(f"Generando headers con token: {token_preview}", "DEBUG")
    
    return headers

def log_to_console(message, level="INFO"):
    """
    Registra un mensaje en la consola con formato y colores.
    Args:
        message: El mensaje a mostrar
        level: Nivel del mensaje (ERROR, WARNING, INFO, etc.)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Usar colores si están disponibles
    if color_enabled():
        color = LOG_COLORS.get(level, COLORS["RESET"])
        formatted_message = f"{COLORS['YELLOW']}[{now}]{COLORS['RESET']} {color}[{level}]{COLORS['RESET']} {message}"
    else:
        formatted_message = f"[{now}] [{level}] {message}"
    
    print(formatted_message, flush=True)
    # Añadir logging a archivo
    getattr(logging, level.lower(), logging.info)(message)

def color_enabled():
    """Comprueba si los colores en la consola están disponibles."""
    return True  # Para desarrollo, siempre habilitar colores

def is_user_whitelisted(user_id):
    """
    Verifica si el id del usuario (user_id) está en la whitelist.
    Se asume que 'whitelist.txt' contiene un id por línea.
    """
    log_to_console(f"Verificando acceso para usuario {user_id}", "PROCESS")
    
    try:
        if not os.path.exists(WHITELIST_PATH):
            log_to_console(f"¡Archivo {WHITELIST_PATH} no encontrado!", "ERROR")
            return False
            
        with open(WHITELIST_PATH, "r") as f:
            whitelist_content = f.read().strip()
            whitelist = whitelist_content.split('\n')
            whitelist = [w.strip() for w in whitelist if w.strip()]
        
        is_allowed = str(user_id) in whitelist
        log_to_console(f"Usuario {user_id} {'está' if is_allowed else 'NO está'} en la lista blanca. Whitelist: {whitelist}", "INFO")
        return is_allowed
        
    except Exception as e:
        # Si ocurre algún error, se niega el acceso por seguridad.
        log_to_console(f"Error al leer {WHITELIST_PATH}: {e}", "ERROR")
        return False

def log_denied_access(user_id, message_text):
    """
    Registra en 'peticiones.txt' el intento de acceso denegado con la fecha, id y texto del mensaje.
    """
    try:
        with open(PETICIONES_PATH, "a") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{now} - Acceso denegado para usuario {user_id}: {message_text}\n"
            f.write(log_entry)
            log_to_console(f"Registro guardado en peticiones.txt", "INFO")
    except Exception as e:
        log_to_console(f"Error al registrar en peticiones.txt: {e}", "ERROR")

def check_whitelist(message, bot):
    """
    Verifica si un usuario está en la whitelist y maneja el acceso
    """
    try:
        # Imprimir información detallada del mensaje
        print(f"🔍 Mensaje completo: {message}")
        print(f"🆔 Chat ID: {message.chat.id}")
        print(f"👤 Usuario: {message.from_user}")
        
        user_id = message.chat.id
        print(f"🔍 Verificando whitelist para usuario {user_id}")
        
        # Verificar contenido de whitelist
        with open(WHITELIST_PATH, "r") as f:
            whitelist_contents = f.read().strip()
            print(f"📋 Contenido de whitelist: '{whitelist_contents}'")
        
        # Convertir a cadena y comparar
        whitelist_ids = [line.strip() for line in whitelist_contents.split('\n') if line.strip()]
        user_id_str = str(user_id)
        
        print(f"🔍 IDs en whitelist: {whitelist_ids}")
        print(f"🔍 ID usuario actual: {user_id_str}")
        
        is_allowed = user_id_str in whitelist_ids
        
        print(f"✅ ¿Usuario {user_id_str} está en whitelist? {is_allowed}")
        
        if is_allowed:
            print(f"✅ Usuario {user_id} está en whitelist")
            return True
        else:
            print(f"❌ Usuario {user_id} NO está en whitelist")
            bot.send_message(
                user_id,
                f"🔒 Acceso denegado. Tu ID de Telegram es: {user_id}\n"
                "Contacta al administrador para obtener acceso."
            )
            log_denied_access(user_id, "Intento de acceso - check_whitelist")
            return False
    except Exception as e:
        print(f"❌ Error en check_whitelist: {e}")
        logging.exception("Error completo en check_whitelist:")
        # En caso de error, permitimos acceso
        return True