import os
from flask import Flask, request, jsonify, render_template
import psycopg2
from datetime import datetime, timedelta
from config import DB_CONFIG
from prompts import format_for_postgres
from logic import clean_input, insert_into_db

# Configurar Flask con las rutas correctas para templates y static
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Usar siempre el ID 3892415 como usuario predeterminado
        user_id = "3892415"

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

@app.route('/logs', methods=['GET'])
def get_logs():
    # Usar siempre el ID 3892415 como usuario predeterminado
    user_id = "3892415"

    try:
        days = int(request.args.get('days', 7))
    except ValueError:
        return jsonify({"error": "El parámetro 'days' debe ser un entero."}), 400

    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Se filtra también por user_id
        query = """
            SELECT fecha, ejercicio, repeticiones, duracion
            FROM ejercicios
            WHERE fecha >= %s AND user_id = %s
            ORDER BY fecha DESC
        """
        cur.execute(query, (cutoff_str, user_id))
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    logs = []
    for row in rows:
        data = row[2] if row[2] is not None else row[3]
        logs.append({
            "fecha": row[0],
            "ejercicio": row[1],
            "data": data
        })
    return jsonify(logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)