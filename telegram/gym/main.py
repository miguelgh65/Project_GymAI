# main.py
import telebot
from telebot import apihelper
import os
import time
import sys
import traceback
from dotenv import load_dotenv
from handlers import register_all_handlers
from utils import log_to_console

# Habilitar middleware antes de crear el bot
apihelper.ENABLE_MIDDLEWARE = True

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener el token del bot desde las variables de entorno
TOKEN = os.getenv("BOT_TOKEN")

# Parámetros de configuración para reintentos
MAX_RETRIES = 10
INITIAL_RETRY_DELAY = 5  # segundos
MAX_RETRY_DELAY = 300    # 5 minutos máximo entre reintentos

def start_bot():
    """Inicializa el bot y lo mantiene en ejecución con sistema de reintentos"""
    # Inicializa el bot
    bot = telebot.TeleBot(TOKEN)
    
    # Registrar todos los handlers
    register_all_handlers(bot)
    
    log_to_console("Bot iniciado y listo para recibir mensajes...")
    
    # Variable para mantener el estado de ejecución
    retry_count = 0
    retry_delay = INITIAL_RETRY_DELAY
    
    # Bucle principal para mantener el bot en ejecución permanentemente
    while True:
        try:
            # Configurar los parámetros de polling para que sea más resistente
            log_to_console("Iniciando bot.polling()...")
            bot.polling(none_stop=True, interval=0.5, timeout=30)
            
            # Si llegamos aquí es que polling ha terminado normalmente, lo reiniciamos
            log_to_console("bot.polling() ha terminado, reiniciando...")
            
        except telebot.apihelper.ApiException as e:
            # Error específico de la API de Telegram
            log_to_console(f"Error de API de Telegram: {e}", "ERROR")
            
        except Exception as e:
            # Cualquier otra excepción inesperada
            error_msg = f"Error inesperado: {e}\n"
            error_msg += traceback.format_exc()
            log_to_console(error_msg, "ERROR")
        
        # Gestión de reintentos con backoff exponencial
        retry_count += 1
        log_to_console(f"Reintento {retry_count}/{MAX_RETRIES} en {retry_delay} segundos...", "WARNING")
        
        # Esperar antes de reintentar
        time.sleep(retry_delay)
        
        # Aumentar el tiempo de espera para el siguiente reintento (backoff exponencial)
        retry_delay = min(retry_delay * 1.5, MAX_RETRY_DELAY)
        
        # Reiniciar el contador después de un tiempo para evitar que el delay sea siempre máximo
        if retry_count >= MAX_RETRIES:
            log_to_console("Reiniciando contador de reintentos", "INFO")
            retry_count = 0
            retry_delay = INITIAL_RETRY_DELAY

if __name__ == "__main__":
    start_bot()