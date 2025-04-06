# telegram/gym/handlers/exercise_handlers.py
import random
import re

# Import requests if needed elsewhere, otherwise it can be removed if ApiClient handles all calls
# import requests
from config import BASE_URL, ERROR_PHRASES, MOTIVATIONAL_PHRASES
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import format_logs, is_user_whitelisted, send_message_split
# Import your ApiClient
from api_client import ApiClient
# Import get_google_id if needed for callback query handler logic
from .base_handlers import (check_whitelist, get_api_user_id,
                            get_telegram_id, log_to_console, get_google_id)


def register_exercise_handlers(bot):
    """
    Registra los handlers relacionados con ejercicios y logs.

    Args:
        bot: Instancia del bot de Telegram
    """
    # Comando /logs (sin dígitos): Consulta los ejercicios de los últimos 7 días.
    @bot.message_handler(commands=["logs"])
    def send_logs_default(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        api_user_id = get_api_user_id(message) # This likely returns Google ID if linked
        telegram_id_str = str(chat_id) # Use Telegram ID for the API call via ApiClient

        if not check_whitelist(message, bot):
            return

        days = 7
        log_to_console(f"Comando /logs - Usuario {chat_id} solicitando registros de {days} días (API User ID: {api_user_id})", "PROCESS")

        try:
            # Use ApiClient to handle the request including headers
            # Pass the telegram_id_str, which ApiClient expects
            response_data = ApiClient.get_logs(telegram_id=telegram_id_str, days=days)

            # Check the structure ApiClient returns on success/error
            if response_data and response_data.get("success") is not False: # Assuming ApiClient returns dict like {'success': True/False, ...}
                formatted = format_logs(response_data.get('logs', [])) # Assuming logs are under a 'logs' key
                log_to_console(f"Procesados {len(response_data.get('logs', []))} registros de ejercicios", "PROCESS")
            else:
                # Handle error reported by ApiClient or default message
                error_message = response_data.get("message", "Error desconocido al obtener logs") if response_data else "Error desconocido"
                formatted = f"Error al obtener los datos: {error_message}"
                log_to_console(f"Error en API /logs (vía ApiClient): {error_message}", "ERROR")

        except Exception as e:
            formatted = f"Error de conexión o procesamiento: {e}" # More generic error
            log_to_console(f"Excepción en /logs: {str(e)}", "ERROR")

        send_message_split(bot, chat_id, formatted)
        log_to_console(f"Respuesta enviada a {chat_id} para comando /logs", "OUTPUT")

    # Handler para comandos /logsX, donde X es el número de días.
    @bot.message_handler(regexp=r"^/logs(\d+)$")
    def send_logs_days(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        api_user_id = get_api_user_id(message) # This likely returns Google ID if linked
        telegram_id_str = str(chat_id) # Use Telegram ID for the API call via ApiClient


        if not check_whitelist(message, bot):
            return

        match = re.match(r"^/logs(\d+)$", message.text)
        if match:
            days = int(match.group(1))
            log_to_console(f"Comando /logs{days} - Usuario {chat_id} solicitando registros de {days} días (API User ID: {api_user_id})", "PROCESS")

            try:
                # Use ApiClient to handle the request including headers
                # Pass the telegram_id_str, which ApiClient expects
                response_data = ApiClient.get_logs(telegram_id=telegram_id_str, days=days)

                # Check the structure ApiClient returns on success/error
                if response_data and response_data.get("success") is not False: # Assuming ApiClient returns dict
                    formatted = format_logs(response_data.get('logs', [])) # Assuming logs are under 'logs' key
                    log_to_console(f"Procesados {len(response_data.get('logs', []))} registros de ejercicios", "PROCESS")
                else:
                     # Handle error reported by ApiClient or default message
                    error_message = response_data.get("message", "Error desconocido al obtener logs") if response_data else "Error desconocido"
                    formatted = f"Error al obtener los datos: {error_message}"
                    log_to_console(f"Error en API /logs{days} (vía ApiClient): {error_message}", "ERROR")

            except Exception as e:
                formatted = f"Error de conexión o procesamiento: {e}"
                log_to_console(f"Excepción en /logs{days}: {str(e)}", "ERROR")

            send_message_split(bot, chat_id, formatted)
            log_to_console(f"Respuesta enviada a {chat_id} para comando /logs{days}", "OUTPUT")

    # Handler para mensajes de texto que parezcan ejercicios
    # NOTE: This handler seems to use a different API endpoint (/api/log-exercise)
    # and different parameters. Check if ApiClient.log_exercise needs adjustment
    # based on whether your backend expects 'user_id' or 'telegram_id' for this specific route.
    # Assuming ApiClient.log_exercise handles its endpoint correctly for now.
    @bot.message_handler(func=lambda message: is_exercise_message(message.text) if hasattr(message, "text") else False)
    def process_exercise_message(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        # Decide which ID ApiClient.log_exercise needs. Let's assume it needs telegram_id based on its definition
        telegram_id_str = str(chat_id)

        if not check_whitelist(message, bot):
            return

        text = message.text.lower()

        bot.send_chat_action(chat_id, "typing")
        log_to_console(f"Ejercicio recibido - Usuario {chat_id}: {message.text}", "PROCESS")
        try:
            # Use ApiClient to log the exercise
            response_data = ApiClient.log_exercise(telegram_id=telegram_id_str, exercise_data=message.text)

            ronnie_quote = random.choice(MOTIVATIONAL_PHRASES)
            error_quote = random.choice(ERROR_PHRASES)

            # Check response structure from ApiClient.log_exercise
            if response_data and response_data.get("success"):
                bot.send_message(
                    chat_id,
                    f"🏋️‍♂️ *{ronnie_quote}* 🏋️‍♂️",
                    parse_mode="Markdown",
                )
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton("Ver mi rutina de hoy", callback_data="cmd_toca"),
                    InlineKeyboardButton("Ver mis logs", callback_data="cmd_logs"),
                )
                keyboard.add(InlineKeyboardButton("Consultar al AI", callback_data="cmd_ai"))
                bot.send_message(chat_id, "¿Qué quieres hacer ahora?", reply_markup=keyboard)
                log_to_console(f"Ejercicio registrado correctamente para usuario {chat_id}", "SUCCESS")
            else:
                error_message = response_data.get("message", "Error desconocido al registrar ejercicio") if response_data else "Error desconocido"
                bot.send_message(
                    chat_id,
                    f"🏋️‍♂️ *{error_quote}* 🏋️‍♂️\n\nError: {error_message}",
                    parse_mode="Markdown",
                )
                log_to_console(f"Error al registrar ejercicio (vía ApiClient): {error_message}", "ERROR")
        except Exception as e:
            bot.send_message(
                chat_id,
                f"🏋️‍♂️ *{random.choice(ERROR_PHRASES)}* 🏋️‍♂️\n\nError de conexión.",
                parse_mode="Markdown",
            )
            log_to_console(f"Error al enviar el ejercicio: {str(e)}", "ERROR")

    # Manejar los botones inline
    # NOTE: This callback handler also makes direct requests.
    # Consider refactoring to use ApiClient methods (get_today_routine, get_logs)
    # for consistency and to ensure headers are sent if needed by those backend routes.
    @bot.callback_query_handler(func=lambda call: call.data in ["cmd_logs", "cmd_toca", "cmd_ai"])
    def handle_callback_query(call) -> None:
        # Obtain Telegram ID for sending messages
        chat_id = get_telegram_id(call.message) # Use the message associated with the callback
        telegram_id_str = str(chat_id)

        # Check whitelist using the chat_id from the message
        # Need to pass the original message object to check_whitelist if it uses message properties
        if not check_whitelist(call.message, bot):
             bot.answer_callback_query(call.id, "Acceso denegado.")
             return

        if call.data == "cmd_toca":
            bot.answer_callback_query(call.id, "Obteniendo tu rutina de hoy...")
            try:
                # Use ApiClient.get_today_routine
                routine_data = ApiClient.get_today_routine(telegram_id=telegram_id_str)
                if routine_data and routine_data.get("success") and routine_data.get("rutina"):
                    # Format routine_data (assuming structure from previous code)
                    dia_nombre = routine_data.get('dia_nombre', 'Día Desconocido')
                    rutina_list = routine_data.get('rutina', [])
                    formatted = f"🏋️‍♂️ *¡YEAH BUDDY! HOY ES {dia_nombre.upper()}* 🏋️‍♂️\n\n"
                    formatted += "¡AIN'T NOTHING BUT A PEANUT! ESTO ES LO QUE TIENES QUE LEVANTAR HOY:\n\n"
                    for i, ejercicio in enumerate(rutina_list, 1):
                        status = "✅" if ejercicio.get("realizado") else "⏱️"
                        formatted += f"{status} *{ejercicio.get('ejercicio', 'N/A').upper()}*\n"
                    formatted += "\n💪 *¡LIGHTWEIGHT BABY!* 💪\n"
                    formatted += "\nRELLENA TUS SERIES Y RESPONDE CON ESTE MENSAJE:\n"
                    for ejercicio in rutina_list:
                        if not ejercicio.get("realizado"):
                             formatted += f"{ejercicio.get('ejercicio', 'N/A')}: \n"
                    formatted += "\nEjemplo: Dominadas: 10,8,6\n"
                    formatted += "\n*¡EVERYBODY WANNA BE A BODYBUILDER, BUT DON'T NOBODY WANNA LIFT NO HEAVY WEIGHT!*"
                elif routine_data and not routine_data.get("rutina"):
                     formatted = (
                            "🏋️‍♂️ *¡LIGHTWEIGHT BABY!* 🏋️‍♂️\n\n"
                            "No hay rutina definida para hoy.\n"
                            "\nConfigura tu rutina con el comando /rutina\n"
                            "\n*¡NO PAIN, NO GAIN!*"
                        )
                else:
                     error_message = routine_data.get("message", "Error desconocido") if routine_data else "Error desconocido"
                     formatted = f"Error al obtener la rutina: {error_message}"
                bot.send_message(chat_id, formatted, parse_mode="Markdown")
            except Exception as e:
                log_to_console(f"Excepción en callback cmd_toca: {str(e)}", "ERROR")
                bot.send_message(chat_id, f"Error de conexión al obtener rutina: {e}")

        elif call.data == "cmd_logs":
            bot.answer_callback_query(call.id, "Obteniendo tus logs...")
            days = 7
            try:
                # Use ApiClient.get_logs
                response_data = ApiClient.get_logs(telegram_id=telegram_id_str, days=days)
                if response_data and response_data.get("success") is not False:
                    formatted = format_logs(response_data.get('logs', []))
                else:
                    error_message = response_data.get("message", "Error desconocido") if response_data else "Error desconocido"
                    formatted = f"Error al obtener los datos: {error_message}"
                send_message_split(bot, chat_id, formatted)
            except Exception as e:
                log_to_console(f"Excepción en callback cmd_logs: {str(e)}", "ERROR")
                bot.send_message(chat_id, f"Error de conexión al obtener logs: {e}")

        elif call.data == "cmd_ai":
            bot.answer_callback_query(call.id, "Activando el asistente AI...")
            bot.send_message(
                chat_id,
                "🤖 *¡ENTRENADOR AI EN LÍNEA!* 🤖\n\n"
                "Usa el comando /ai seguido de tu pregunta:\n\n"
                "Ejemplo: /ai Recomiéndame ejercicios para bíceps\n\n"
                "O simplemente escribe tu pregunta directamente.\n\n" # Added clarification
                "*¡LIGHTWEIGHT BABY!*",
                parse_mode="Markdown",
            )

def is_exercise_message(text: str) -> bool:
    """
    Determina si un mensaje parece ser un registro de ejercicio.

    Args:
        text: El texto del mensaje

    Returns:
        bool: True si parece un ejercicio, False en caso contrario
    """
    if not text:
        return False

    # Avoid matching commands
    if text.startswith('/'):
        return False

    text = text.lower()
    # Updated patterns to be more specific and avoid broad matches
    # Pattern 1: Exercise name followed by digits/sets/reps (more flexible)
    # Allows for variations like "press banca 10 10 8", "dominadas 5x5", "curl biceps 12,10,8 x 20kg"
    pattern1 = r"^[a-záéíóúüñ\s]+(\d{1,3}(\s*x\s*\d{1,3})?(\s*kg)?(\s*lbs)?|[,\s]*\d{1,3})+"

    # Pattern 2: Simple rep counts like "10, 8, 6" (less likely for exercises but kept for compatibility)
    pattern2 = r"^\s*\d{1,3}(,\s*\d{1,3})+\s*$"

    # Pattern 3: Specific keywords often present in exercise logs
    keywords = ["press banca", "dominadas", "sentadillas", "curl", "press militar", "peso muerto", "remo", "fondos"]


    # Check if pattern1 matches OR if pattern2 matches OR if any keyword is present
    if re.search(pattern1, text, re.IGNORECASE):
        return True
    # if re.match(pattern2, text): # Use match for pattern2 as it should match the whole string
    #     return True
    if any(keyword in text for keyword in keywords):
         # Add extra check: ensure there are also numbers present to avoid matching general chat about exercises
         if re.search(r'\d', text):
             return True

    return False