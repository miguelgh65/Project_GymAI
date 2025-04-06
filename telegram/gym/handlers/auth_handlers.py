# telegram/gym/handlers/auth_handlers.py
import re

import requests
from config import BASE_URL, WHITELIST_PATH # Import WHITELIST_PATH if needed elsewhere, or remove if unused
from telebot.types import Message
from .base_handlers import (
    check_whitelist,
    log_to_console,
    get_telegram_id # Correct import already present
)



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

        # You might need to import WHITELIST_PATH in this function's scope or pass it if needed
        # For simplicity, assuming WHITELIST_PATH is accessible or defined globally in this file/module if used.
        # Example: from config import WHITELIST_PATH if not imported at the top
        try:
            with open(WHITELIST_PATH, 'r') as f:
                whitelist_content = f.read().strip()
        except FileNotFoundError:
            whitelist_content = "Whitelist file not found."
        except Exception as e:
            whitelist_content = f"Error reading whitelist: {e}"


        debug_text = (
            f"🤖 Debug Information:\n"
            f"Chat ID: `{chat_id}`\n"
            f"Username: @{username}\n"
            f"First Name: {message.from_user.first_name if message.from_user else 'N/A'}\n"
            f"Last Name: {message.from_user.last_name if message.from_user else 'N/A'}\n"
            f"Whitelist contents: {whitelist_content}" # Display content read from file
        )
        bot.send_message(chat_id, debug_text, parse_mode="Markdown")

    # --- Comando /start: Mensaje de bienvenida al estilo Ronnie Coleman.
    @bot.message_handler(commands=["start"])
    def send_welcome(message: Message) -> None:
        print("🔔 COMANDO /start RECIBIDO") # Añade este print directo
        # Uses the correctly imported get_telegram_id
        chat_id = get_telegram_id(message)
        print(f"Chat ID: {chat_id}") # Añade este print
        log_to_console(f"Comando /start recibido de usuario {chat_id}", "INPUT")

        if not check_whitelist(message, bot):
            print(f"❌ Usuario {chat_id} no está en whitelist") # Añade este print
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
        # Use get_telegram_id instead of get_chat_id - Correct function is used here
        chat_id = get_telegram_id(message)

        if not check_whitelist(message, bot):
            return

        help_text = (
            "¡Yeah buddy! Aquí van los comandos:\n"
            "/toca - Ver qué ejercicios tocan hoy según tu rutina\n"
            "/rutina - Configurar tu rutina semanal\n"
            "/logs  - Consulta los ejercicios de los últimos 7 días (por defecto).\n"
            "/logsX - Consulta los ejercicios de los últimos X días. Ejemplo: /logs1, /logs2, /logs3, ...\n"
            "/ai - Consulta a tu entrenador personal AI. Ejemplo: /ai ¿Cómo mejorar mi press de banca?\n"
            "/vincular - Vincular tu cuenta de Telegram con tu cuenta web\n"
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
        # Use get_telegram_id to get the chat_id for sending messages
        chat_id = get_telegram_id(message)
        if not check_whitelist(message, bot):
            return

        code = message.text.strip().upper()
        telegram_id = str(chat_id) # Use the chat_id as the telegram_id for the API call

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
        url = f"{BASE_URL}/api/verify-link-code"
        try:
            # Include the telegram_id in the payload
            payload = {"code": code, "telegram_id": telegram_id}
            # Get headers if needed, assuming ApiClient or similar defines them
            # headers = ApiClient.get_headers() # Example if using an ApiClient class
            headers = {"Content-Type": "application/json"} # Simple header

            response = requests.post(
                url,
                json=payload,
                headers=headers, # Pass headers if required by your API
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    bot.send_message(
                        chat_id,
                        "✅ *¡Cuentas vinculadas con éxito!*\n\n"
                        "Ahora puedes acceder a tus datos desde la web y desde Telegram.\n"
                        "Tus entrenamientos se sincronizarán automáticamente entre ambas plataformas.",
                        parse_mode="Markdown",
                    )
                    log_to_console(f"Cuentas vinculadas para Telegram ID {telegram_id}", "SUCCESS")
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ Error: {data.get('message', 'Código inválido o expirado')}.\n"
                        "Por favor, genera un nuevo código en la web e inténtalo de nuevo con /vincular",
                    )
                    log_to_console(f"Fallo vinculación para Telegram ID {telegram_id}: {data.get('message', 'Código inválido')}", "WARNING")
            else:
                 # Log the status code and response text for debugging
                log_to_console(f"Error en API /verify-link-code: {response.status_code} - {response.text}", "ERROR")
                bot.send_message(
                    chat_id,
                    f"❌ Error al verificar el código ({response.status_code}). Por favor, intenta nuevamente.",
                )
        except requests.exceptions.RequestException as e: # Catch specific request errors
            bot.send_message(
                chat_id,
                "❌ Error de conexión al verificar el código. Por favor, intenta más tarde.",
            )
            log_to_console(f"Error de conexión en verificación de código: {str(e)}", "ERROR")
        except Exception as e: # Catch any other unexpected errors
            bot.send_message(
                chat_id,
                "❌ Ocurrió un error inesperado. Por favor, intenta más tarde.",
            )
            log_to_console(f"Error inesperado en process_link_code: {str(e)}", "ERROR")


    # Comando /vincular
    @bot.message_handler(commands=["vincular"])
    def link_account_command(message: Message) -> None:
        # Use get_telegram_id to get chat_id
        chat_id = get_telegram_id(message)
        if not check_whitelist(message, bot):
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