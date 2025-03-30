# telegram/gym/handlers/auth_handlers.py
import re
import requests
from telebot.types import Message
from .base_handlers import get_chat_id, check_whitelist, log_to_console
from config import BASE_URL

def register_auth_handlers(bot):
    """
    Registra los handlers relacionados con autenticación y vinculación de cuentas.
    
    Args:
        bot: Instancia del bot de Telegram
    """
    # --- Comando /start: Mensaje de bienvenida al estilo Ronnie Coleman.
    @bot.message_handler(commands=["start"])
    def send_welcome(message: Message) -> None:
        chat_id = get_chat_id(message)
        if not check_whitelist(message, bot):
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
        chat_id = get_chat_id(message)
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
        chat_id = str(message.chat.id)  # Usar el ID de Telegram directamente para la vinculación
        if not check_whitelist(message, bot):
            return

        code = message.text.strip().upper()
        telegram_id = chat_id

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
            response = requests.post(
                url,
                json={"code": code, "telegram_id": telegram_id},
                headers={"Content-Type": "application/json"},
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
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ Error: {data.get('message', 'Código inválido o expirado')}.\n"
                        "Por favor, genera un nuevo código en la web e inténtalo de nuevo con /vincular",
                    )
            else:
                bot.send_message(
                    chat_id,
                    "❌ Error al verificar el código. Por favor, intenta nuevamente.",
                )
        except Exception as e:
            bot.send_message(
                chat_id,
                "❌ Error al conectar con el servidor. Por favor, intenta más tarde.",
            )
            log_to_console(f"Error en verificación de código: {str(e)}", "ERROR")

    # Comando /vincular
    @bot.message_handler(commands=["vincular"])
    def link_account_command(message: Message) -> None:
        chat_id = str(message.chat.id)  # Usar el ID de Telegram directamente para la vinculación
        if not check_whitelist(message, bot):
            return

        bot.send_message(
            chat_id,
            "🔗 *Vincular con cuenta web*\n\n"
            "Por favor, envía el código de vinculación que ves en la web.\n"
            "El código debe ser de 6 caracteres (letras y números).",
            parse_mode="Markdown",
        )
        # Registrar el siguiente paso para procesar el código
        bot.register_next_step_handler(message, process_link_code)