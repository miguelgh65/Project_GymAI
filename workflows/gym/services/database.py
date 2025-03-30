import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import datetime
import psycopg2
import traceback
from config import DB_CONFIG
from models.schemas import ExerciseData

def insert_into_db(json_data, user_id) -> bool:
    """
    Inserta los datos de ejercicios en la base de datos.
    
    Args:
        json_data (dict): Datos de ejercicios en formato JSON.
        user_id (str): ID de Google del usuario.
        
    Returns:
        bool: True si la inserción fue exitosa, False en caso contrario.
    """
    conn = None
    try:
        print("\n🔍 Recibido JSON para inserción:")
        print(json.dumps(json_data, indent=4, ensure_ascii=False))
        parsed = ExerciseData.model_validate(json_data)
        exercises = parsed.get_exercises()
        print(f"\n📌 Se han parseado {len(exercises)} ejercicios.")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        for exercise in exercises:
            nombre_ejercicio = exercise.ejercicio
            fecha_hora_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"📌 Preparando inserción para {nombre_ejercicio} en {fecha_hora_actual}")
            
            if exercise.series is not None:
                series_json = json.dumps([s.model_dump() for s in exercise.series])
                
                cur.execute(
                    """
                    INSERT INTO ejercicios 
                    (fecha, ejercicio, repeticiones, user_id) 
                    VALUES (%s, %s, %s::jsonb, %s)
                    """,
                    (fecha_hora_actual, nombre_ejercicio, series_json, user_id)
                )
            elif exercise.duracion is not None:
                cur.execute(
                    """
                    INSERT INTO ejercicios 
                    (fecha, ejercicio, duracion, user_id) 
                    VALUES (%s, %s, %s, %s)
                    """,
                    (fecha_hora_actual, nombre_ejercicio, exercise.duracion, user_id)
                )
        
        conn.commit()
        print("✅ Inserción confirmada en la BD.")
        return True
    except Exception as e:
        print(f"❌ Error al insertar en la base de datos: {e}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                print(f"Error al cerrar la conexión: {close_error}")

def get_exercise_logs(user_id, days=7):
    """
    Obtiene los logs de ejercicios de un usuario usando su ID de Google.
    
    Args:
        user_id (str): ID de Google del usuario.
        days (int): Número de días hacia atrás para obtener logs.
        
    Returns:
        list or None: Lista de logs o None si hay un error.
    """
    conn = None
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Buscar logs usando el user_id (Google ID)
        query = """
            SELECT fecha, ejercicio, repeticiones, duracion
            FROM ejercicios
            WHERE fecha >= %s AND user_id = %s
            ORDER BY fecha DESC
        """
        cur.execute(query, (cutoff_str, user_id))
        
        rows = cur.fetchall()

        logs = []
        for row in rows:
            data = row[2] if row[2] is not None else row[3]
            logs.append({
                "fecha": row[0],
                "ejercicio": row[1],
                "data": data
            })
        return logs
    except Exception as e:
        print(f"Error al obtener logs: {e}")
        traceback.print_exc()
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                print(f"Error al cerrar la conexión: {close_error}")

def save_routine(user_id, routine_data):
    """
    Guarda la rutina de un usuario usando su ID de Google.
    
    Args:
        user_id (str): ID de Google del usuario.
        routine_data (dict): Datos de la rutina.
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Primero eliminar cualquier rutina existente para este usuario
        cur.execute(
            "DELETE FROM rutinas WHERE user_id = %s", 
            (user_id,)
        )
        
        # Insertar la nueva rutina
        for dia, ejercicios in routine_data.items():
            try:
                dia_semana = int(dia)
                if not 1 <= dia_semana <= 7:
                    continue
                    
                ejercicios_json = json.dumps(ejercicios)
                
                cur.execute(
                    """
                    INSERT INTO rutinas 
                    (user_id, dia_semana, ejercicios) 
                    VALUES (%s, %s, %s::jsonb)
                    """,
                    (user_id, dia_semana, ejercicios_json)
                )
            except ValueError:
                # Ignorar claves que no sean números entre 1-7
                continue
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al guardar rutina: {e}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                print(f"Error al cerrar la conexión: {close_error}")

def get_routine(user_id):
    """
    Obtiene la rutina de un usuario usando su ID de Google.
    
    Args:
        user_id (str): ID de Google del usuario.
        
    Returns:
        dict or None: Rutina del usuario o None si hay un error.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Obtener la rutina para todos los días
        cur.execute(
            """
            SELECT dia_semana, ejercicios 
            FROM rutinas 
            WHERE user_id = %s 
            ORDER BY dia_semana
            """,
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
        
        return rutina
    
    except Exception as e:
        print(f"Error al obtener rutina: {e}")
        traceback.print_exc()
        return None
    
    finally:
        # Asegurarse de cerrar la conexión si está abierta
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                print(f"Error al cerrar la conexión: {close_error}")

def get_today_routine(user_id):
    """
    Obtiene la rutina del día actual para un usuario usando su ID de Google.
    
    Args:
        user_id (str): ID de Google del usuario.
        
    Returns:
        dict: Información de la rutina del día o mensaje de error.
    """
    conn = None
    try:
        # Obtener el día de la semana actual (1=Lunes, 7=Domingo)
        from utils.date_utils import get_weekday_name
        dia_actual = datetime.datetime.now().isoweekday()
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Obtener la rutina para el día actual
        cur.execute(
            """
            SELECT ejercicios 
            FROM rutinas 
            WHERE user_id = %s AND dia_semana = %s
            """,
            (user_id, dia_actual)
        )
        
        row = cur.fetchone()
        
        if not row:
            return {
                "success": False, 
                "message": "No hay rutina definida para hoy.",
                "dia_nombre": get_weekday_name(dia_actual),
                "rutina": None
            }
        
        # Verificar si el valor ya es un diccionario o necesita ser parseado
        if isinstance(row[0], str):
            ejercicios_hoy = json.loads(row[0])
        else:
            ejercicios_hoy = row[0]
        
        # Obtener los ejercicios ya realizados hoy
        hoy = datetime.datetime.now().strftime('%Y-%m-%d')
        
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
        
        return {
            "success": True,
            "message": "Rutina para hoy obtenida correctamente.",
            "rutina": rutina_resultado,
            "dia_nombre": get_weekday_name(dia_actual)
        }
    except Exception as e:
        print(f"Error al obtener la rutina: {e}")
        traceback.print_exc()
        return {
            "success": False, 
            "message": f"Error al obtener la rutina: {str(e)}",
            "dia_nombre": get_weekday_name(datetime.datetime.now().isoweekday()),
            "rutina": None
        }
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                print(f"Error al cerrar la conexión: {close_error}")