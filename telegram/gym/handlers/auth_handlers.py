# telegram/gym/handlers/auth_handlers.py
import re
import logging
from telebot.types import Message
from config import BASE_URL, WHITELIST_PATH
from .base_handlers import (
    check_whitelist,
    log_to_console,
    get_telegram_id,
    get_google_id
)

# Importar ApiClient para la verificación de códigos
from api_client import ApiClient

def register_auth_handlers(bot):
    """
    Registra los handlers relacionados con autenticación y vinculación de cuentas.

    Args:
        bot: Instancia del bot de Telegram
    """
    @bot.message_handler(commands=["debug"])
    def debug_info(message: Message) -> None:
        chat_id = message.chat.id
        username = message.from_user.username if message.from_user else "N/A"

        # Leer contenido de whitelist
        try:
            with open(WHITELIST_PATH, 'r') as f:
                whitelist_content = f.read().strip()
        except FileNotFoundError:
            whitelist_content = "Whitelist file not found."
        except Exception as e:
            whitelist_content = f"Error reading whitelist: {e}"

        # Intentar obtener google_id para esta sesión
        google_id = get_google_id(chat_id)
        google_id_text = google_id if google_id != str(chat_id) else "No vinculado"

        debug_text = (
            f"🤖 Debug Information:\n"
            f"Chat ID: `{chat_id}`\n"
            f"Username: @{username}\n"
            f"First Name: {message.from_user.first_name if message.from_user else 'N/A'}\n"
            f"Last Name: {message.from_user.last_name if message.from_user else 'N/A'}\n"
            f"Google ID: {google_id_text}\n"
            f"Whitelist contents: {whitelist_content}"
        )
        bot.send_message(chat_id, debug_text, parse_mode="Markdown")

    # --- Comando /start: Mensaje de bienvenida al estilo Ronnie Coleman.
    @bot.message_handler(commands=["start"])
    def send_welcome(message: Message) -> None:
        print("🔔 COMANDO /start RECIBIDO")
        chat_id = get_telegram_id(message)
        print(f"Chat ID: {chat_id}")
        log_to_console(f"Comando /start recibido de usuario {chat_id}", "INPUT")

        if not check_whitelist(message, bot):
            print(f"❌ Usuario {chat_id} no está en whitelist")
            return

        welcome_text = (
            "¡Yeah buddy! Bienvenido a tu Bot de Gym, donde cada sesión es 'light weight, baby'!\n"
            "Usa /help para ver los comandos disponibles y saber cómo enviar tus ejercicios."
        )
        bot.send_message(chat_id, welcome_text)
        log_to_console(f"Comando /start - Bienvenida enviada a {chat_id}", "OUTPUT")

    # --- Comando /help: Muestra los comandos disponibles y cómo enviar ejercicios.
    @bot.message_handler(commands=["help"])
    def send_help(message: Message) -> None:
        chat_id = get_telegram_id(message)

        if not check_whitelist(message, bot):
            return

        help_text = (
            "¡Yeah buddy! Aquí van los comandos:\n"
            "/toca - Ver qué ejercicios tocan hoy según tu rutina\n"
            "/rutina - Configurar tu rutina semanal\n"
            "/logs - Consulta los ejercicios de los últimos 7 días (por defecto).\n"
            "/logsX - Consulta los ejercicios de los últimos X días. Ejemplo: /logs1, /logs2, /logs3, ...\n"
            "/ai - Consulta a tu entrenador personal AI. Ejemplo: /ai ¿Cómo mejorar mi press de banca?\n"
            "/vincular - Vincular tu cuenta de Telegram con tu cuenta web\n"
            "/debug - Muestra información de debug (ID, estado de vinculación)\n"
            "\n"
            "También puedes hacer preguntas directamente al Entrenador AI simplemente escribiendo tu pregunta normal.\n"
            "\n"
            "Para enviar tus ejercicios, utiliza este formato:\n"
            "Ejemplo: press banca 10x130,7x130,5x130 dominadas 10,9,5\n"
            "¡Suelta esas series y registra tu grandeza!"
        )
        bot.send_message(chat_id, help_text)
        log_to_console(f"Comando /help - Mostrando ayuda a {chat_id}", "OUTPUT")

    # --- Función para procesar el código de vinculación ---
    def process_link_code(message: Message) -> None:
        chat_id = get_telegram_id(message)
        if not check_whitelist(message, bot):
            return

        code = message.text.strip().upper()
        telegram_id = str(chat_id)

        # Validar formato del código (6 caracteres alfanuméricos)
        if not re.match(r"^[A-Z0-9]{6}$", code):
            bot.send_message(
                chat_id,
                "❌ El código debe ser de 6 caracteres (letras y números).\n"
                "Por favor, intenta de nuevo con /vincular",
            )
            return

        # Enviar mensaje de "procesando"
        bot.send_chat_action(chat_id, "typing")

        # Llamar a la API para verificar el código
        response = ApiClient.verify_link_code(code, telegram_id)
        
        if response and response.get("success"):
            bot.send_message(
                chat_id,
                "✅ *¡Cuentas vinculadas con éxito!*\n\n"
                "Ahora puedes acceder a tus datos desde la web y desde Telegram.\n"
                "Tus entrenamientos se sincronizarán automáticamente entre ambas plataformas.",
                parse_mode="Markdown",
            )
            log_to_console(f"Cuentas vinculadas para Telegram ID {telegram_id}", "SUCCESS")
        else:
            error_message = response.get("message", "Código inválido o expirado") if response else "Error desconocido"
            bot.send_message(
                chat_id,
                f"❌ Error: {error_message}.\n"
                "Por favor, genera un nuevo código en la web e inténtalo de nuevo con /vincular",
            )
            log_to_console(f"Fallo vinculación para Telegram ID {telegram_id}: {error_message}", "WARNING")

    # Comando /vincular
    @bot.message_handler(commands=["vincular"])
    def link_account_command(message: Message) -> None:
        chat_id = get_telegram_id(message)
        if not check_whitelist(message, bot):
            return

        # Verificar si ya tiene una cuenta vinculada
        google_id = get_google_id(chat_id)
        if google_id and google_id != str(chat_id):
            bot.send_message(
                chat_id,
                "🔄 *¡Ya tienes una cuenta vinculada!*\n\n"
                f"Tu cuenta de Telegram está vinculada con Google ID: `{google_id}`\n\n"
                "Si deseas vincular con otra cuenta, primero debes desvincular la actual desde la web.",
                parse_mode="Markdown"
            )
            return

        log_to_console(f"Comando /vincular recibido de usuario {chat_id}", "INPUT")
        bot.send_message(
            chat_id,
            "🔗 *Vincular con cuenta web*\n\n"
            "Por favor, envía el código de vinculación que ves en la web.\n"
            "El código debe ser de 6 caracteres (letras y números).",
            parse_mode="Markdown",
        )
        # Registrar el siguiente paso para procesar el código
        bot.register_next_step_handler(message, process_link_code)