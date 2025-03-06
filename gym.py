from flask import Flask, request, jsonify, render_template
import requests
import psycopg2
import re
import datetime
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional

app = Flask(__name__)

# Configuración de la base de datos
DB_CONFIG = {
    'dbname': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'host': os.getenv("DB_HOST"),
    'port': os.getenv("DB_PORT")
}

# Configuración del LLM con DeepSeek
llm = ChatDeepSeek(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("LLM_API_KEY"),
    temperature=float(os.getenv("LLM_TEMPERATURE")),
    max_tokens=int(os.getenv("LLM_MAX_TOKENS")),
    timeout=int(os.getenv("LLM_TIMEOUT")),
    max_retries=int(os.getenv("LLM_MAX_RETRIES"))
)

# ✅ Lista de ejercicios conocidos, asegurando que variantes sean reconocidas
KNOWN_EXERCISES = {
    "natacion": "Natación",
    "piscina": "Piscina",
    "correr": "Correr",
    "dominadas": "Dominadas",
    "jalón agarre estrecho": "Jalón agarre estrecho",
    "máquina dominadas": "Máquina dominadas",
    "maquina dominadas": "Máquina dominadas",  # Permite ambas variantes
    "remo en máquina": "Remo en máquina",
    "remo agarre estrecho": "Remo agarre estrecho",
    "press banca": "Press banca",
    "contractor pecho": "Contractor pecho",
    "press militar": "Press militar",
    "triceps en polea": "Triceps en polea",
    "elevaciones frontales": "Elevaciones frontales",
    "máquina de bíceps": "Máquina de bíceps",
    "biceps": "Bíceps"
}

def clean_input(text):
    """Limpia el texto recibido eliminando timestamps u otros artefactos."""
    return re.sub(r'\[\d+/\d+, \d+:\d+\] .*?: ', '', text).strip()

def format_for_postgres(text):
    """Convierte el texto en JSON estructurado válido para PostgreSQL usando DeepSeek."""
    print("\n➡️ Texto enviado al LLM para procesamiento:")
    print(text)

    prompt = ChatPromptTemplate.from_template(
        "Estructura los registros de entrenamiento físico en JSON válido.\n\n"
        "Reglas:\n"
        "- Si es un ejercicio de fuerza, usa 'ejercicio' y 'series' (lista de objetos con 'repeticiones' y 'peso').\n"
        "- Si es cardio, usa 'ejercicio' y 'duracion' en minutos.\n"
        "- Devuelve solo JSON válido sin explicaciones.\n\n"
        "Entrada:\n{input_text}"
    )

    formatted_prompt = prompt.format(input_text=text)

    try:
        response = llm.invoke(formatted_prompt)
        print("\n📌 Respuesta completa del LLM:")
        print(response.content)

        json_match = re.search(r"```json\n([\s\S]*?)\n```", response.content)

        if json_match:
            try:
                json_parsed = json.loads(json_match.group(1))
                
                # 🔥 Asegurar que siempre haya una clave "registro"
                if isinstance(json_parsed, list):
                    json_parsed = {"registro": json_parsed}

                print("\n✅ JSON extraído y parseado correctamente:")
                print(json.dumps(json_parsed, indent=4, ensure_ascii=False))
                return json_parsed
            except json.JSONDecodeError:
                print("\n❌ Error al convertir la respuesta en JSON.")
                return None
        else:
            print("\n❌ No se encontró JSON en la respuesta del LLM.")
            return None
    except requests.Timeout:
        print("\n❌ Timeout en DeepSeek. La API tardó demasiado en responder.")
        return None
    except Exception as e:
        print(f"\n❌ Error en la API de DeepSeek: {e}")
        return None

# ✅ Función para normalizar nombres de ejercicios
def normalize_exercise_name(exercise_name):
    """Normaliza nombres de ejercicios eliminando espacios extra y convirtiendo a minúsculas."""
    return exercise_name.lower().strip()

# ✅ Pydantic Models con validación mejorada
class Series(BaseModel):
    repeticiones: int
    peso: float

class Exercise(BaseModel):
    ejercicio: str
    series: Optional[List[Series]] = None
    duracion: Optional[int] = None

    @field_validator("ejercicio")
    @classmethod
    def validate_ejercicio(cls, v):
        v_clean = normalize_exercise_name(v)
        if v_clean in KNOWN_EXERCISES:
            return KNOWN_EXERCISES[v_clean]
        raise ValueError(f"Ejercicio desconocido: {v}")

    @model_validator(mode="after")
    def check_fields(self):
        if self.series is None and self.duracion is None:
            raise ValueError("Se debe proporcionar 'series' o 'duracion'.")
        return self

class ExerciseData(BaseModel):
    registro: Optional[List[Exercise]] = None

    def get_exercises(self) -> List[Exercise]:
        return self.registro or []

def insert_into_db(json_data):
    """Inserta los datos en PostgreSQL con validación y logs detallados."""
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
                    "INSERT INTO ejercicios (fecha, ejercicio, repeticiones) VALUES (%s, %s, %s::jsonb)",
                    (fecha_hora_actual, nombre_ejercicio, series_json)
                )
            elif exercise.duracion is not None:
                cur.execute(
                    "INSERT INTO ejercicios (fecha, ejercicio, duracion) VALUES (%s, %s, %s)",
                    (fecha_hora_actual, nombre_ejercicio, exercise.duracion)
                )

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Inserción confirmada en la BD.")
        return True

    except Exception as e:
        print(f"❌ Error al insertar en la base de datos: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw_text = request.form.get('exercise_data')
        print("\n📥 Texto recibido desde el frontend:")
        print(raw_text)

        cleaned_text = clean_input(raw_text)
        formatted_json = format_for_postgres(cleaned_text)

        if formatted_json:
            success = insert_into_db(formatted_json)
            return jsonify({"success": success, "message": "Datos insertados correctamente" if success else "Error al insertar"})

        return jsonify({"success": False, "message": "Error en el formateo de datos"})
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
