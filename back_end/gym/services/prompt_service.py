# En back_end/gym/services/prompt_service.py
import json
import re
import logging # <-- Asegúrate de importar logging si quieres usar logger
from config import KNOWN_EXERCISES, llm

# logger = logging.getLogger(__name__) # <-- Opcional: configurar logger

def format_for_postgres(text: str):
    """
    Convierte el texto en JSON estructurado válido para PostgreSQL usando DeepSeek.
    Maneja JSON con o sin bloques ```json```.

    Args:
        text (str): Texto de entrada con información de ejercicios.

    Returns:
        dict or None: JSON estructurado con la clave 'registro' o None si hay un error.
    """
    print("\n➡️ Texto enviado al LLM para procesamiento:")
    print(text)
    # logger.info(f"Texto enviado al LLM: {text}") # Alternativa con logger

    exercise_list = ", ".join(KNOWN_EXERCISES.keys())
    prompt = f"""estructura los registros de entrenamiento fisico en json valido para postgresql.

reglas:
- corrige faltas de ortografia y normaliza los nombres de los ejercicios sin acentos y en minusculas.
por ejemplo, 'trices en polea' debe transformarse en 'triceps en polea' y 'press banca inclinado' en 'press banca inclinado'.
- asegúrate de que el ejercicio normalizado pertenezca a la siguiente lista: {exercise_list}.
- si se trata de un ejercicio de fuerza, utiliza la clave 'ejercicio' y 'series' (una lista de objetos con 'repeticiones' y 'peso').
- para ejercicios con peso corporal como dominadas, si no se especifica peso, usa "peso": 0 explícitamente.
- si es cardio, utiliza 'ejercicio' y 'duracion' (en minutos).
- devuelve unicamente json valido, sin explicaciones adicionales ni markdown ```json ```. SOLO el JSON.

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

salida JSON:
""" # <-- Ligeramente ajustado el final del prompt

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        print("\n📌 Respuesta completa del LLM:")
        print(content)
        # logger.info(f"Respuesta LLM: {content}")

        json_str = None
        # 1. Intentar extraer de ```json ... ```
        json_match_markdown = re.search(r"```json\n([\s\S]*?)\n```", content)
        if json_match_markdown:
            json_str = json_match_markdown.group(1).strip()
            print("DEBUG: JSON extraído de bloque Markdown.")
            # logger.debug("JSON extraído de bloque Markdown.")
        else:
            # 2. Si no, intentar encontrar el primer '[' o '{' que parezca iniciar un JSON
            #    y el último ']' o '}' que parezca terminarlo.
            start_index = -1
            end_index = -1
            # Buscar el primer '[' o '{'
            for i, char in enumerate(content):
                if char == '[' or char == '{':
                    start_index = i
                    break
            # Buscar el último ']' o '}'
            for i in range(len(content) - 1, -1, -1):
                if content[i] == ']' or content[i] == '}':
                    end_index = i + 1
                    break

            if start_index != -1 and end_index != -1 and start_index < end_index:
                 json_str = content[start_index:end_index].strip()
                 print("DEBUG: JSON extraído por búsqueda de delimitadores [/{ ... }/].")
                 # logger.debug("JSON extraído por búsqueda de delimitadores.")
            else:
                 # 3. Como último recurso, usar todo el contenido si parece JSON simple
                 if (content.startswith('[') and content.endswith(']')) or \
                    (content.startswith('{') and content.endswith('}')):
                      json_str = content
                      print("DEBUG: Usando contenido completo como posible JSON.")
                      # logger.debug("Usando contenido completo como posible JSON.")

        # Si pudimos extraer una cadena JSON, intentar parsearla
        if json_str:
            try:
                json_parsed = json.loads(json_str)
                # Asegurar que siempre se devuelva un dict con la clave 'registro'
                if isinstance(json_parsed, list):
                    result_dict = {"registro": json_parsed}
                elif isinstance(json_parsed, dict) and 'registro' in json_parsed:
                    # Si ya tiene 'registro', usarlo directamente (menos probable con el prompt actual)
                    result_dict = json_parsed
                elif isinstance(json_parsed, dict):
                     # Si es un diccionario pero no tiene 'registro', envolverlo
                     result_dict = {"registro": [json_parsed]}
                else:
                    # Tipo inesperado
                    print("\n❌ Error: El JSON parseado no es una lista ni un diccionario esperado.")
                    # logger.error("El JSON parseado no es una lista ni un diccionario esperado.")
                    return None

                print("\n✅ JSON extraído y parseado correctamente:")
                print(json.dumps(result_dict, indent=4, ensure_ascii=False))
                # logger.info("JSON parseado correctamente.")
                return result_dict
            except json.JSONDecodeError as e:
                print(f"\n❌ Error al convertir la cadena extraída en JSON: {e}")
                print(f"Cadena JSON intentada: {json_str}")
                # logger.error(f"Error al convertir la cadena extraída en JSON: {e}. Cadena: {json_str}")
                return None
        else:
            print("\n❌ No se encontró una cadena JSON válida en la respuesta del LLM.")
            # logger.error("No se encontró JSON válido en la respuesta LLM.")
            return None

    except Exception as e:
        print(f"\n❌ Error general en format_for_postgres (llamada a API o procesamiento): {e}")
        # logger.exception("Error general en format_for_postgres")
        return None