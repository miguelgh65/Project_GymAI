# models/schemas.py
import unicodedata
from typing import Any, Dict, List, Optional, Union

from config import KNOWN_EXERCISES
from pydantic import BaseModel, field_validator, model_validator


def normalize_exercise_name(name: str) -> str:
    """Elimina acentos y convierte a minúsculas."""
    nfkd_form = unicodedata.normalize('NFKD', name)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return only_ascii.lower().strip()

class Series(BaseModel):
    repeticiones: int
    peso: Optional[float] = 0.0  # Ahora el peso es opcional, por defecto 0.0 para ejercicios con peso corporal

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