# telegram/gym/handlers/exercise_handlers.py
import random
import re

import requests
from config import BASE_URL, ERROR_PHRASES, MOTIVATIONAL_PHRASES
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import format_logs, is_user_whitelisted, send_message_split

from .base_handlers import (check_whitelist, get_api_user_id, get_google_id,
                            get_telegram_id, log_to_console)


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
        api_user_id = get_api_user_id(message)
        
        if not check_whitelist(message, bot):
            return
        days = 7
        url = f"{BASE_URL}/logs"
        params = {"days": days, "user_id": api_user_id}

        log_to_console(f"Comando /logs - Usuario {chat_id} solicitando registros de {days} días", "PROCESS")

        try:
            response = requests.get(url, params=params)
            log_to_console(f"API /logs - Respuesta: {response.status_code}", "API")

            if response.status_code == 200:
                data = response.json()
                formatted = format_logs(data)
                log_to_console(f"Procesados {len(data)} registros de ejercicios", "PROCESS")
            else:
                formatted = f"Error al obtener los datos: {response.status_code}"
                log_to_console(f"Error en API /logs: {response.status_code} - {response.text}", "ERROR")
        except Exception as e:
            formatted = f"Error al conectar con el servidor: {e}"
            log_to_console(f"Excepción en /logs: {str(e)}", "ERROR")

        send_message_split(bot, chat_id, formatted)
        log_to_console(f"Respuesta enviada a {chat_id} para comando /logs", "OUTPUT")

    # Handler para comandos /logsX, donde X es el número de días.
    @bot.message_handler(regexp=r"^/logs(\d+)$")
    def send_logs_days(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        api_user_id = get_api_user_id(message)
        
        if not check_whitelist(message, bot):
            return
        match = re.match(r"^/logs(\d+)$", message.text)
        if match:
            days = int(match.group(1))
            url = f"{BASE_URL}/logs"
            params = {"days": days, "user_id": api_user_id}

            log_to_console(f"Comando /logs{days} - Usuario {chat_id} solicitando registros de {days} días", "PROCESS")

            try:
                response = requests.get(url, params=params)
                log_to_console(f"API /logs - Respuesta: {response.status_code}", "API")

                if response.status_code == 200:
                    data = response.json()
                    formatted = format_logs(data)
                    log_to_console(f"Procesados {len(data)} registros de ejercicios", "PROCESS")
                else:
                    formatted = f"Error al obtener los datos: {response.status_code}"
                    log_to_console(f"Error en API /logs: {response.status_code} - {response.text}", "ERROR")
            except Exception as e:
                formatted = f"Error al conectar con el servidor: {e}"
                log_to_console(f"Excepción en /logs{days}: {str(e)}", "ERROR")

            send_message_split(bot, chat_id, formatted)
            log_to_console(f"Respuesta enviada a {chat_id} para comando /logs{days}", "OUTPUT")

    # Handler para mensajes de texto que parezcan ejercicios
    @bot.message_handler(func=lambda message: is_exercise_message(message.text) if hasattr(message, "text") else False)
    def process_exercise_message(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        api_user_id = get_api_user_id(message)
        
        if not check_whitelist(message, bot):
            return

        text = message.text.lower()
        
        bot.send_chat_action(chat_id, "typing")
        data = {"exercise_data": message.text, "user_id": api_user_id}
        log_to_console(f"Ejercicio recibido - Usuario {chat_id}: {message.text}", "PROCESS")
        try:
            response = requests.post(f"{BASE_URL}", data=data)
            log_to_console(f"API envío ejercicio - Respuesta: {response.status_code}", "API")

            ronnie_quote = random.choice(MOTIVATIONAL_PHRASES)
            error_quote = random.choice(ERROR_PHRASES)

            if response.status_code == 200:
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
                bot.send_message(
                    chat_id,
                    f"🏋️‍♂️ *{error_quote}* 🏋️‍♂️\n\nCódigo: {response.status_code}",
                    parse_mode="Markdown",
                )
                log_to_console(f"Error al registrar ejercicio: {response.status_code} - {response.text}", "ERROR")
        except Exception as e:
            bot.send_message(
                chat_id,
                f"🏋️‍♂️ *{random.choice(ERROR_PHRASES)}* 🏋️‍♂️",
                parse_mode="Markdown",
            )
            log_to_console(f"Error al enviar el ejercicio: {str(e)}", "ERROR")

    # Manejar los botones inline
    @bot.callback_query_handler(func=lambda call: call.data in ["cmd_logs", "cmd_toca", "cmd_ai"])
    def handle_callback_query(call) -> None:
        # Obtener ID de Telegram para enviar mensajes
        chat_id = str(call.message.chat.id)
        # Obtener ID para APIs (Google ID si está disponible)
        telegram_id = chat_id
        api_user_id = get_google_id(telegram_id)

        # Verificamos directamente con el ID de Telegram
        if not is_user_whitelisted(chat_id):
            bot.answer_callback_query(call.id, "No tienes acceso a esta función")
            return

        if call.data == "cmd_toca":
            bot.answer_callback_query(call.id, "Obteniendo tu rutina de hoy...")
            url = f"{BASE_URL}/rutina_hoy?format=json"
            params = {"user_id": api_user_id}
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("rutina"):
                        formatted = f"🏋️‍♂️ *¡YEAH BUDDY! HOY ES {data['dia_nombre'].upper()}* 🏋️‍♂️\n\n"
                        formatted += "¡AIN'T NOTHING BUT A PEANUT! ESTO ES LO QUE TIENES QUE LEVANTAR HOY:\n\n"
                        for i, ejercicio in enumerate(data["rutina"], 1):
                            status = "✅" if ejercicio.get("realizado") else "⏱️"
                            formatted += f"{status} *{ejercicio['ejercicio'].upper()}*\n"
                        formatted += "\n💪 *¡LIGHTWEIGHT BABY!* 💪\n"
                        formatted += "\nRELLENA TUS SERIES Y RESPONDE CON ESTE MENSAJE:\n"
                        for ejercicio in data["rutina"]:
                            if not ejercicio.get("realizado"):
                                formatted += f"{ejercicio['ejercicio']}: \n"
                        formatted += "\nEjemplo: Dominadas: 10,8,6\n"
                        formatted += "\n*¡EVERYBODY WANNA BE A BODYBUILDER, BUT DON'T NOBODY WANNA LIFT NO HEAVY WEIGHT!*"
                    else:
                        formatted = (
                            "🏋️‍♂️ *¡LIGHTWEIGHT BABY!* 🏋️‍♂️\n\n"
                            "No hay rutina definida para hoy.\n"
                            "\nConfigura tu rutina con el comando /rutina\n"
                            "\n*¡NO PAIN, NO GAIN!*"
                        )
                    bot.send_message(chat_id, formatted, parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, f"Error al obtener la rutina: {response.status_code}")
            except Exception as e:
                bot.send_message(chat_id, f"Error al conectar con el servidor: {e}")
        elif call.data == "cmd_logs":
            bot.answer_callback_query(call.id, "Obteniendo tus logs...")
            days = 7
            url = f"{BASE_URL}/logs"
            params = {"days": days, "user_id": api_user_id}
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    formatted = format_logs(data)
                else:
                    formatted = f"Error al obtener los datos: {response.status_code}"
                send_message_split(bot, chat_id, formatted)
            except Exception as e:
                bot.send_message(chat_id, f"Error al conectar con el servidor: {e}")
        elif call.data == "cmd_ai":
            bot.answer_callback_query(call.id, "Activando el asistente AI...")
            bot.send_message(
                chat_id,
                "🤖 *¡ENTRENADOR AI EN LÍNEA!* 🤖\n\n"
                "Usa el comando /ai seguido de tu pregunta:\n\n"
                "Ejemplo: /ai Recomiéndame ejercicios para bíceps\n\n"
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
        
    text = text.lower()
    exercise_patterns = [
        r"\d+x\d+",  # Ej: 5x75
        r"press banca|dominadas|sentadillas|curl|press militar",
        r"\b\d+,\s*\d+\b",  # Ej: 10, 8, 6
    ]
    
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in exercise_patterns)