import unicodedata
from typing import Any, Dict, List, Optional, Union
import re

from config import KNOWN_EXERCISES
from pydantic import BaseModel, field_validator, model_validator


def normalize_exercise_name(name: str) -> str:
    """
    Elimina acentos y convierte a minúsculas.
    
    Args:
        name (str): Nombre del ejercicio a normalizar.
        
    Returns:
        str: Nombre normalizado en minúsculas y sin acentos.
    """
    nfkd_form = unicodedata.normalize('NFKD', name)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return only_ascii.lower().strip()

def match_exercise_variant(exercise_name: str) -> str:
    """
    Busca el ejercicio en la lista de conocidos, incluyendo variantes.
    
    Args:
        exercise_name (str): Nombre normalizado del ejercicio.
        
    Returns:
        str: Nombre normalizado, posiblemente con variante reconocida.
    """
    # Si está exactamente en la lista conocida, normalizar al nombre estándar
    if exercise_name in KNOWN_EXERCISES:
        return KNOWN_EXERCISES[exercise_name]
    
    # Variantes conocidas
    variantes = [
        " en maquina", " maquina", " en máquina", " máquina",
        " con mancuernas", " mancuernas", 
        " con barra", " barra",
        " con polea", " polea",
        " asistidas", " lastradas"
    ]
    
    # Buscar la forma base del ejercicio removiendo las variantes
    for variante in variantes:
        if variante in exercise_name:
            # Quitar la variante para ver si el ejercicio base está en la lista conocida
            possible_base = exercise_name.replace(variante, "").strip()
            if possible_base in KNOWN_EXERCISES:
                # Si el ejercicio base está en la lista, mantener la variante en el nombre final
                base_normalized = KNOWN_EXERCISES[possible_base]
                return f"{base_normalized}{variante}"
    
    # Si no se encontró, devolver el nombre limpio
    return exercise_name

class Series(BaseModel):
    repeticiones: int
    peso: Optional[float] = 0.0  # Peso opcional, por defecto 0.0 para ejercicios con peso corporal
    rir: Optional[int] = None    # RIR específico para esta serie (opcional)

class Exercise(BaseModel):
    ejercicio: str
    series: Optional[List[Series]] = None
    duracion: Optional[int] = None
    comentarios: Optional[str] = None  # Comentarios opcionales del ejercicio
    rir: Optional[int] = None          # RIR general para todo el ejercicio

    @field_validator("ejercicio")
    @classmethod
    def validate_ejercicio(cls, v):
        """Validar y normalizar el nombre del ejercicio."""
        v_clean = normalize_exercise_name(v)
        return match_exercise_variant(v_clean)

    @model_validator(mode="after")
    def check_fields(self):
        """Verificar que se incluya series o duración."""
        if self.series is None and self.duracion is None:
            raise ValueError("Se debe proporcionar 'series' o 'duracion'.")
        return self

class ExerciseData(BaseModel):
    registro: Optional[List[Exercise]] = None

    def get_exercises(self) -> List[Exercise]:
        """Obtiene la lista de ejercicios, o lista vacía si no hay ninguno."""
        return self.registro or []