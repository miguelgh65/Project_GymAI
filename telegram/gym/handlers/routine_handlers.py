# telegram/gym/handlers/routine_handlers.py
import re
import json
import requests
from telebot.types import Message
from .base_handlers import get_chat_id, check_whitelist, log_to_console
from config import BASE_URL

def register_routine_handlers(bot):
    """
    Registra los handlers relacionados con rutinas.
    
    Args:
        bot: Instancia del bot de Telegram
    """
    # Comando /toca: Muestra los ejercicios programados para hoy
    @bot.message_handler(commands=["toca"])
    def send_todays_workout(message: Message) -> None:
        chat_id = get_chat_id(message)
        if not check_whitelist(message, bot):
            return

        url = f"{BASE_URL}/rutina_hoy?format=json"  # Añadir format=json
        params = {"user_id": chat_id}  # Añadir user_id como parámetro

        log_to_console(f"Comando /toca - Usuario {chat_id} solicitando rutina de hoy", "PROCESS")

        try:
            response = requests.get(url, params=params)
            log_to_console(f"API /rutina_hoy - Respuesta: {response.status_code}", "API")

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
            else:
                formatted = f"Error al obtener la rutina: {response.status_code}"
                log_to_console(f"Error en API /rutina_hoy: {response.status_code} - {response.text}", "ERROR")
        except Exception as e:
            formatted = f"Error al conectar con el servidor: {e}"
            log_to_console(f"Excepción en /toca: {str(e)}", "ERROR")

        bot.send_message(chat_id, formatted, parse_mode="Markdown")
        log_to_console(f"Respuesta enviada a {chat_id} para comando /toca", "OUTPUT")

    # Comando /rutina: Permite configurar la rutina semanal
    @bot.message_handler(commands=["rutina"])
    def config_routine(message: Message) -> None:
        chat_id = get_chat_id(message)
        if not check_whitelist(message, bot):
            return

        url = f"{BASE_URL}/rutina?format=json"
        params = {"user_id": chat_id}

        log_to_console(f"Comando /rutina - Usuario {chat_id} solicitando configuración de rutina", "PROCESS")

        try:
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("rutina"):
                    formatted = "🏋️‍♂️ *¡LIGHT WEIGHT BABY! TU RUTINA ACTUAL* 🏋️‍♂️\n\n"

                    weekdays = [
                        {"id": 1, "name": "Lunes"},
                        {"id": 2, "name": "Martes"},
                        {"id": 3, "name": "Miércoles"},
                        {"id": 4, "name": "Jueves"},
                        {"id": 5, "name": "Viernes"},
                        {"id": 6, "name": "Sábado"},
                        {"id": 7, "name": "Domingo"},
                    ]

                    for day in weekdays:
                        day_id = str(day["id"])
                        formatted += f"*{day['name']}*: "

                        if day_id in data["rutina"] and data["rutina"][day_id]:
                            exercises = ", ".join(data["rutina"][day_id])
                            formatted += exercises
                        else:
                            formatted += "Descanso"

                        formatted += "\n"

                    formatted += "\n💪 *PARA CONFIGURAR UN DÍA*: Envía un mensaje con el formato:\n"
                    formatted += "```\nDía: ejercicio1, ejercicio2, ...\n```\n"
                    formatted += "Ejemplo: Lunes: Press Banca, Dominadas, Triceps\n\n"
                    formatted += "*EVERYBODY WANNA BE A BODYBUILDER, BUT DON'T NOBODY WANNA LIFT NO HEAVY WEIGHT!*"
                else:
                    formatted = (
                        "🏋️‍♂️ *¡NO PAIN NO GAIN! CONFIGURA TU RUTINA* 🏋️‍♂️\n\n"
                        "No tienes una rutina configurada aún. Para configurar, envía un mensaje con el formato:\n"
                        "```\nDía: ejercicio1, ejercicio2, ...\n```\n"
                        "Ejemplo: Lunes: Press Banca, Dominadas, Triceps\n\n"
                        "*¡LIGHTWEIGHT BABY!*"
                    )
            else:
                formatted = f"Error al obtener la rutina: {response.status_code}"
                log_to_console(f"Error en API /rutina: {response.status_code} - {response.text}", "ERROR")
        except Exception as e:
            formatted = f"Error al conectar con el servidor: {e}"
            log_to_console(f"Excepción en /rutina: {str(e)}", "ERROR")

        bot.send_message(chat_id, formatted, parse_mode="Markdown")
        log_to_console(f"Respuesta enviada a {chat_id} para comando /rutina", "OUTPUT")

    # Handler para configurar rutina por día
    @bot.message_handler(regexp=r"^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo):\s*(.+)$")
    def set_routine_day(message: Message) -> None:
        chat_id = get_chat_id(message)
        if not check_whitelist(message, bot):
            return

        match = re.match(r"^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo):\s*(.+)$", message.text, re.IGNORECASE)
        if match:
            day_name = match.group(1).capitalize()
            exercises_text = match.group(2).strip()

            # Mapeo de nombres a números
            day_map = {
                "Lunes": 1,
                "Martes": 2,
                "Miércoles": 3,
                "Jueves": 4,
                "Viernes": 5,
                "Sábado": 6,
                "Domingo": 7,
            }

            day_number = day_map.get(day_name)
            if not day_number:
                bot.send_message(chat_id, "¡ERROR! Día no reconocido. Usa: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado o Domingo.")
                return

            # Dividir los ejercicios por comas
            exercises = [e.strip() for e in exercises_text.split(",") if e.strip()]
            if not exercises:
                bot.send_message(chat_id, "¡ERROR! No se encontraron ejercicios válidos. Asegúrate de separar los ejercicios con comas.")
                return

            url = f"{BASE_URL}/rutina"

            try:
                log_to_console(f"Intentando obtener rutina actual para usuario {chat_id}...", "INFO")
                bot.send_chat_action(chat_id, "typing")
                response = requests.get(url, params={"user_id": chat_id})
                log_to_console(f"Respuesta del servidor: Status {response.status_code}", "DEBUG")

                if response.status_code == 200:
                    try:
                        raw_text = response.text
                        log_to_console(f"Texto de respuesta: {raw_text[:100]}...", "DEBUG")
                        if not raw_text or raw_text.isspace():
                            log_to_console("Respuesta vacía recibida del servidor", "ERROR")
                            current_routine = {}
                        else:
                            data = response.json()
                            current_routine = data.get("rutina", {})
                            if current_routine is None:
                                current_routine = {}
                        current_routine[str(day_number)] = exercises
                        payload = {"rutina": current_routine, "user_id": chat_id}
                        log_to_console(f"Enviando payload: {json.dumps(payload)}", "INFO")
                        update_response = requests.post(
                            url,
                            json=payload,
                            headers={"Content-Type": "application/json"},
                        )
                        log_to_console(f"Respuesta de actualización: {update_response.status_code}", "DEBUG")

                        if update_response.status_code == 200:
                            bot.send_message(
                                chat_id,
                                f"🏋️‍♂️ *¡YEAH BUDDY!* 🏋️‍♂️\n\nRutina de *{day_name}* actualizada con éxito!\n\n"
                                f"Ejercicios configurados: {', '.join(exercises)}\n\n"
                                "*¡LIGHTWEIGHT, BABY!*",
                                parse_mode="Markdown",
                            )
                            log_to_console(f"Rutina actualizada para {chat_id}, día {day_name}", "SUCCESS")
                        else:
                            error_msg = f"Error al actualizar la rutina: {update_response.status_code}"
                            try:
                                error_detail = update_response.json().get("message", "No hay detalles adicionales")
                                error_msg += f"\n{error_detail}"
                            except Exception:
                                error_msg += "\nNo se pudo obtener detalles del error"
                            bot.send_message(chat_id, error_msg)
                            log_to_console(error_msg, "ERROR")
                    except json.JSONDecodeError as e:
                        log_to_console(f"Error al decodificar JSON: {e}. Respuesta: {response.text[:200]}", "ERROR")
                        current_routine = {}
                        current_routine[str(day_number)] = exercises
                        payload = {"rutina": current_routine, "user_id": chat_id}
                        log_to_console(f"Intentando crear nueva rutina: {json.dumps(payload)}", "INFO")
                        try:
                            update_response = requests.post(
                                url,
                                json=payload,
                                headers={"Content-Type": "application/json"},
                            )
                            if update_response.status_code == 200:
                                bot.send_message(
                                    chat_id,
                                    f"🏋️‍♂️ *¡YEAH BUDDY!* 🏋️‍♂️\n\nRutina de *{day_name}* creada con éxito!\n\n"
                                    "*¡LIGHTWEIGHT, BABY!*",
                                    parse_mode="Markdown",
                                )
                            else:
                                bot.send_message(
                                    chat_id,
                                    f"Error al crear la rutina. Por favor, inténtalo de nuevo más tarde.",
                                )
                        except Exception as inner_e:
                            bot.send_message(
                                chat_id,
                                f"Error al procesar la rutina. Inténtalo de nuevo más tarde.",
                            )
                            log_to_console(f"Error al crear rutina: {str(inner_e)}", "ERROR")
                else:
                    bot.send_message(
                        chat_id,
                        f"Error al obtener la rutina actual: {response.status_code}. Por favor, inténtalo de nuevo más tarde.",
                    )
                    log_to_console(f"Error HTTP {response.status_code} al obtener rutina", "ERROR")
            except Exception as e:
                bot.send_message(
                    chat_id,
                    f"Error al conectar con el servidor. Por favor, inténtalo de nuevo más tarde.",
                )
                log_to_console(f"Excepción al configurar rutina: {str(e)}", "ERROR")