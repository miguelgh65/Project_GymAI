# logic.py
import re
import json
import datetime
import psycopg2
from config import DB_CONFIG
from schemas import ExerciseData

def clean_input(text: str) -> str:
    return re.sub(r'\[\d+/\d+, \d+:\d+\] .*?: ', '', text).strip()

def insert_into_db(json_data, user_id) -> bool:
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
                    "INSERT INTO ejercicios (fecha, ejercicio, repeticiones, user_id) VALUES (%s, %s, %s::jsonb, %s)",
                    (fecha_hora_actual, nombre_ejercicio, series_json, user_id)
                )
            elif exercise.duracion is not None:
                cur.execute(
                    "INSERT INTO ejercicios (fecha, ejercicio, duracion, user_id) VALUES (%s, %s, %s, %s)",
                    (fecha_hora_actual, nombre_ejercicio, exercise.duracion, user_id)
                )
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Inserción confirmada en la BD.")
        return True
    except Exception as e:
        print(f"❌ Error al insertar en la base de datos: {e}")
        return False