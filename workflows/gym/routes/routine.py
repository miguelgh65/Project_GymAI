import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify, render_template
import json
from datetime import datetime
import psycopg2
from config import DB_CONFIG
from utils.date_utils import get_weekday_name

# Crear blueprint
routine_bp = Blueprint('routine', __name__)

@routine_bp.route('/rutina', methods=['GET', 'POST'])
def manage_routine():
    # Si es una solicitud simple GET y no tiene parámetros format=json, entonces es una solicitud de página HTML
    if request.method == 'GET' and request.args.get('format') != 'json':
        return render_template('rutina.html')
    
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
@routine_bp.route('/rutina_hoy', methods=['GET'])
def get_todays_routine():
    # Si es una solicitud simple GET y no tiene parámetros format=json, entonces es una solicitud de página HTML
    if request.args.get('format') != 'json':
        return render_template('rutina_hoy.html')
    
    # Obtener user_id de los parámetros o usar el valor predeterminado
    user_id = request.args.get('user_id', "3892415")
    
    try:
        # Obtener el día de la semana actual (1=Lunes, 7=Domingo)
        dia_actual = datetime.now().isoweekday()
        print(f"Día actual: {dia_actual}, Nombre: {get_weekday_name(dia_actual)}")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Verificar conexión a la base de datos
        cur.execute("SELECT 1")
        print("Conexión a la base de datos establecida correctamente")
        
        # Obtener la rutina para el día actual
        query = "SELECT ejercicios FROM rutinas WHERE user_id = %s AND dia_semana = %s"
        print(f"Ejecutando consulta: {query} con parámetros: {user_id}, {dia_actual}")
        
        cur.execute(query, (user_id, dia_actual))
        row = cur.fetchone()
        
        if not row:
            print(f"No se encontró rutina para el día {dia_actual}")
            cur.close()
            conn.close()
            return jsonify({
                "success": False, 
                "message": "No hay rutina definida para hoy.",
                "dia_nombre": get_weekday_name(dia_actual),
                "rutina": []  # Enviar array vacío en lugar de None
            })
        
        print(f"Rutina encontrada para el día {dia_actual}")
        
        # Verificar si el valor ya es un diccionario o necesita ser parseado
        if isinstance(row[0], str):
            ejercicios_hoy = json.loads(row[0])
        else:
            ejercicios_hoy = row[0]
        
        print(f"Ejercicios para hoy: {ejercicios_hoy}")
        
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
        print(f"Ejercicios realizados hoy: {ejercicios_realizados}")
        
        # Marcar los ejercicios ya realizados
        rutina_resultado = []
        for ejercicio in ejercicios_hoy:
            rutina_resultado.append({
                "ejercicio": ejercicio,
                "realizado": ejercicio in ejercicios_realizados
            })
        
        cur.close()
        conn.close()
        
        result = {
            "success": True,
            "message": "Rutina para hoy obtenida correctamente.",
            "rutina": rutina_resultado,
            "dia_nombre": get_weekday_name(dia_actual)
        }
        print(f"Respuesta final: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error al obtener la rutina del día: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False, 
            "message": f"Error al obtener la rutina: {str(e)}",
            "dia_nombre": get_weekday_name(datetime.now().isoweekday()),
            "rutina": []  # Enviar array vacío en lugar de None
        })