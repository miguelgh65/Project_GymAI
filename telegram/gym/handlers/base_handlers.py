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
            print(f"🔍 Mensaje recibido: {message.text}")
            print(f"👤 Usuario: {message.from_user.id}")
            log_to_console(f"Mensaje recibido: {message.text} de usuario {message.from_user.id}")

            # Verificación de whitelist
            user_id = str(message.from_user.id)
            
            # Verificar contenido de whitelist
            try:
                with open(WHITELIST_PATH, "r") as f:
                    whitelist_contents = f.read().strip().split('\n')
                    whitelist_contents = [w.strip() for w in whitelist_contents]
                
                if user_id not in whitelist_contents:
                    print(f"❌ Usuario {user_id} NO está en whitelist")
                    log_denied_access(user_id, message.text)
                    bot_instance.send_message(
                        message.chat.id,
                        f"🔒 Acceso denegado. Tu ID de Telegram es: {user_id}\n"
                        "Contacta al administrador para obtener acceso."
                    )
                    return False
                else:
                    print(f"✅ Usuario {user_id} está en whitelist")
                    return True
            
            except Exception as e:
                log_to_console(f"Error al verificar whitelist: {e}", "ERROR")
                return False

        except Exception as e:
            log_to_console(f"Error en middleware: {e}", "ERROR")
            return False

def get_telegram_id(message):
    """Obtiene el ID de chat de Telegram del mensaje"""
    return message.chat.id

def get_api_user_id(message):
    """
    Obtiene el ID para usar en la API (Google ID si está vinculado,
    de lo contrario, el ID de Telegram).
    """
    # Primero intentamos obtener el Google ID
    google_id = get_google_id(message.chat.id)
    
    # Registrar información en logs para depuración
    log_to_console(f"get_api_user_id - Telegram ID: {message.chat.id}, Google ID: {google_id}", "INFO")
    
    # Si no se encuentra el Google ID, usamos el ID de Telegram
    return str(google_id)

def get_telegram_headers():
    """Devuelve las cabeceras necesarias para autenticarse como bot de Telegram."""
    return {
        'Content-Type': 'application/json',
        'X-Telegram-Bot-Token': TELEGRAM_BOT_API_TOKEN
    }

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
    # Añadir logging a archivo si es necesario
    logging.info(message)

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
            whitelist = {line.strip() for line in f if line.strip()}
        
        is_allowed = str(user_id) in whitelist
        log_to_console(f"Usuario {user_id} {'está' if is_allowed else 'NO está'} en la lista blanca", "INFO")
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
        is_allowed = str(user_id) in whitelist_contents.split('\n')
        
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
            return False
    except Exception as e:
        print(f"❌ Error en check_whitelist: {e}")
        return False