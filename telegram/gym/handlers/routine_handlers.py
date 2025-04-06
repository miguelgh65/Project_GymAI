# telegram/gym/handlers/routine_handlers.py
import json
import re
import logging # Import logging if you want to use it directly

# Assuming requests is potentially used elsewhere or needed by ApiClient implicitly
# import requests
from config import BASE_URL
from telebot.types import Message

# Import your ApiClient
from api_client import ApiClient

from .base_handlers import (check_whitelist, get_api_user_id, get_telegram_id,
                            log_to_console, get_telegram_headers) # get_telegram_headers might be unused now


def register_routine_handlers(bot):
    """
    Registra los handlers relacionados con rutinas.

    Args:
        bot: Instancia del bot de Telegram
    """
    # Comando /toca: Muestra los ejercicios programados para hoy
    @bot.message_handler(commands=["toca"])
    def send_todays_workout(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # Use Telegram ID for the API call via ApiClient
        telegram_id_str = str(chat_id)

        if not check_whitelist(message, bot):
            return

        log_to_console(f"Comando /toca - Usuario {chat_id} solicitando rutina de hoy", "PROCESS")

        try:
            # Use ApiClient.get_today_routine
            routine_data = ApiClient.get_today_routine(telegram_id=telegram_id_str)

            # <<< --- !!! ADD THIS LOGGING LINE !!! --- >>>
            log_to_console(f"API Response Data (/rutina_hoy): {routine_data}", "DEBUG")
            # <<< --- !!! ADD THIS LOGGING LINE !!! --- >>>


            # Check the structure ApiClient returns on success/error
            # Ensure the key 'rutina' exists and is not None and has content
            if routine_data and routine_data.get("success") and routine_data.get("rutina") is not None and len(routine_data.get("rutina")) > 0:
                # Format routine_data
                dia_nombre = routine_data.get('dia_nombre', 'Día Desconocido')
                rutina_list = routine_data.get('rutina', [])
                formatted = f"🏋️‍♂️ *¡YEAH BUDDY! HOY ES {dia_nombre.upper()}* 🏋️‍♂️\n\n"
                formatted += "¡AIN'T NOTHING BUT A PEANUT! ESTO ES LO QUE TIENES QUE LEVANTAR HOY:\n\n"
                for i, ejercicio in enumerate(rutina_list, 1):
                    # Assuming 'ejercicio' is a dict like {'ejercicio': 'name', 'realizado': False}
                    status = "✅" if ejercicio.get("realizado") else "⏱️"
                    formatted += f"{status} *{ejercicio.get('ejercicio', 'N/A').upper()}*\n"
                formatted += "\n💪 *¡LIGHTWEIGHT BABY!* 💪\n"
                formatted += "\nRELLENA TUS SERIES Y RESPONDE CON ESTE MENSAJE:\n"
                for ejercicio in rutina_list:
                    if not ejercicio.get("realizado"):
                         formatted += f"{ejercicio.get('ejercicio', 'N/A')}: \n"
                formatted += "\nEjemplo: Dominadas: 10,8,6\n"
                formatted += "\n*¡EVERYBODY WANNA BE A BODYBUILDER, BUT DON'T NOBODY WANNA LIFT NO HEAVY WEIGHT!*"
            # Check specifically if success is True but the routine list is empty or None
            elif routine_data and routine_data.get("success") and (routine_data.get("rutina") is None or len(routine_data.get("rutina")) == 0):
                 formatted = (
                        "🏋️‍♂️ *¡LIGHTWEIGHT BABY!* 🏋️‍♂️\n\n"
                        "No hay rutina definida para hoy.\n"
                        "\nConfigura tu rutina con el comando /rutina\n"
                        "\n*¡NO PAIN, NO GAIN!*"
                    )
            else:
                 # Handles API errors or unexpected structure
                 error_message = routine_data.get("message", "Error desconocido al obtener rutina") if routine_data else "Error desconocido"
                 formatted = f"Error al obtener la rutina: {error_message}"
                 log_to_console(f"Error procesando rutina /toca: {error_message}", "ERROR")

        except Exception as e:
            formatted = f"Error de conexión o procesamiento en /toca: {e}"
            log_to_console(f"Excepción en /toca: {str(e)}", "ERROR")
            # Optionally log the full traceback for deeper debugging
            # logging.exception("Exception details in /toca:")

        bot.send_message(chat_id, formatted, parse_mode="Markdown")
        log_to_console(f"Respuesta enviada a {chat_id} para comando /toca", "OUTPUT")

    # Comando /rutina: Permite configurar la rutina semanal
    @bot.message_handler(commands=["rutina"])
    def config_routine(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # Use Telegram ID for the API call via ApiClient
        telegram_id_str = str(chat_id)

        if not check_whitelist(message, bot):
            return

        log_to_console(f"Comando /rutina - Usuario {chat_id} solicitando configuración de rutina", "PROCESS")

        try:
            # Use ApiClient.get_routine
            routine_config_data = ApiClient.get_routine(telegram_id=telegram_id_str)

             # <<< --- ADD LOGGING HERE TOO --- >>>
            log_to_console(f"API Response Data (/rutina): {routine_config_data}", "DEBUG")
             # <<< --- ADD LOGGING HERE TOO --- >>>

            # Check the structure returned by ApiClient.get_routine
            if routine_config_data and routine_config_data.get("success") and routine_config_data.get("rutina"):
                formatted = "🏋️‍♂️ *¡LIGHT WEIGHT BABY! TU RUTINA ACTUAL* 🏋️‍♂️\n\n"
                rutina_dict = routine_config_data.get("rutina", {}) # Expecting a dict like {"1": [...], "2": [...]}

                weekdays = [
                    {"id": 1, "name": "Lunes"}, {"id": 2, "name": "Martes"},
                    {"id": 3, "name": "Miércoles"}, {"id": 4, "name": "Jueves"},
                    {"id": 5, "name": "Viernes"}, {"id": 6, "name": "Sábado"},
                    {"id": 7, "name": "Domingo"},
                ]

                for day in weekdays:
                    day_id_str = str(day["id"])
                    formatted += f"*{day['name']}*: "
                    # Check if day exists and has exercises
                    if day_id_str in rutina_dict and rutina_dict[day_id_str]:
                        exercises = ", ".join(rutina_dict[day_id_str])
                        formatted += exercises
                    else:
                        formatted += "Descanso"
                    formatted += "\n"

                formatted += "\n💪 *PARA CONFIGURAR UN DÍA*: Envía un mensaje con el formato:\n"
                formatted += "```\nDía: ejercicio1, ejercicio2, ...\n```\n"
                formatted += "Ejemplo: Lunes: Press Banca, Dominadas, Triceps\n\n"
                formatted += "*EVERYBODY WANNA BE A BODYBUILDER, BUT DON'T NOBODY WANNA LIFT NO HEAVY WEIGHT!*"
            # Handle case where routine exists but might be empty, or success is False
            else:
                 # Check if success is explicitly False
                 if routine_config_data and routine_config_data.get("success") is False:
                     error_message = routine_config_data.get("message", "Error desconocido")
                     formatted = f"Error al obtener la rutina: {error_message}"
                     log_to_console(f"Error API /rutina: {error_message}", "ERROR")
                 else: # Assume no routine configured yet
                     formatted = (
                        "🏋️‍♂️ *¡NO PAIN NO GAIN! CONFIGURA TU RUTINA* 🏋️‍♂️\n\n"
                        "No tienes una rutina configurada aún. Para configurar, envía un mensaje con el formato:\n"
                        "```\nDía: ejercicio1, ejercicio2, ...\n```\n"
                        "Ejemplo: Lunes: Press Banca, Dominadas, Triceps\n\n"
                        "*¡LIGHTWEIGHT BABY!*"
                    )
        except Exception as e:
            formatted = f"Error de conexión o procesamiento en /rutina: {e}"
            log_to_console(f"Excepción en /rutina: {str(e)}", "ERROR")
            # logging.exception("Exception details in /rutina:")

        bot.send_message(chat_id, formatted, parse_mode="Markdown")
        log_to_console(f"Respuesta enviada a {chat_id} para comando /rutina", "OUTPUT")


    # Handler para configurar rutina por día
    @bot.message_handler(regexp=r"^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo):\s*(.+)$")
    def set_routine_day(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # Use Telegram ID for the API call via ApiClient
        telegram_id_str = str(chat_id)

        if not check_whitelist(message, bot):
            return

        match = re.match(r"^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo):\s*(.+)$", message.text, re.IGNORECASE | re.UNICODE) # Added UNICODE flag
        if match:
            day_name = match.group(1).capitalize()
            exercises_text = match.group(2).strip()

            # Mapeo de nombres a números
            day_map = {
                "Lunes": 1, "Martes": 2, "Miércoles": 3, "Jueves": 4,
                "Viernes": 5, "Sábado": 6, "Domingo": 7,
            }

            day_number = day_map.get(day_name)
            if not day_number:
                bot.send_message(chat_id, "¡ERROR! Día no reconocido. Usa: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado o Domingo.")
                return

            # Dividir los ejercicios por comas y limpiar espacios
            exercises = [e.strip() for e in exercises_text.split(",") if e.strip()]

            # Si la lista está vacía después de limpiar, significa "Descanso"
            if not exercises and exercises_text.lower() != 'descanso':
                 # Allow setting 'Descanso' explicitly or handle empty list case
                 if exercises_text.lower() != 'descanso':
                     bot.send_message(chat_id, "¡ERROR! No se encontraron ejercicios válidos. Separa los ejercicios con comas o escribe 'Descanso'.")
                     return
                 # If user writes 'Descanso', exercises list will be empty, which is correct for API
            elif exercises_text.lower() == 'descanso':
                 exercises = [] # Ensure exercises is an empty list for descanso


            log_to_console(f"Intentando configurar rutina para {day_name} (Día {day_number}) para usuario {chat_id}: {exercises}", "PROCESS")
            bot.send_chat_action(chat_id, "typing")

            try:
                # 1. Get the current full routine using ApiClient
                current_routine_data = ApiClient.get_routine(telegram_id=telegram_id_str)
                log_to_console(f"Rutina actual obtenida: {current_routine_data}", "DEBUG")

                # Initialize routine_to_save, handle potential errors from get_routine
                routine_to_save = {}
                if current_routine_data and current_routine_data.get("success"):
                    routine_to_save = current_routine_data.get("rutina", {}) # Expecting dict {"1": [...], "2": []...}
                    if routine_to_save is None: # Handle API potentially returning null
                        routine_to_save = {}
                elif current_routine_data and not current_routine_data.get("success"):
                    log_to_console(f"No se pudo obtener la rutina actual para modificar: {current_routine_data.get('message')}", "WARNING")
                    # Decide if you want to proceed with an empty routine or abort
                    # Proceeding with empty for now, API should handle creation/update
                # else: handle connection error case maybe? ApiClient might raise or return specific dict

                # 2. Update the specific day in the dictionary
                routine_to_save[str(day_number)] = exercises

                # 3. Save the updated full routine dictionary using ApiClient
                log_to_console(f"Enviando rutina actualizada a API: {routine_to_save}", "INFO")
                save_response = ApiClient.save_routine(telegram_id=telegram_id_str, routine_data=routine_to_save)

                log_to_console(f"Respuesta de guardado: {save_response}", "DEBUG")

                if save_response and save_response.get("success"):
                    exercises_display = ', '.join(exercises) if exercises else "Descanso"
                    bot.send_message(
                        chat_id,
                        f"🏋️‍♂️ *¡YEAH BUDDY!* 🏋️‍♂️\n\nRutina de *{day_name}* actualizada con éxito!\n\n"
                        f"Configurado: {exercises_display}\n\n"
                        "*¡LIGHTWEIGHT, BABY!*",
                        parse_mode="Markdown",
                    )
                    log_to_console(f"Rutina actualizada para {chat_id}, día {day_name}", "SUCCESS")
                else:
                    error_msg = save_response.get("message", "Error desconocido al guardar") if save_response else "Error desconocido"
                    bot.send_message(chat_id, f"Error al guardar la rutina: {error_msg}")
                    log_to_console(f"Error al guardar rutina: {error_msg}", "ERROR")

            except Exception as e:
                bot.send_message(
                    chat_id,
                    f"Error de conexión o procesamiento al configurar rutina. Por favor, inténtalo de nuevo más tarde.",
                )
                log_to_console(f"Excepción al configurar rutina: {str(e)}", "ERROR")
                # logging.exception("Exception details in set_routine_day:")