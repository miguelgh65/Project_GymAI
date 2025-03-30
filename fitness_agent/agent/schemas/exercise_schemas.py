from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Union, Dict, Any
import unicodedata
import re
from enum import Enum

# Parte 1: Definición de tipos de ejercicios y normalización
class ExerciseType(str, Enum):
    """Tipos de ejercicios soportados por el sistema."""
    # Cardio
    RUNNING = "correr"
    SWIMMING = "natacion"
    CYCLING = "ciclismo"
    ELLIPTICAL = "eliptica"
    ROWING = "remo"
    
    # Pecho
    BENCH_PRESS = "press banca"
    INCLINE_BENCH_PRESS = "press banca inclinado"
    DECLINE_BENCH_PRESS = "press banca declinado"
    CHEST_FLY = "contractor pecho"
    PUSH_UP = "flexiones"
    
    # Espalda
    PULL_UP = "dominadas"
    LAT_PULLDOWN = "jalon al pecho"
    NARROW_GRIP_PULLDOWN = "jalon agarre estrecho"
    MACHINE_ROW = "remo en maquina"
    NARROW_GRIP_ROW = "remo agarre estrecho"
    
    # Hombros
    MILITARY_PRESS = "press militar"
    FRONT_RAISE = "elevaciones frontales"
    LATERAL_RAISE = "elevaciones laterales"
    REAR_DELT_FLY = "contractor posterior"
    
    # Brazos
    BICEP_CURL = "curl de biceps"
    HAMMER_CURL = "curl martillo"
    TRICEP_PUSHDOWN = "triceps en polea"
    TRICEP_EXTENSION = "extension de triceps"
    
    # Piernas
    SQUAT = "sentadilla"
    LEG_PRESS = "prensa"
    DEADLIFT = "peso muerto"
    LEG_EXTENSION = "extension de piernas"
    LEG_CURL = "curl de piernas"
    CALF_RAISE = "elevacion de gemelos"
    LUNGE = "zancada"
    
    # Core
    CRUNCH = "abdominales"
    PLANK = "plancha"
    RUSSIAN_TWIST = "giro ruso"
    LEG_RAISE = "elevacion de piernas"

# Diccionario de normalización
# Mapea variantes y entradas mal escritas a los valores del enum
EXERCISE_MAPPING: Dict[str, ExerciseType] = {
    # Cardio
    "correr": ExerciseType.RUNNING,
    "running": ExerciseType.RUNNING,
    "run": ExerciseType.RUNNING,
    "carrera": ExerciseType.RUNNING,
    "trote": ExerciseType.RUNNING,
    
    "nadar": ExerciseType.SWIMMING,
    "natacion": ExerciseType.SWIMMING,
    "natación": ExerciseType.SWIMMING,
    "piscina": ExerciseType.SWIMMING,
    "swimming": ExerciseType.SWIMMING,
    
    # Pecho
    "press banca": ExerciseType.BENCH_PRESS,
    "press de banca": ExerciseType.BENCH_PRESS,
    "bench press": ExerciseType.BENCH_PRESS,
    "pres banca": ExerciseType.BENCH_PRESS,
    "press banco": ExerciseType.BENCH_PRESS,
    
    "press banca inclinado": ExerciseType.INCLINE_BENCH_PRESS,
    "press inclinado": ExerciseType.INCLINE_BENCH_PRESS,
    "incline bench": ExerciseType.INCLINE_BENCH_PRESS,
    "incline press": ExerciseType.INCLINE_BENCH_PRESS,
    
    "contractor pecho": ExerciseType.CHEST_FLY,
    "aperturas": ExerciseType.CHEST_FLY,
    "chest fly": ExerciseType.CHEST_FLY,
    "pec deck": ExerciseType.CHEST_FLY,
    "cable fly": ExerciseType.CHEST_FLY,
    
    # Espalda
    "dominadas": ExerciseType.PULL_UP,
    "dominada": ExerciseType.PULL_UP,
    "pull up": ExerciseType.PULL_UP,
    "pull-up": ExerciseType.PULL_UP,
    "chin up": ExerciseType.PULL_UP,
    
    "jalon al pecho": ExerciseType.LAT_PULLDOWN,
    "jalon": ExerciseType.LAT_PULLDOWN,
    "pulldown": ExerciseType.LAT_PULLDOWN,
    "lat pulldown": ExerciseType.LAT_PULLDOWN,
    "polea al pecho": ExerciseType.LAT_PULLDOWN,
    
    "jalon agarre estrecho": ExerciseType.NARROW_GRIP_PULLDOWN,
    "jalon estrecho": ExerciseType.NARROW_GRIP_PULLDOWN,
    "close grip pulldown": ExerciseType.NARROW_GRIP_PULLDOWN,
    
    "remo en maquina": ExerciseType.MACHINE_ROW,
    "remo": ExerciseType.MACHINE_ROW,
    "machine row": ExerciseType.MACHINE_ROW,
    "seated row": ExerciseType.MACHINE_ROW,
    
    # Hombros
    "press militar": ExerciseType.MILITARY_PRESS,
    "military press": ExerciseType.MILITARY_PRESS,
    "press hombro": ExerciseType.MILITARY_PRESS,
    "shoulder press": ExerciseType.MILITARY_PRESS,
    "press de hombros": ExerciseType.MILITARY_PRESS,
    
    "elevaciones frontales": ExerciseType.FRONT_RAISE,
    "front raise": ExerciseType.FRONT_RAISE,
    
    # Brazos
    "curl de biceps": ExerciseType.BICEP_CURL,
    "curl biceps": ExerciseType.BICEP_CURL,
    "biceps": ExerciseType.BICEP_CURL,
    "bicep curls": ExerciseType.BICEP_CURL,
    "maquina de biceps": ExerciseType.BICEP_CURL,
    
    "triceps en polea": ExerciseType.TRICEP_PUSHDOWN,
    "pushdown": ExerciseType.TRICEP_PUSHDOWN,
    "triceps pushdown": ExerciseType.TRICEP_PUSHDOWN,
    "extension de triceps": ExerciseType.TRICEP_EXTENSION,
    "triceps": ExerciseType.TRICEP_PUSHDOWN,
    
    # Piernas
    "sentadilla": ExerciseType.SQUAT,
    "squat": ExerciseType.SQUAT,
    "sentadillas": ExerciseType.SQUAT,
    
    "prensa": ExerciseType.LEG_PRESS,
    "leg press": ExerciseType.LEG_PRESS,
    "prensa de piernas": ExerciseType.LEG_PRESS,
    
    "peso muerto": ExerciseType.DEADLIFT,
    "deadlift": ExerciseType.DEADLIFT,
}

