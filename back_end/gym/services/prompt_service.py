# back_end/gym/services/prompt_service.py
import json
import re
import logging
from config import KNOWN_EXERCISES, llm

logger = logging.getLogger(__name__)

def generate_exercise_prompt(text):
    """
    Genera el prompt para el LLM con instrucciones y ejemplos.
    
    Args:
        text (str): Texto de entrada con información de ejercicios.
        
    Returns:
        str: Prompt completo con instrucciones estructuradas.
    """
    prompt = f"""
<task>Estructurar registros de entrenamiento físico en JSON válido para PostgreSQL</task>

<input>
{text}
</input>

<instructions>
Analiza el texto de entrada y conviértelo en JSON válido para almacenar registros de entrenamiento. El JSON debe seguir estas reglas:

1. Normaliza los nombres de ejercicios:
   - Convierte a minúsculas
   - Elimina acentos
   - Corrige errores ortográficos
   - Mantén variantes como "en máquina", "con mancuernas", "con barra" junto al nombre del ejercicio

2. Para ejercicios de fuerza:
   - Incluye campo "ejercicio" con el nombre normalizado
   - Incluye "series" como lista de objetos con "repeticiones", "peso" y opcionalmente "rir"
   - Para ejercicios con peso corporal, usa "peso": 0 explícitamente
   - Si no se especifica el peso, asume un valor razonable según el tipo de ejercicio (por ejemplo, 0 para dominadas, 20 para press, etc.)
   - Si el formato es "NxNxN" (por ejemplo, "10x10x10"), interpreta cada número como repeticiones de series separadas con el mismo peso
   - Si el formato es "NxPeso" (por ejemplo, "10x50"), interpreta N como repeticiones y Peso como el peso

3. Para ejercicio de cardio:
   - Incluye campo "ejercicio" con el nombre normalizado
   - Usa "duracion" en minutos (número entero)

4. Para campos adicionales:
   - Si hay un RIR general, inclúyelo como campo "rir" al mismo nivel que "ejercicio"
   - Si hay un RIR específico para la última serie, añádelo en esa serie
   - Si hay comentarios o notas, inclúyelos como campo "comentarios"

5. Formato de salida:
   - Devuelve SOLO el JSON sin explicaciones adicionales ni markdown
   - El JSON debe ser una lista de objetos, cada uno representando un ejercicio
</instructions>

<examples>
<example>
<input>press banca inclinado 5x75, 7x70, 8x60 rir 2 comentario: me costó el último</input>
<output>
[
  {{
    "ejercicio": "press banca inclinado",
    "series": [
      {{"repeticiones": 5, "peso": 75, "rir": null}},
      {{"repeticiones": 7, "peso": 70, "rir": null}},
      {{"repeticiones": 8, "peso": 60, "rir": 2}}
    ],
    "rir": 2,
    "comentarios": "me costó el último"
  }}
]
</output>
</example>

<example>
<input>press banca 10x10x10x10x10 rir 3 muy cansado</input>
<output>
[
  {{
    "ejercicio": "press banca",
    "series": [
      {{"repeticiones": 10, "peso": 50, "rir": null}},
      {{"repeticiones": 10, "peso": 50, "rir": null}},
      {{"repeticiones": 10, "peso": 50, "rir": null}},
      {{"repeticiones": 10, "peso": 50, "rir": null}},
      {{"repeticiones": 10, "peso": 50, "rir": null}}
    ],
    "rir": 3,
    "comentarios": "muy cansado"
  }}
]
</output>
</example>

<example>
<input>dominadas 5, 7, 8 rir 1 me duelen los brazos</input>
<output>
[
  {{
    "ejercicio": "dominadas",
    "series": [
      {{"repeticiones": 5, "peso": 0, "rir": null}},
      {{"repeticiones": 7, "peso": 0, "rir": null}},
      {{"repeticiones": 8, "peso": 0, "rir": null}}
    ],
    "rir": 1,
    "comentarios": "me duelen los brazos"
  }}
]
</output>
</example>

<example>
<input>trices en polea : 12x30, 10x30, 13x22.5 notas: aumentar peso próxima vez</input>
<output>
[
  {{
    "ejercicio": "triceps en polea",
    "series": [
      {{"repeticiones": 12, "peso": 30, "rir": null}},
      {{"repeticiones": 10, "peso": 30, "rir": null}},
      {{"repeticiones": 13, "peso": 22.5, "rir": null}}
    ],
    "comentarios": "aumentar peso próxima vez"
  }}
]
</output>
</example>

<example>
<input>press militar en maquina 3x10 20 kg rir 2 muy cansado</input>
<output>
[
  {{
    "ejercicio": "press militar en maquina",
    "series": [
      {{"repeticiones": 10, "peso": 20, "rir": null}},
      {{"repeticiones": 10, "peso": 20, "rir": null}},
      {{"repeticiones": 10, "peso": 20, "rir": null}}
    ],
    "rir": 2,
    "comentarios": "muy cansado"
  }}
]
</output>
</example>

<example>
<input>correr 30 min cansado al final</input>
<output>
[
  {{
    "ejercicio": "correr",
    "duracion": 30,
    "comentarios": "cansado al final"
  }}
]
</output>
</example>
</examples>

<output_format>
JSON estructurado sin markdown, bloques de código ni explicaciones adicionales.
</output_format>
"""
    return prompt

