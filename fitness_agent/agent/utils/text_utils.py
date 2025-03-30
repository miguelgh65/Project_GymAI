# fitness_agent/agent/utils/text_utils.py
import re
import unicodedata
from typing import Optional, List

def normalize_text(text: str) -> str:
    """
    Normaliza texto eliminando acentos, convirtiendo a minúsculas y limpiando.
    
    Args:
        text: Texto a normalizar
    
    Returns:
        Texto normalizado
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Eliminar acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    
    # Eliminar caracteres especiales
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Reducir espacios múltiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_exercise_name(text: str) -> Optional[str]:
    """
    Extrae el nombre de un ejercicio de un texto.
    
    Args:
        text: Texto para extraer el nombre del ejercicio
    
    Returns:
        Nombre del ejercicio si se encuentra, None en otro caso
    """
    # Patrones para extraer nombres de ejercicios
    patterns = [
        r'(?:progreso|estadisticas|mejora)\s+de\s+(.+)',
        r'(?:sobre|acerca\s+de)\s+(.+)',
        r'^(.+?)[\s:]+',  # Captura al inicio del texto
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            # Normalizar y devolver el nombre
            return normalize_text(match.group(1).strip())
    
    return None

def tokenize_exercise_input(text: str) -> List[str]:
    """
    Divide la entrada de ejercicios en tokens individuales.
    
    Args:
        text: Texto de entrada con información de ejercicios
    
    Returns:
        Lista de tokens de ejercicios
    """
    # Dividir por comas o nuevas líneas
    tokens = re.split(r'[,\n]', text)
    
    # Limpiar y filtrar tokens
    return [normalize_text(token) for token in tokens if token.strip()]

def is_valid_exercise_input(text: str) -> bool:
    """
    Verifica si el texto parece ser una entrada válida de ejercicio.
    
    Args:
        text: Texto a verificar
    
    Returns:
        True si parece ser una entrada de ejercicio válida, False en otro caso
    """
    # Patrones que sugieren una entrada de ejercicio
    patterns = [
        r'\d+x\d+',  # Patrón como 5x75 (repeticiones x peso)
        r'\d+\s*(?:min|minutos)',  # Patrón de duración
        r'\d+\s*(?:rep|reps|repeticiones)',  # Patrón de repeticiones
    ]
    
    return any(re.search(pattern, text.lower()) for pattern in patterns)