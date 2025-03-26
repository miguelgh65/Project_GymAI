# Archivo: workflows/gym/routes/chatbot.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify, render_template
from services.langgraph_agent.agent import process_message

# Crear blueprint
chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot', methods=['GET'])
def chatbot_page():
    """Página principal del chatbot."""
    user_id = request.args.get('user_id', "3892415")
    return render_template('chatbot.html', user_id=user_id)

@chatbot_bp.route('/api/chatbot/send', methods=['POST'])
def chatbot_send():
    """API para enviar mensajes al chatbot."""
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"success": False, "error": "No se proporcionó un mensaje"}), 400
    
    user_id = data.get('user_id', "3892415")
    message = data.get('message', '')
    
    # Procesar el mensaje con el agente
    responses = process_message(user_id, message)
    
    return jsonify({
        "success": True,
        "responses": responses
    })

@chatbot_bp.route('/api/chatbot/history', methods=['GET'])
def chatbot_history():
    """API para obtener el historial de conversación."""
    user_id = request.args.get('user_id', "3892415")
    
    # Aquí podrías implementar la obtención del historial desde la base de datos
    # Por ahora, retornamos un historial vacío
    return jsonify({
        "success": True,
        "history": []
    })