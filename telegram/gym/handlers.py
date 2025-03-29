# handlers.py
import re
import requests
import telebot
import json
import random
from utils import send_message_split, format_logs, is_user_whitelisted, log_denied_access, log_to_console

# Mantener la URL que funciona con los curls
BASE_URL = "http://localhost:5050"
DEFAULT_USER_ID = "3892415"  # Id por defecto si no viene en el mensaje

def get_chat_id(message):
    """
    Retorna el id del chat si existe; de lo contrario, retorna el id por defecto.
    """
    try:
        return str(message.chat.id)
    except AttributeError:
        return DEFAULT_USER_ID

def register_handlers(bot: telebot.TeleBot):
    # Registra un middleware global para loggear todos los mensajes entrantes
    @bot.middleware_handler(update_types=['message'])
    def log_all_messages(bot_instance, message):
        """Middleware para registrar todos los mensajes entrantes"""
        user_id = get_chat_id(message)
        if hasattr(message, 'text') and message.text:
            log_to_console(f"MENSAJE RECIBIDO - Usuario {user_id}: {message.text}", "INPUT")
    
    def check_whitelist(message):
        chat_id = get_chat_id(message)
        if not is_user_whitelisted(chat_id):
            denied_text = (
                "¡Oh no, brother! No tienes acceso para levantar en este bot.\n"
                "Ponte en contacto con el admin del bot para que te dé la autorización.\n"
                "¡Let's get those gains, baby!"
            )
            bot.send_message(chat_id, denied_text)
            log_denied_access(chat_id, message.text if hasattr(message, 'text') else "Sin texto")
            log_to_console(f"Acceso denegado para {chat_id}", "ACCESS_DENIED")
            return False
        return True

    # Comando /start: Mensaje de bienvenida al estilo Ronnie Coleman.
    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        welcome_text = (
            "¡Yeah buddy! Bienvenido a tu Bot de Gym, donde cada sesión es 'light weight, baby'!\n"
            "Usa /help para ver los comandos disponibles y saber cómo enviar tus ejercicios."
        )
        bot.send_message(chat_id, welcome_text)
        log_to_console(f"Comando /start - Bienvenida enviada a {chat_id}", "OUTPUT")

    # Comando /help: Muestra los comandos disponibles y cómo enviar ejercicios.
    @bot.message_handler(commands=["help"])
    def send_help(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        help_text = (
            "¡Yeah buddy! Aquí van los comandos:\n"
            "/toca - Ver qué ejercicios tocan hoy según tu rutina\n"
            "/rutina - Configurar tu rutina semanal\n"
            "/logs  - Consulta los ejercicios de los últimos 7 días (por defecto).\n"
            "/logsX - Consulta los ejercicios de los últimos X días. Ejemplo: /logs1, /logs2, /logs3, ...\n"
            "/ai - Consulta a tu entrenador personal AI. Ejemplo: /ai ¿Cómo mejorar mi press de banca?\n"
            "\n"
            "También puedes hacer preguntas directamente al Entrenador AI simplemente escribiendo tu pregunta normal.\n"
            "\n"
            "Para enviar tus ejercicios, utiliza este formato:\n"
            "Ejemplo: press banca 10x130,7x130,5x130 dominadas 10,9,5\n"
            "¡Suelta esas series y registra tu grandeza!"
        )
        bot.send_message(chat_id, help_text)
        log_to_console(f"Comando /help - Mostrando ayuda a {chat_id}", "OUTPUT")

    # Comando /ai: Interactúa con el entrenador personal AI
    @bot.message_handler(commands=["ai"])
    def chat_with_ai(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        
        # Extrae el texto después del comando
        ai_prompt = message.text.replace('/ai', '', 1).strip()
        
        if not ai_prompt:
            # Si no hay texto, pedir al usuario que proporcione una pregunta
            help_text = (
                "🤖 *¡ENTRENADOR AI EN LÍNEA!* 🤖\n\n"
                "Pregúntame sobre tu rutina, nutrición o entrenamiento.\n\n"
                "*Ejemplo:* /ai Necesito ejercicios para fortalecer los tríceps\n\n"
                "*¡LIGHTWEIGHT BABY!*"
            )
            bot.send_message(chat_id, help_text, parse_mode="Markdown")
            return
        
        # Enviar indicador de "escribiendo..."
        bot.send_chat_action(chat_id, "typing")
        log_to_console(f"Enviando pregunta al AI: {ai_prompt}", "PROCESS")
        
        # Llamada a la API del chatbot
        url = f"{BASE_URL}/api/chatbot/send"
        try:
            response = requests.post(
                url,
                json={"user_id": chat_id, "message": ai_prompt},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("responses"):
                    # Concatenar todas las respuestas en un solo mensaje
                    answer = ""
                    for resp in data["responses"]:
                        answer += resp.get("content", "") + "\n\n"
                    
                    # Añadir estilo Ronnie Coleman
                    answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{answer}\n\n*¡LIGHTWEIGHT BABY!*"
                    send_message_split(bot, chat_id, answer)
                else:
                    bot.send_message(
                        chat_id, 
                        "🤖 El entrenador AI está descansando ahora. ¡Inténtalo de nuevo en unos minutos! 🤖"
                    )
            else:
                bot.send_message(
                    chat_id, 
                    f"Error al comunicarse con el entrenador AI: {response.status_code}"
                )
        except Exception as e:
            bot.send_message(
                chat_id, 
                "No pude conectar con el entrenador AI. ¡Los músculos necesitan descanso a veces!"
            )
            log_to_console(f"Error en comunicación con el chatbot: {str(e)}", "ERROR")

    # Comando /logs (sin dígitos): Consulta los ejercicios de los últimos 7 días.
    @bot.message_handler(commands=["logs"])
    def send_logs_default(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        days = 7
        url = f"{BASE_URL}/logs"
        params = {"days": days, "user_id": chat_id}
        
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
    def send_logs_days(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        match = re.match(r"^/logs(\d+)$", message.text)
        if match:
            days = int(match.group(1))
            url = f"{BASE_URL}/logs"
            params = {"days": days, "user_id": chat_id}
            
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

    # Comando /toca: Muestra los ejercicios programados para hoy
    @bot.message_handler(commands=["toca"])
    def send_todays_workout(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        
        url = f"{BASE_URL}/rutina_hoy?format=json"  # Añadir format=json
        params = {"user_id": chat_id}  # Añadir user_id como parámetro
        
        log_to_console(f"Comando /toca - Usuario {chat_id} solicitando rutina de hoy", "PROCESS")
        
        try:
            # Usar el formato exacto que funciona en curl
            response = requests.get(url, params=params)
            log_to_console(f"API /rutina_hoy - Respuesta: {response.status_code}", "API")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("rutina"):
                    # Formato motivacional estilo Ronnie Coleman
                    formatted = f"🏋️‍♂️ *¡YEAH BUDDY! HOY ES {data['dia_nombre'].upper()}* 🏋️‍♂️\n\n"
                    formatted += "¡AIN'T NOTHING BUT A PEANUT! ESTO ES LO QUE TIENES QUE LEVANTAR HOY:\n\n"
                    
                    # Lista de ejercicios
                    for i, ejercicio in enumerate(data["rutina"], 1):
                        status = "✅" if ejercicio.get("realizado") else "⏱️"
                        formatted += f"{status} *{ejercicio['ejercicio'].upper()}*\n"
                    
                    # Mensaje motivacional para registrar
                    formatted += "\n💪 *¡LIGHTWEIGHT BABY!* 💪\n"
                    formatted += "\nRELLENA TUS SERIES Y RESPONDE CON ESTE MENSAJE:\n"
                    
                    # Proporcionar plantilla para rellenar
                    for ejercicio in data["rutina"]:
                        if not ejercicio.get("realizado"):
                            formatted += f"{ejercicio['ejercicio']}: \n"
                    
                    formatted += "\nEjemplo: Dominadas: 10,8,6\n"
                    formatted += "\n*¡EVERYBODY WANNA BE A BODYBUILDER, BUT DON'T NOBODY WANNA LIFT NO HEAVY WEIGHT!*"
                else:
                    formatted = "🏋️‍♂️ *¡LIGHTWEIGHT BABY!* 🏋️‍♂️\n\n"
                    formatted += "No hay rutina definida para hoy.\n"
                    formatted += "\nConfigura tu rutina con el comando /rutina\n"
                    formatted += "\n*¡NO PAIN, NO GAIN!*"
            else:
                formatted = f"Error al obtener la rutina: {response.status_code}"
                log_to_console(f"Error en API /rutina_hoy: {response.status_code} - {response.text}", "ERROR")
        except Exception as e:
            formatted = f"Error al conectar con el servidor: {e}"
            log_to_console(f"Excepción en /toca: {str(e)}", "ERROR")
        
        # Envía el mensaje con formato Markdown para destacar texto
        bot.send_message(chat_id, formatted, parse_mode="Markdown")
        log_to_console(f"Respuesta enviada a {chat_id} para comando /toca", "OUTPUT")

    # Comando /rutina: Permite configurar la rutina semanal
    @bot.message_handler(commands=["rutina"])
    def config_routine(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        
        # Obtener la rutina actual
        url = f"{BASE_URL}/rutina?format=json"
        params = {"user_id": chat_id}
        
        log_to_console(f"Comando /rutina - Usuario {chat_id} solicitando configuración de rutina", "PROCESS")
        
        try:
            # Usar el formato exacto que funciona en curl
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("rutina"):
                    # Mostrar la rutina actual
                    formatted = "🏋️‍♂️ *¡LIGHT WEIGHT BABY! TU RUTINA ACTUAL* 🏋️‍♂️\n\n"
                    
                    weekdays = [
                        {"id": 1, "name": "Lunes"},
                        {"id": 2, "name": "Martes"},
                        {"id": 3, "name": "Miércoles"},
                        {"id": 4, "name": "Jueves"},
                        {"id": 5, "name": "Viernes"},
                        {"id": 6, "name": "Sábado"},
                        {"id": 7, "name": "Domingo"}
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
                    
                    # Instrucciones para configurar
                    formatted += "\n💪 *PARA CONFIGURAR UN DÍA*: Envía un mensaje con el formato:\n"
                    formatted += "```\nDía: ejercicio1, ejercicio2, ...\n```\n"
                    formatted += "Ejemplo: Lunes: Press Banca, Dominadas, Triceps\n\n"
                    formatted += "*EVERYBODY WANNA BE A BODYBUILDER, BUT DON'T NOBODY WANNA LIFT NO HEAVY WEIGHT!*"
                else:
                    # No hay rutina configurada, mostrar instrucciones
                    formatted = "🏋️‍♂️ *¡NO PAIN NO GAIN! CONFIGURA TU RUTINA* 🏋️‍♂️\n\n"
                    formatted += "No tienes una rutina configurada aún. Para configurar, envía un mensaje con el formato:\n"
                    formatted += "```\nDía: ejercicio1, ejercicio2, ...\n```\n"
                    formatted += "Ejemplo: Lunes: Press Banca, Dominadas, Triceps\n\n"
                    formatted += "*¡LIGHTWEIGHT BABY!*"
            else:
                formatted = f"Error al obtener la rutina: {response.status_code}"
                log_to_console(f"Error en API /rutina: {response.status_code} - {response.text}", "ERROR")
        except Exception as e:
            formatted = f"Error al conectar con el servidor: {e}"
            log_to_console(f"Excepción en /rutina: {str(e)}", "ERROR")
        
        # Envía el mensaje con formato Markdown
        bot.send_message(chat_id, formatted, parse_mode="Markdown")
        log_to_console(f"Respuesta enviada a {chat_id} para comando /rutina", "OUTPUT")

    # Handler para configurar rutina por día
    # Handler para configurar rutina por día
    @bot.message_handler(regexp=r"^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo):\s*(.+)$")
    def set_routine_day(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
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
                "Domingo": 7
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
            
            # Obtener la rutina actual
            url = f"{BASE_URL}/rutina"
            
            try:
                log_to_console(f"Intentando obtener rutina actual para usuario {chat_id}...", "INFO")
                
                # Enviar mensaje para que el usuario sepa que estamos procesando
                bot.send_chat_action(chat_id, "typing")
                
                # Primero obtenemos la rutina actual
                response = requests.get(url, params={"user_id": chat_id})
                
                log_to_console(f"Respuesta del servidor: Status {response.status_code}", "DEBUG")
                
                if response.status_code == 200:
                    try:
                        # Intentar decodificar la respuesta JSON
                        raw_text = response.text
                        log_to_console(f"Texto de respuesta: {raw_text[:100]}...", "DEBUG")  # Logueamos los primeros 100 caracteres para debug
                        
                        if not raw_text or raw_text.isspace():
                            log_to_console("Respuesta vacía recibida del servidor", "ERROR")
                            current_routine = {}
                        else:
                            data = response.json()
                            current_routine = data.get("rutina", {})
                            
                            # Si rutina no existe o es None, inicializarla como un diccionario vacío
                            if current_routine is None:
                                current_routine = {}
                        
                        # Actualizar solo el día especificado
                        current_routine[str(day_number)] = exercises
                        
                        # Enviar la rutina actualizada
                        payload = {"rutina": current_routine, "user_id": chat_id}
                        log_to_console(f"Enviando payload: {json.dumps(payload)}", "INFO")
                        
                        update_response = requests.post(
                            url,
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        log_to_console(f"Respuesta de actualización: {update_response.status_code}", "DEBUG")
                        
                        if update_response.status_code == 200:
                            # Éxito al actualizar
                            bot.send_message(
                                chat_id, 
                                f"🏋️‍♂️ *¡YEAH BUDDY!* 🏋️‍♂️\n\nRutina de *{day_name}* actualizada con éxito!\n\n"
                                f"Ejercicios configurados: {', '.join(exercises)}\n\n"
                                "*¡LIGHTWEIGHT, BABY!*", 
                                parse_mode="Markdown"
                            )
                            log_to_console(f"Rutina actualizada para {chat_id}, día {day_name}", "SUCCESS")
                        else:
                            # Error al actualizar
                            error_msg = f"Error al actualizar la rutina: {update_response.status_code}"
                            try:
                                error_detail = update_response.json().get("message", "No hay detalles adicionales")
                                error_msg += f"\n{error_detail}"
                            except:
                                error_msg += "\nNo se pudo obtener detalles del error"
                            
                            bot.send_message(chat_id, error_msg)
                            log_to_console(error_msg, "ERROR")
                    
                    except json.JSONDecodeError as e:
                        # Error específico al decodificar JSON
                        log_to_console(f"Error al decodificar JSON: {e}. Respuesta: {response.text[:200]}", "ERROR")
                        
                        # Intentar crear una rutina desde cero
                        current_routine = {}
                        current_routine[str(day_number)] = exercises
                        
                        # Intentar enviar la rutina nueva
                        payload = {"rutina": current_routine, "user_id": chat_id}
                        log_to_console(f"Intentando crear nueva rutina: {json.dumps(payload)}", "INFO")
                        
                        try:
                            update_response = requests.post(
                                url,
                                json=payload,
                                headers={"Content-Type": "application/json"}
                            )
                            
                            if update_response.status_code == 200:
                                bot.send_message(
                                    chat_id, 
                                    f"🏋️‍♂️ *¡YEAH BUDDY!* 🏋️‍♂️\n\nRutina de *{day_name}* creada con éxito!\n\n"
                                    "*¡LIGHTWEIGHT, BABY!*", 
                                    parse_mode="Markdown"
                                )
                            else:
                                bot.send_message(
                                    chat_id, 
                                    f"Error al crear la rutina. Por favor, inténtalo de nuevo más tarde."
                                )
                        except Exception as inner_e:
                            bot.send_message(
                                chat_id, 
                                f"Error al procesar la rutina. Inténtalo de nuevo más tarde."
                            )
                            log_to_console(f"Error al crear rutina: {str(inner_e)}", "ERROR")
                else:
                    # Error en la solicitud inicial
                    bot.send_message(
                        chat_id, 
                        f"Error al obtener la rutina actual: {response.status_code}. Por favor, inténtalo de nuevo más tarde."
                    )
                    log_to_console(f"Error HTTP {response.status_code} al obtener rutina", "ERROR")
            
            except Exception as e:
                # Error general (probablemente de red)
                bot.send_message(
                    chat_id, 
                    f"Error al conectar con el servidor. Por favor, inténtalo de nuevo más tarde."
                )
                log_to_console(f"Excepción al configurar rutina: {str(e)}", "ERROR")
    # Handler para mensajes de texto no comando
    @bot.message_handler(func=lambda message: not message.text.startswith("/"))
    def process_text_message(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        
        # Analizar el mensaje para determinar si es un registro de ejercicio o una pregunta
        text = message.text.lower()
        
        # Patrones que indican que es un registro de ejercicio
        exercise_patterns = [
            r'\d+x\d+',        # Patrón de "repeticionesx1peso" (ej: 5x75)
            r'press banca|dominadas|sentadillas|curl|press militar',  # Nombres comunes de ejercicios
            r'\b\d+,\s*\d+\b'  # Series separadas por comas (ej: 10, 8, 6)
        ]
        
        is_exercise = any(re.search(pattern, text, re.IGNORECASE) for pattern in exercise_patterns)
        
        if is_exercise:
            # Procesar como registro de ejercicio
            # Mostrar "escribiendo..." mientras se procesa
            bot.send_chat_action(chat_id, "typing")
            
            # Usar multipart/form-data como en el curl
            data = {"exercise_data": message.text, "user_id": chat_id}
            
            log_to_console(f"Ejercicio recibido - Usuario {chat_id}: {message.text}", "PROCESS")
            
            try:
                # Enviar en el formato exacto que funciona con curl
                response = requests.post(BASE_URL, data=data)
                log_to_console(f"API envío ejercicio - Respuesta: {response.status_code}", "API")
                
                # Generar una respuesta motivacional aleatoria estilo Ronnie Coleman
                ronnie_quotes = [
                    "¡YEAH BUDDY! ¡LIGHTWEIGHT BABY! Tu entrenamiento ha sido registrado. ¡HOO! ¡EVERYBODY WANNA BE A BODYBUILDER!",
                    "¡BOOOM! ¡EJERCICIO REGISTRADO! ¡AIN'T NOTHIN' BUT A PEANUT!",
                    "¡WHOOOOOO! ¡REGISTRO COMPLETADO! ¡ESO ES TODO LO QUE TIENES, BABY! ¡LIGHTWEIGHT!",
                    "¡YEAH BUDDY! ¡BRUTAL! Ejercicio registrado. ¡LIGHTWEIGHT, BABY, LIGHTWEIGHT!",
                    "¡ESO ES! ¡Ejercicio registrado! ¡NADIE QUIERE LEVANTAR ESTE PESO PESADO PERO YO SÍ!",
                    "¡REGISTRO EXITOSO! ¡HOO! ¡EVERYBODY WANTS TO BE A BODYBUILDER, BUT NOBODY WANTS TO LIFT NO HEAVY WEIGHT!",
                    "¡TIME TO BLEED! ¡Ejercicio registrado! ¡NO PAIN, NO GAIN!",
                    "¡BOOM! ¡HICISTE ESO! ¡Ejercicio registrado! ¡NO EXCUSES, ONLY RESULTS!",
                    "¡OOOH YEAH! ¡ERES UNA MÁQUINA! ¡Ejercicio registrado! ¡LIGHTWEIGHT BABY!",
                    "¡YEP YEP! ¡Ejercicio registrado! ¡NOTHING TO IT BUT TO DO IT!"
                ]
                
                # Frases para errores
                error_quotes = [
                    "¡WHOOPS! ¡ESO FUE MÁS PESADO DE LO ESPERADO! Error al registrar. ¡VAMOS A INTENTARLO DE NUEVO, BABY!",
                    "¡OOOH! ¡PARECE QUE NECESITAMOS MÁS FUERZA PARA ESTE REGISTRO! Error al conectar con el servidor.",
                    "¡UH OH! ¡ESTE PESO SE RESISTE! No se pudo registrar tu ejercicio. ¡VAMOS DE NUEVO!",
                    "¡EVERYBODY WANTS TO REGISTER, BUT SOMETIMES THE SERVER SAYS NO! Error en la conexión. ¡NO TE RINDAS!",
                    "¡AIN'T NOTHING BUT A SERVER ERROR, BABY! Intentémoslo de nuevo. ¡LIGHTWEIGHT!"
                ]
                
                ronnie_quote = random.choice(ronnie_quotes)
                error_quote = random.choice(error_quotes)
                
                if response.status_code == 200:
                    bot.send_message(
                        chat_id, 
                        f"🏋️‍♂️ *{ronnie_quote}* 🏋️‍♂️",
                        parse_mode="Markdown"
                    )
                    
                    # Sugerir próximas acciones
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    keyboard.add(
                        telebot.types.InlineKeyboardButton("Ver mi rutina de hoy", callback_data="cmd_toca"),
                        telebot.types.InlineKeyboardButton("Ver mis logs", callback_data="cmd_logs")
                    )
                    keyboard.add(
                        telebot.types.InlineKeyboardButton("Consultar al AI", callback_data="cmd_ai")
                    )
                    
                    bot.send_message(
                        chat_id,
                        "¿Qué quieres hacer ahora?",
                        reply_markup=keyboard
                    )
                    
                    log_to_console(f"Ejercicio registrado correctamente para usuario {chat_id}", "SUCCESS")
                else:
                    bot.send_message(
                        chat_id, 
                        f"🏋️‍♂️ *{error_quote}* 🏋️‍♂️\n\nCódigo: {response.status_code}",
                        parse_mode="Markdown"
                    )
                    log_to_console(f"Error al registrar ejercicio: {response.status_code} - {response.text}", "ERROR")
            except Exception as e:
                error_msg = f"Error al enviar el ejercicio: {str(e)}"
                bot.send_message(
                    chat_id, 
                    f"🏋️‍♂️ *{random.choice(error_quotes)}* 🏋️‍♂️",
                    parse_mode="Markdown"
                )
                log_to_console(error_msg, "ERROR")
        else:
            # Procesar como pregunta para el AI
            # Mostrar "escribiendo..." mientras se procesa
            bot.send_chat_action(chat_id, "typing")
            
            log_to_console(f"Pregunta recibida - Usuario {chat_id}: {message.text}", "PROCESS")
            
            # Llamada a la API del chatbot
            url = f"{BASE_URL}/api/chatbot/send"
            try:
                response = requests.post(
                    url,
                    json={"user_id": chat_id, "message": message.text},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("responses"):
                        # Concatenar todas las respuestas en un solo mensaje
                        answer = ""
                        for resp in data["responses"]:
                            answer += resp.get("content", "") + "\n\n"
                        
                        # Añadir estilo Ronnie Coleman
                        answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{answer}\n\n*¡LIGHTWEIGHT BABY!*"
                        send_message_split(bot, chat_id, answer)
                    else:
                        bot.send_message(
                            chat_id, 
                            "🤖 El entrenador AI está descansando ahora. ¡Inténtalo de nuevo en unos minutos! 🤖"
                        )
                else:
                    bot.send_message(
                        chat_id, 
                        f"Error al comunicarse con el entrenador AI: {response.status_code}"
                    )
            except Exception as e:
                bot.send_message(
                    chat_id, 
                    "No pude conectar con el entrenador AI. ¡Los músculos necesitan descanso a veces!"
                )
                log_to_console(f"Error en comunicación con el chatbot: {str(e)}", "ERROR")

    # Manejar los botones inline
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        chat_id = str(call.message.chat.id)
        
        # Verificar si el usuario está en la lista blanca
        if not is_user_whitelisted(chat_id):
            bot.answer_callback_query(call.id, "No tienes acceso a esta función")
            return
        
        if call.data == "cmd_toca":
            # Responder al callback y luego enviar comando directamente
            bot.answer_callback_query(call.id, "Obteniendo tu rutina de hoy...")
            
            # En lugar de crear un mensaje simulado, enviar directamente la respuesta
            url = f"{BASE_URL}/rutina_hoy?format=json"
            params = {"user_id": chat_id}
            
            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("rutina"):
                        # Mismo formato que en send_todays_workout
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
                        formatted = "🏋️‍♂️ *¡LIGHTWEIGHT BABY!* 🏋️‍♂️\n\n"
                        formatted += "No hay rutina definida para hoy.\n"
                        formatted += "\nConfigura tu rutina con el comando /rutina\n"
                        formatted += "\n*¡NO PAIN, NO GAIN!*"
                    
                    bot.send_message(chat_id, formatted, parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, f"Error al obtener la rutina: {response.status_code}")
            except Exception as e:
                bot.send_message(chat_id, f"Error al conectar con el servidor: {e}")
            
        elif call.data == "cmd_logs":
            # Responder al callback y luego enviar logs
            bot.answer_callback_query(call.id, "Obteniendo tus logs...")
            
            days = 7
            url = f"{BASE_URL}/logs"
            params = {"days": days, "user_id": chat_id}
            
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
            # Invitar a usar el comando /ai
            bot.answer_callback_query(call.id, "Activando el asistente AI...")
            bot.send_message(
                chat_id,
                "🤖 *¡ENTRENADOR AI EN LÍNEA!* 🤖\n\n"
                "Usa el comando /ai seguido de tu pregunta:\n\n"
                "Ejemplo: /ai Recomiéndame ejercicios para bíceps\n\n"
                "*¡LIGHTWEIGHT BABY!*",
                parse_mode="Markdown"
            )

    # Añadir a handlers.py en telegram/gym

    # Comando /vincular
    @bot.message_handler(commands=["vincular"])
    def link_account_command(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        
        bot.send_message(
            chat_id, 
            "🔗 *Vincular con cuenta web*\n\n"
            "Por favor, envía el código de vinculación que ves en la web.\n"
            "El código debe ser de 6 caracteres (letras y números).",
            parse_mode="Markdown"
        )
        
        # Registrar el siguiente paso para procesar el código
        bot.register_next_step_handler(message, process_link_code)

    def process_link_code(message):
        chat_id = get_chat_id(message)
        if not check_whitelist(message):
            return
        
        code = message.text.strip().upper()
        telegram_id = str(chat_id)
        
        # Validar formato del código (6 caracteres alfanuméricos)
        if not re.match(r'^[A-Z0-9]{6}$', code):
            bot.send_message(
                chat_id, 
                "❌ El código debe ser de 6 caracteres (letras y números).\n"
                "Por favor, intenta de nuevo con /vincular"
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
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    bot.send_message(
                        chat_id, 
                        "✅ *¡Cuentas vinculadas con éxito!*\n\n"
                        "Ahora puedes acceder a tus datos desde la web y desde Telegram.\n"
                        "Tus entrenamientos se sincronizarán automáticamente entre ambas plataformas.",
                        parse_mode="Markdown"
                    )
                else:
                    bot.send_message(
                        chat_id, 
                        f"❌ Error: {data.get('message', 'Código inválido o expirado')}.\n"
                        "Por favor, genera un nuevo código en la web e inténtalo de nuevo con /vincular"
                    )
            else:
                bot.send_message(
                    chat_id,
                    "❌ Error al verificar el código. Por favor, intenta nuevamente."
                )
        except Exception as e:
            bot.send_message(
                chat_id,
                "❌ Error al conectar con el servidor. Por favor, intenta más tarde."
            )
            log_to_console(f"Error en verificación de código: {str(e)}", "ERROR")