# database.py - Archivo principal que expone todas las funciones

# Importar funciones para hacerlas disponibles a través de este módulo
from .database_exercise import insert_into_db, get_exercise_logs
from .database_routine import save_routine, get_routine
from .database_routine_utils import get_today_routine, reset_today_routine_status

# Cualquier configuración adicional o inicialización global puede ir aquí

# Nota: Este archivo permite importar directamente desde `database` manteniendo
# compatibilidad con código existente.