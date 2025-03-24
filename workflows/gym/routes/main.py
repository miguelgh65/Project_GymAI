import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
from services.database import get_exercise_logs
from services.prompt_service import format_for_postgres
from utils.formatting import clean_input
from services.database import insert_into_db

# Crear blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Usar siempre el ID 3892415 como usuario predeterminado
        user_id = request.form.get('user_id', "3892415")

        raw_text = request.form.get('exercise_data')
        if not raw_text:
            return jsonify({"success": False, "message": "No se proporcionó información de ejercicios."})
        
        cleaned_text = clean_input(raw_text)
        formatted_json = format_for_postgres(cleaned_text)
        if formatted_json is None:
            return jsonify({"success": False, "message": "Error en el procesamiento del LLM."})
        
        # Se pasa user_id a la función de inserción
        success = insert_into_db(formatted_json, user_id)
        return jsonify({
            "success": success,
            "message": "Datos insertados correctamente." if success else "Error al insertar en la base de datos."
        })
    
    return render_template('index.html')

@main_bp.route('/logs', methods=['GET'])
def get_logs():
    # Obtener user_id de los parámetros o usar el valor predeterminado
    user_id = request.args.get('user_id', "3892415")

    try:
        days = int(request.args.get('days', 7))
    except ValueError:
        return jsonify({"error": "El parámetro 'days' debe ser un entero."}), 400

    logs = get_exercise_logs(user_id, days)
    if logs is None:
        return jsonify({"error": "Error al obtener los logs."}), 500
    
    return jsonify(logs)