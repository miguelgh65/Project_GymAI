# telegram/gym/handlers/chatbot_handlers.py
import re
import requests
from telebot.types import Message
from .base_handlers import get_telegram_id, get_api_user_id, check_whitelist, log_to_console
from utils import send_message_split
from config import BASE_URL

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
        
        if not check_whitelist(message, bot):
            return

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
            # Opción 1: Usar directamente la función del fitness_agent
            try:
                from fitness_agent.agent.nodes.router_node import process_message
                
                response = process_message(api_user_id, ai_prompt)
                
                # Formatear la respuesta
                answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{response.content}\n\n*¡LIGHTWEIGHT BABY!*"
                send_message_split(bot, chat_id, answer, parse_mode="Markdown")
                
                log_to_console(f"Respuesta del AI enviada a {chat_id}", "OUTPUT")
                
            # Opción 2: Usar la API si la importación directa falla    
            except ImportError:
                log_to_console("Importación de process_message falló, usando API", "WARNING")
                url = f"{BASE_URL}/api/chatbot/send"
                
                response = requests.post(
                    url,
                    json={"user_id": api_user_id, "message": ai_prompt},
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code == 200:
                    data = response.json()
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
            bot.send_message(
                chat_id,
                "No pude conectar con el entrenador AI. ¡Los músculos necesitan descanso a veces!",
            )
            log_to_console(f"Error en comunicación con el chatbot: {str(e)}", "ERROR")

    # Handler para mensajes de texto que no son comandos ni ejercicios
    # Este handler debe estar después del de ejercicios para no interferir
    @bot.message_handler(func=lambda message: True)
    def handle_general_message(message: Message) -> None:
        # ID para enviar respuestas por Telegram
        chat_id = get_telegram_id(message)
        # ID para enviar a las APIs (Google ID si está vinculado)
        api_user_id = get_api_user_id(message)
        
        if not check_whitelist(message, bot):
            return
            
        # Si llegamos aquí, el mensaje no es un comando ni un ejercicio
        # Así que lo tratamos como una pregunta para el AI
        
        # Enviar indicador de "escribiendo..."
        bot.send_chat_action(chat_id, "typing")
        log_to_console(f"Pregunta recibida - Usuario {chat_id} (API user_id: {api_user_id}): {message.text}", "PROCESS")
        
        try:
            # Opción 1: Usar directamente la función del fitness_agent
            try:
                from fitness_agent.agent.nodes.router_node import process_message
                
                response = process_message(api_user_id, message.text)
                
                # Formatear la respuesta
                answer = f"🤖 *ENTRENADOR AI:* 🤖\n\n{response.content}\n\n*¡LIGHTWEIGHT BABY!*"
                send_message_split(bot, chat_id, answer, parse_mode="Markdown")
                
                log_to_console(f"Respuesta del AI enviada a {chat_id}", "OUTPUT")
                
            # Opción 2: Usar la API si la importación directa falla    
            except ImportError:
                log_to_console("Importación de process_message falló, usando API", "WARNING")
                url = f"{BASE_URL}/api/chatbot/send"
                
                response = requests.post(
                    url,
                    json={"user_id": api_user_id, "message": message.text},
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code == 200:
                    data = response.json()
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
            bot.send_message(
                chat_id,
                "No pude conectar con el entrenador AI. ¡Los músculos necesitan descanso a veces!",
            )
            log_to_console(f"Error en comunicación con el chatbot: {str(e)}", "ERROR")