def normalize_text(text: str) -> str:
    """
    Normaliza el texto eliminando acentos, convirtiéndolo a minúsculas
    y eliminando caracteres especiales.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Eliminar acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    
    # Eliminar caracteres especiales excepto espacios
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Reducir múltiples espacios a uno solo
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def get_normalized_exercise(exercise_name: str) -> Optional[ExerciseType]:
    """
    Obtiene el tipo de ejercicio normalizado a partir de un nombre.
    
    Args:
        exercise_name: Nombre del ejercicio a normalizar
        
    Returns:
        ExerciseType o None si no se encuentra
    """
    # Normalizar el nombre
    normalized_name = normalize_text(exercise_name)
    
    # Buscar coincidencia exacta
    if normalized_name in EXERCISE_MAPPING:
        return EXERCISE_MAPPING[normalized_name]
    
    # Buscar coincidencia parcial
    for key, value in EXERCISE_MAPPING.items():
        if key in normalized_name or normalized_name in key:
            return value
    
    # No se encontró coincidencia
    return None

# Parte 2: Esquemas de datos para ejercicios
def normalize_exercise_name(name: str) -> str:
    """Elimina acentos y convierte a minúsculas."""
    nfkd_form = unicodedata.normalize('NFKD', name)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return only_ascii.lower().strip()

class Series(BaseModel):
    """Representa una serie de un ejercicio con repeticiones y peso."""
    repeticiones: int
    peso: Optional[float] = 0.0  # Ahora el peso es opcional, por defecto 0.0 para ejercicios con peso corporal

class Exercise(BaseModel):
    """Representa un ejercicio con series o duración."""
    ejercicio: str
    series: Optional[List[Series]] = None
    duracion: Optional[int] = None

    @field_validator("ejercicio")
    @classmethod
    def validate_ejercicio(cls, v):
        """Valida y normaliza el nombre del ejercicio."""
        # Intentar normalizar usando el sistema de tipos
        normalized = get_normalized_exercise(v)
        if normalized:
            return normalized.value
        
        # Fallback a normalización simple
        v_clean = normalize_exercise_name(v)
        return v_clean

    @model_validator(mode="after")
    def check_fields(self):
        """Verifica que se ha proporcionado series o duración."""
        if self.series is None and self.duracion is None:
            raise ValueError("Se debe proporcionar 'series' o 'duracion'.")
        return self

class ExerciseData(BaseModel):
    """Contiene una lista de ejercicios."""
    registro: Optional[List[Exercise]] = None

    def get_exercises(self) -> List[Exercise]:
        """Obtiene la lista de ejercicios."""
        return self.registro or []