# telegram/gym/handlers/chatbot_handlers.py
import re
import logging
import requests
import os
from telebot.types import Message
from utils import send_message_split
from config import WHITELIST_PATH

from .base_handlers import (check_whitelist, get_api_user_id, get_telegram_id,
                            log_to_console)

# Intentar importar el proceso de mensaje de LangGraph
try:
    from fitness_chatbot.nodes.router_node import process_message
    CHATBOT_AVAILABLE = True
    log_to_console("✅ Fitness Chatbot (LangGraph) disponible")
except ImportError as e:
    CHATBOT_AVAILABLE = False
    log_to_console(f"⚠️ Fitness Chatbot (LangGraph) no disponible, usando API: {e}", "WARNING")

def register_chatbot_handlers(bot):
    """
    Registra los handlers relacionados con el chatbot AI.
    
    Args:
        bot: Instancia del bot de Telegram
    """
    # Comando /ai: Interactúa con el entrenador personal AI
    @bot.message_handler(commands=["ai"])
    def chat_with_ai(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        api_user_id = get_api_user_id(message)
        
        # Verificación directa de whitelist
        try:
            with open(WHITELIST_PATH, "r") as f:
                whitelist_contents = f.read().strip().split('\n')
                whitelist_contents = [w.strip() for w in whitelist_contents]
                
            is_allowed = str(chat_id) in whitelist_contents
            print(f"✅ ¿Usuario {chat_id} está en whitelist para AI? {is_allowed}")
            
            if not is_allowed:
                bot.send_message(
                    chat_id,
                    f"🔒 Acceso denegado. Tu ID de Telegram es: {chat_id}\n"
                    "Contacta al administrador para obtener acceso."
                )
                log_to_console(f"❌ Usuario {chat_id} no está en whitelist - Acceso denegado a /ai", "ACCESS_DENIED")
                return
        except Exception as e:
            print(f"❌ Error verificando whitelist para AI: {e}")
            # Si hay error en la verificación, continuamos

        # Extrae el texto después del comando
        ai_prompt = message.text.replace("/ai", "", 1).strip()

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
        log_to_console(f"Enviando pregunta al AI: {ai_prompt} (API user_id: {api_user_id})", "PROCESS")

        try:
            # Intentar usar el chatbot de LangGraph directamente
            if CHATBOT_AVAILABLE:
                try:
                    # Usar process_message del LangGraph
                    import asyncio
                    
                    # Ejecutar de forma asíncrona pero bloqueando hasta completar
                    response = asyncio.run(process_message(api_user_id, ai_prompt))
                    
                    # Formatear la respuesta
                    answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{response.content}\n\n*¡LIGHTWEIGHT BABY!*"
                    send_message_split(bot, chat_id, answer, parse_mode="Markdown")
                    
                    log_to_console(f"Respuesta del AI enviada a {chat_id}", "OUTPUT")
                    return
                    
                except Exception as e:
                    log_to_console(f"Error usando LangGraph: {str(e)}", "ERROR")
                    # Continuar con API como fallback
            
            # FALLBACK: Usar la API si LangGraph no está disponible o falló
            from config import BASE_URL
            url = f"{BASE_URL}/api/chatbot/send"
            
            # Incluir headers correctos en la solicitud
            from api_client import ApiClient
            headers = ApiClient.get_headers()
            
            log_to_console(f"Enviando solicitud a {url} con headers: {headers}", "DEBUG")
            
            response = requests.post(
                url,
                json={"user_id": api_user_id, "message": ai_prompt},
                headers=headers,
            )
            
            log_to_console(f"API response status: {response.status_code}", "INFO")
            if response.status_code == 200:
                data = response.json()
                log_to_console(f"API response data: {data}", "DEBUG")
                if data.get("success") and data.get("responses"):
                    answer = ""
                    for resp in data["responses"]:
                        answer += resp.get("content", "") + "\n\n"
                    answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{answer}\n\n*¡LIGHTWEIGHT BABY!*"
                    send_message_split(bot, chat_id, answer, parse_mode="Markdown")
                else:
                    bot.send_message(
                        chat_id,
                        "🤖 El entrenador AI está descansando ahora. ¡Inténtalo de nuevo en unos minutos! 🤖",
                    )
            else:
                bot.send_message(
                    chat_id,
                    f"Error al comunicarse con el entrenador AI: {response.status_code}",
                )
        except Exception as e:
            log_to_console(f"Error en comunicación con el chatbot: {str(e)}", "ERROR")
            logging.exception("Error completo en chat_with_ai:")
            bot.send_message(
                chat_id,
                "No pude conectar con el entrenador AI. ¡Los músculos necesitan descanso a veces!",
            )

    # Handler para mensajes de texto que no son comandos ni ejercicios
    # Este handler debe estar después del de ejercicios para no interferir
    @bot.message_handler(func=lambda message: True)
    def handle_general_message(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        api_user_id = get_api_user_id(message)
        
        # Verificación directa de whitelist
        try:
            with open(WHITELIST_PATH, "r") as f:
                whitelist_contents = f.read().strip().split('\n')
                whitelist_contents = [w.strip() for w in whitelist_contents]
                
            is_allowed = str(chat_id) in whitelist_contents
            print(f"✅ ¿Usuario {chat_id} está en whitelist para mensaje general? {is_allowed}")
            
            if not is_allowed:
                bot.send_message(
                    chat_id,
                    f"🔒 Acceso denegado. Tu ID de Telegram es: {chat_id}\n"
                    "Contacta al administrador para obtener acceso."
                )
                log_to_console(f"❌ Usuario {chat_id} no está en whitelist - Acceso denegado a mensaje general", "ACCESS_DENIED")
                return
        except Exception as e:
            print(f"❌ Error verificando whitelist para mensaje general: {e}")
            # Si hay error en la verificación, continuamos
            
        # Si llegamos aquí, el mensaje no es un comando ni un ejercicio
        # Así que lo tratamos como una pregunta para el AI
        
        # Enviar indicador de "escribiendo..."
        bot.send_chat_action(chat_id, "typing")
        log_to_console(f"Pregunta recibida - Usuario {chat_id} (API user_id: {api_user_id}): {message.text}", "PROCESS")
        
        try:
            # Intentar usar el chatbot de LangGraph directamente
            if CHATBOT_AVAILABLE:
                try:
                    # Usar process_message del LangGraph
                    import asyncio
                    
                    # Ejecutar de forma asíncrona pero bloqueando hasta completar
                    response = asyncio.run(process_message(api_user_id, message.text))
                    
                    # Formatear la respuesta
                    answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{response.content}\n\n*¡LIGHTWEIGHT BABY!*"
                    send_message_split(bot, chat_id, answer, parse_mode="Markdown")
                    
                    log_to_console(f"Respuesta del AI enviada a {chat_id}", "OUTPUT")
                    return
                    
                except Exception as e:
                    log_to_console(f"Error usando LangGraph: {str(e)}", "ERROR")
                    # Continuar con API como fallback
            
            # FALLBACK: Usar la API si LangGraph no está disponible o falló
            from config import BASE_URL
            url = f"{BASE_URL}/api/chatbot/send"
            
            # Usar ApiClient para obtener headers correctos
            from api_client import ApiClient
            headers = ApiClient.get_headers()
            
            log_to_console(f"Enviando solicitud a {url} con headers: {headers}", "DEBUG")
            
            response = requests.post(
                url,
                json={"user_id": api_user_id, "message": message.text},
                headers=headers,
            )
            
            log_to_console(f"API response status: {response.status_code}", "INFO")
            if response.status_code == 200:
                data = response.json()
                log_to_console(f"API response data: {data}", "DEBUG")
                if data.get("success") and data.get("responses"):
                    answer = ""
                    for resp in data["responses"]:
                        answer += resp.get("content", "") + "\n\n"
                    answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{answer}\n\n*¡LIGHTWEIGHT BABY!*"
                    send_message_split(bot, chat_id, answer, parse_mode="Markdown")
                else:
                    bot.send_message(
                        chat_id,
                        "🤖 El entrenador AI está descansando ahora. ¡Inténtalo de nuevo en unos minutos! 🤖",
                    )
            else:
                bot.send_message(
                    chat_id,
                    f"Error al comunicarse con el entrenador AI: {response.status_code}",
                )
        except Exception as e:
            log_to_console(f"Error en comunicación con el chatbot: {str(e)}", "ERROR")
            logging.exception("Error completo en handle_general_message:")
            bot.send_message(
                chat_id,
                "No pude conectar con el entrenador AI. ¡Los músculos necesitan descanso a veces!",
            )