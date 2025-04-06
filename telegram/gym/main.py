import os
import sys
import time
import traceback
import logging

import telebot
from dotenv import load_dotenv
from handlers import register_all_handlers
from telebot import apihelper
from utils import log_to_console
from telegram.gym.handlers import register_all_handlers  # Ajusta la ruta de importación



# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Imprimir en consola
        logging.FileHandler('telegram_bot.log')  # Guardar en archivo de log
    ]
)

# Habilitar middleware antes de crear el bot
apihelper.ENABLE_MIDDLEWARE = True

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener el token del bot desde las variables de entorno
TOKEN = os.getenv("BOT_TOKEN")

# Verificación del token
if not TOKEN:
    print("❌ ERROR: No se encontró el token del bot. Verifica tu archivo .env")
    logging.critical("No se encontró BOT_TOKEN en las variables de entorno")
    sys.exit(1)

# Parámetros de configuración para reintentos
MAX_RETRIES = 10
INITIAL_RETRY_DELAY = 5  # segundos
MAX_RETRY_DELAY = 300    # 5 minutos máximo entre reintentos

def start_bot():
    """Inicializa el bot y lo mantiene en ejecución con sistema de reintentos"""
    try:
        print(f"🤖 Iniciando bot de Telegram con token: {TOKEN[:10]}...")
        logging.info(f"Iniciando bot con token que comienza con {TOKEN[:10]}")

        # Inicializa el bot
        bot = telebot.TeleBot(TOKEN, parse_mode=None)
        
        # Añadir middleware de depuración
        @bot.middleware_handler(update_types=['message'])
        def debug_middleware(bot_instance, message):
            print(f"🔍 Mensaje recibido: {message.text}")
            print(f"👤 Usuario: {message.from_user.id}")
            logging.debug(f"Mensaje recibido: {message.text} de usuario {message.from_user.id}")
        
        # Registrar todos los handlers
        register_all_handlers(bot)
        
        log_to_console("✅ Bot iniciado y handlers registrados...")
        print("✅ Todos los handlers registrados correctamente.")
        
        # Variable para mantener el estado de ejecución
        retry_count = 0
        retry_delay = INITIAL_RETRY_DELAY
        
        # Bucle principal para mantener el bot en ejecución permanentemente
        while True:
            try:
                # Configurar los parámetros de polling para que sea más resistente
                print("🚀 Iniciando bot polling...")
                logging.info("Iniciando bot polling")
                
                bot.polling(
                    none_stop=True, 
                    interval=0.5, 
                    timeout=30,
                    long_polling_timeout=30
                )
                
                # Si llegamos aquí es que polling ha terminado normalmente, lo reiniciamos
                log_to_console("bot.polling() ha terminado, reiniciando...")
                
            except telebot.apihelper.ApiException as e:
                # Error específico de la API de Telegram
                error_msg = f"Error de API de Telegram: {e}"
                print(f"❌ {error_msg}")
                log_to_console(error_msg, "ERROR")
                logging.error(error_msg, exc_info=True)
                
            except Exception as e:
                # Cualquier otra excepción inesperada
                error_msg = f"Error inesperado: {e}\n"
                error_msg += traceback.format_exc()
                print(f"❌ {error_msg}")
                log_to_console(error_msg, "ERROR")
                logging.exception("Error inesperado en bot polling")
            
            # Gestión de reintentos con backoff exponencial
            retry_count += 1
            retry_msg = f"Reintento {retry_count}/{MAX_RETRIES} en {retry_delay} segundos..."
            print(f"⏳ {retry_msg}")
            log_to_console(retry_msg, "WARNING")
            logging.warning(retry_msg)
            
            # Esperar antes de reintentar
            time.sleep(retry_delay)
            
            # Aumentar el tiempo de espera para el siguiente reintento (backoff exponencial)
            retry_delay = min(retry_delay * 1.5, MAX_RETRY_DELAY)
            
            # Reiniciar el contador después de un tiempo para evitar que el delay sea siempre máximo
            if retry_count >= MAX_RETRIES:
                reset_msg = "Reiniciando contador de reintentos"
                print(f"🔄 {reset_msg}")
                log_to_console(reset_msg, "INFO")
                logging.info(reset_msg)
                retry_count = 0
                retry_delay = INITIAL_RETRY_DELAY

    except Exception as fatal_error:
        print(f"💥 Error fatal al iniciar el bot: {fatal_error}")
        logging.critical("Error fatal al iniciar el bot", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    start_bot()