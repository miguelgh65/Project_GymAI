# telegram/gym/handlers/base_handlers.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from telebot.types import Message
from utils import (
    send_message_split,
    is_user_whitelisted,
    log_denied_access,
    log_to_console,
)
from config import DB_CONFIG, DEFAULT_USER_ID, WHITELIST_PATH

def get_google_id(message: Message) -> str:
    """
    Busca el ID de Google asociado con el ID de Telegram.
    Este ID se usa para peticiones a la API y operaciones de base de datos.
    
    Args:
        message: Mensaje de Telegram
        
    Returns:
        str: ID de Google si existe, o ID de Telegram como fallback
    """
    try:
        telegram_id = str(message.chat.id)
        
        # Intentar obtener el Google ID asociado a este Telegram ID
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Buscar el usuario por su Telegram ID
            cur.execute("SELECT google_id FROM users WHERE telegram_id = %s", (telegram_id,))
            result = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if result and result[0]:
                # Si encontramos un Google ID, lo usamos
                google_id = result[0]
                log_to_console(f"Encontrado Google ID ({google_id}) para Telegram ID {telegram_id}", "INFO")
                return google_id
            else:
                # Si no encontramos un Google ID, usamos el Telegram ID
                log_to_console(f"No se encontró Google ID para Telegram ID {telegram_id}", "WARNING")
                return telegram_id
                
        except Exception as e:
            log_to_console(f"Error al buscar Google ID para Telegram ID {telegram_id}: {e}", "ERROR")
            return telegram_id
            
    except AttributeError:
        log_to_console("No se pudo obtener el chat ID del mensaje", "ERROR")
        # En caso de error, devolvemos el ID de Telegram (si podemos obtenerlo)
        if hasattr(message, 'from_user') and message.from_user and message.from_user.id:
            return str(message.from_user.id)
        else:
            # Solo como último recurso usamos el ID por defecto
            return DEFAULT_USER_ID

def get_telegram_id(message: Message) -> str:
    """
    Obtiene el ID de Telegram del mensaje.
    Este ID se usa para enviar mensajes a través de Telegram.
    
    Args:
        message: Mensaje de Telegram
        
    Returns:
        str: ID de Telegram
    """
    try:
        return str(message.chat.id)
    except AttributeError:
        log_to_console("No se pudo obtener el Telegram ID del mensaje", "ERROR")
        if hasattr(message, 'from_user') and message.from_user and message.from_user.id:
            return str(message.from_user.id)
        else:
            return "unknown_user"

# Por retrocompatibilidad, mantenemos get_chat_id como alias de get_google_id
get_chat_id = get_google_id

def check_whitelist(message: Message, bot) -> bool:
    """
    Verifica si el usuario está en la lista blanca.
    
    Args:
        message: Mensaje de Telegram
        bot: Instancia del bot
        
    Returns:
        bool: True si el usuario está en la lista blanca, False en caso contrario
    """
    chat_id = get_telegram_id(message)  # Usamos el Telegram ID para verificar la whitelist
    
    if not is_user_whitelisted(chat_id):
        denied_text = (
            "¡Oh no, brother! No tienes acceso para levantar en este bot.\n"
            "Ponte en contacto con el admin del bot para que te dé la autorización.\n"
            "¡Let's get those gains, baby!"
        )
        bot.send_message(chat_id, denied_text)
        log_denied_access(chat_id, message.text if hasattr(message, "text") else "Sin texto")
        log_to_console(f"Acceso denegado para {chat_id}", "ACCESS_DENIED")
        return False
    return True

def register_middleware(bot):
    """
    Registra middleware global para el bot.
    
    Args:
        bot: Instancia del bot de Telegram
    """
    @bot.middleware_handler(update_types=["message"])
    def log_all_messages(bot_instance, message: Message):
        """Middleware para registrar todos los mensajes entrantes"""
        user_id = get_google_id(message)
        telegram_id = get_telegram_id(message)
        if hasattr(message, "text") and message.text:
            log_to_console(f"MENSAJE RECIBIDO - Usuario {telegram_id} (Google ID: {user_id}): {message.text}", "INPUT")