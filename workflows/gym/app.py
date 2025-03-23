import os
from flask import Flask, request, jsonify, render_template
import psycopg2
from datetime import datetime, timedelta
import json
from config import DB_CONFIG
from prompts import format_for_postgres
from logic import clean_input, insert_into_db

# Configurar Flask con las rutas correctas para templates y static
app = Flask(__name__)

# Función auxiliar para obtener el nombre del día de la semana
def get_weekday_name(day_number):
    days = {
        1: "Lunes",
        2: "Martes",
        3: "Miércoles",
        4: "Jueves",
        5: "Viernes",
        6: "Sábado",
        7: "Domingo"
    }
    return days.get(day_number, "Desconocido")

@app.route('/', methods=['GET', 'POST'])
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

@app.route('/logs', methods=['GET'])
def get_logs():
    # Obtener user_id de los parámetros o usar el valor predeterminado
    user_id = request.args.get('user_id', "3892415")

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

# RUTAS PARA RUTINAS DE EJERCICIOS

@app.route('/rutina', methods=['GET', 'POST'])
def manage_routine():
    # Obtener user_id de los parámetros o usar el valor predeterminado
    user_id = request.args.get('user_id', "3892415")
    if request.method == 'POST':
        user_id = request.json.get('user_id', "3892415") if request.json else "3892415"
    
    # Obtener la rutina actual
    if request.method == 'GET':
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Obtener la rutina para todos los días
            cur.execute(
                "SELECT dia_semana, ejercicios FROM rutinas WHERE user_id = %s ORDER BY dia_semana",
                (user_id,)
            )
            rows = cur.fetchall()
            
            rutina = {}
            for row in rows:
                dia_semana = row[0]
                # Verificar si el valor ya es un diccionario o necesita ser parseado
                if isinstance(row[1], str):
                    ejercicios = json.loads(row[1])
                else:
                    ejercicios = row[1]
                rutina[str(dia_semana)] = ejercicios
            
            cur.close()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Rutina obtenida correctamente.",
                "rutina": rutina
            })
        except Exception as e:
            return jsonify({
                "success": False, 
                "message": f"Error al obtener la rutina: {str(e)}",
                "rutina": {}
            })
    
    # Guardar o actualizar la rutina
    elif request.method == 'POST':
        try:
            data = request.json
            if not data or 'rutina' not in data:
                return jsonify({"success": False, "message": "Datos de rutina no proporcionados."})
            
            # La rutina debe ser un diccionario donde las claves son los días (1-7) y 
            # los valores son listas de ejercicios
            rutina = data['rutina']
            
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Primero eliminar cualquier rutina existente para este usuario
            cur.execute("DELETE FROM rutinas WHERE user_id = %s", (user_id,))
            
            # Insertar la nueva rutina
            for dia, ejercicios in rutina.items():
                try:
                    dia_semana = int(dia)
                    if not 1 <= dia_semana <= 7:
                        continue
                        
                    ejercicios_json = json.dumps(ejercicios)
                    cur.execute(
                        "INSERT INTO rutinas (user_id, dia_semana, ejercicios) VALUES (%s, %s, %s::jsonb)",
                        (user_id, dia_semana, ejercicios_json)
                    )
                except ValueError:
                    # Ignorar claves que no sean números entre 1-7
                    continue
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"success": True, "message": "Rutina guardada correctamente."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Error al guardar la rutina: {str(e)}"})

@app.route('/rutina_hoy', methods=['GET'])
def get_todays_routine():
    # Obtener user_id de los parámetros o usar el valor predeterminado
    user_id = request.args.get('user_id', "3892415")
    
    try:
        # Obtener el día de la semana actual (1=Lunes, 7=Domingo)
        dia_actual = datetime.now().isoweekday()
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Obtener la rutina para el día actual
        cur.execute(
            "SELECT ejercicios FROM rutinas WHERE user_id = %s AND dia_semana = %s",
            (user_id, dia_actual)
        )
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return jsonify({
                "success": False, 
                "message": "No hay rutina definida para hoy.",
                "dia_nombre": get_weekday_name(dia_actual),
                "rutina": None
            })
        
        # Verificar si el valor ya es un diccionario o necesita ser parseado
        if isinstance(row[0], str):
            ejercicios_hoy = json.loads(row[0])
        else:
            ejercicios_hoy = row[0]
        
        # Obtener los ejercicios ya realizados hoy
        hoy = datetime.now().strftime('%Y-%m-%d')
        cur.execute(
            """
            SELECT ejercicio FROM ejercicios 
            WHERE user_id = %s AND fecha::date = %s::date
            """,
            (user_id, hoy)
        )
        ejercicios_realizados = [row[0] for row in cur.fetchall()]
        
        # Marcar los ejercicios ya realizados
        rutina_resultado = []
        for ejercicio in ejercicios_hoy:
            rutina_resultado.append({
                "ejercicio": ejercicio,
                "realizado": ejercicio in ejercicios_realizados
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Rutina para hoy obtenida correctamente.",
            "rutina": rutina_resultado,
            "dia_nombre": get_weekday_name(dia_actual)
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Error al obtener la rutina: {str(e)}",
            "dia_nombre": get_weekday_name(datetime.now().isoweekday()),
            "rutina": None
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)