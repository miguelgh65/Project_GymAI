# prompts.py
import re
import json
from config import KNOWN_EXERCISES, llm

def format_for_postgres(text: str):
    """
    Convierte el texto en JSON estructurado válido para PostgreSQL usando DeepSeek.
    """
    print("\n➡️ Texto enviado al LLM para procesamiento:")
    print(text)

    # Convertir las claves de KNOWN_EXERCISES a una cadena separada por comas
    exercise_list = ", ".join(KNOWN_EXERCISES.keys())

    # Crear el prompt para el LLM
    prompt = f"""estructura los registros de entrenamiento fisico en json valido para postgresql.

reglas:
- corrige faltas de ortografia y normaliza los nombres de los ejercicios sin acentos y en minusculas. 
por ejemplo, 'trices en polea' debe transformarse en 'triceps en polea' y 'press banca inclinado' en 'press banca inclinado'.
- asegúrate de que el ejercicio normalizado pertenezca a la siguiente lista: {exercise_list}.
- si se trata de un ejercicio de fuerza, utiliza la clave 'ejercicio' y 'series' (una lista de objetos con 'repeticiones' y 'peso').
- para ejercicios con peso corporal como dominadas, si no se especifica peso, usa "peso": 0 explícitamente.
- si es cardio, utiliza 'ejercicio' y 'duracion' (en minutos).
- devuelve unicamente json valido, sin explicaciones adicionales.

ejemplos:
entrada: "press banca inclinado 5x75, 7x70, 8x60"
salida:
[
  {{
    "ejercicio": "press banca inclinado",
    "series": [
      {{"repeticiones": 5, "peso": 75}},
      {{"repeticiones": 7, "peso": 70}},
      {{"repeticiones": 8, "peso": 60}}
    ]
  }}
]

entrada: "dominadas 5, 7, 8"
salida:
[
  {{
    "ejercicio": "dominadas",
    "series": [
      {{"repeticiones": 5, "peso": 0}},
      {{"repeticiones": 7, "peso": 0}},
      {{"repeticiones": 8, "peso": 0}}
    ]
  }}
]

entrada: "trices en polea : 12x30, 10x30, 13x22.5"
salida:
[
  {{
    "ejercicio": "triceps en polea",
    "series": [
      {{"repeticiones": 12, "peso": 30}},
      {{"repeticiones": 10, "peso": 30}},
      {{"repeticiones": 13, "peso": 22.5}}
    ]
  }}
]

entrada:
{text}
"""

    try:
        # Llamar al modelo DeepSeek
        response = llm.invoke(prompt)
        
        print("\n📌 Respuesta completa del LLM:")
        print(response.content)

        json_match = re.search(r"```json\n([\s\S]*?)\n```", response.content)
        if not json_match:
            # Intentar extraer JSON sin formato de código
            json_match = re.search(r"\[([\s\S]*?)\]", response.content)
            if json_match:
                try:
                    json_str = "[" + json_match.group(1) + "]"
                    json_parsed = json.loads(json_str)
                    json_parsed = {"registro": json_parsed}
                    print("\n✅ JSON extraído y parseado correctamente:")
                    print(json.dumps(json_parsed, indent=4, ensure_ascii=False))
                    return json_parsed
                except json.JSONDecodeError:
                    pass

        if json_match:
            try:
                json_parsed = json.loads(json_match.group(1))
                # Asegurar que siempre haya una clave "registro"
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
    except Exception as e:
        print(f"\n❌ Error en la API de DeepSeek: {e}")
        return None