def extract_json_from_llm_response(content):
    """
    Extrae contenido JSON de la respuesta del LLM.
    
    Args:
        content (str): Respuesta completa del LLM.
        
    Returns:
        str or None: Cadena JSON si se encuentra, None en caso contrario.
    """
    # 1. Intentar extraer de ```json ... ```
    json_match_markdown = re.search(r"```json\n([\s\S]*?)\n```", content)
    if json_match_markdown:
        json_str = json_match_markdown.group(1).strip()
        logger.debug("JSON extraído de bloque Markdown")
        return json_str
    
    # 2. Buscar el primer '[' o '{' que parezca iniciar un JSON
    # y el último ']' o '}' que parezca terminarlo
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
        logger.debug("JSON extraído por búsqueda de delimitadores")
        return json_str
    
    # 3. Como último recurso, usar todo el contenido si parece JSON simple
    if (content.startswith('[') and content.endswith(']')) or \
       (content.startswith('{') and content.endswith('}')):
        logger.debug("Usando contenido completo como posible JSON")
        return content
    
    # No se encontró JSON
    return None

def parse_json_to_exercise_data(json_str):
    """
    Parsea la cadena JSON a un diccionario con la estructura correcta para ExerciseData.
    
    Args:
        json_str (str): Cadena JSON a parsear.
        
    Returns:
        dict or None: Diccionario con la estructura correcta o None si hay error.
    """
    try:
        json_parsed = json.loads(json_str)
        
        # Asegurar que siempre se devuelva un dict con la clave 'registro'
        if isinstance(json_parsed, list):
            return {"registro": json_parsed}
        elif isinstance(json_parsed, dict) and 'registro' in json_parsed:
            return json_parsed
        elif isinstance(json_parsed, dict):
            return {"registro": [json_parsed]}
        else:
            logger.error("El JSON parseado no es una lista ni un diccionario esperado")
            return None
    except json.JSONDecodeError as e:
        logger.error(f"Error al convertir la cadena en JSON: {e}")
        return None

def format_for_postgres(text: str):
    """
    Convierte el texto en JSON estructurado válido para PostgreSQL usando DeepSeek.
    Maneja JSON con o sin bloques ```json```.

    Args:
        text (str): Texto de entrada con información de ejercicios.

    Returns:
        dict or None: JSON estructurado con la clave 'registro' o None si hay un error.
    """
    logger.info("➡️ Procesando texto para extracción de ejercicios")
    print("\n➡️ Texto enviado al LLM para procesamiento:")
    print(text)

    try:
        # 1. Generar el prompt
        prompt = generate_exercise_prompt(text)
        
        # 2. Enviar al LLM
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        print("\n📌 Respuesta completa del LLM:")
        print(content)
        
        # 3. Extraer JSON de la respuesta
        json_str = extract_json_from_llm_response(content)
        
        if not json_str:
            logger.error("No se encontró una cadena JSON válida en la respuesta del LLM")
            return None
        
        # 4. Parsear y validar el JSON
        result_dict = parse_json_to_exercise_data(json_str)
        
        if result_dict:
            print("\n✅ JSON extraído y parseado correctamente:")
            print(json.dumps(result_dict, indent=4, ensure_ascii=False))
            return result_dict
        
        return None

    except Exception as e:
        logger.exception(f"Error general en format_for_postgres: {e}")
        return None