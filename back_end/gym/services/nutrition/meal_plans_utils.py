# back_end/gym/services/nutrition/meal_plans_utils.py
import logging
import decimal
import datetime
from typing import Dict, Any, Optional, Union

# Configurar logger
logger = logging.getLogger(__name__)

# Mapeo bidireccional entre nombres de días y números
DAY_NAME_TO_NUMBER = {
    'Lunes': 1, 
    'Martes': 2, 
    'Miércoles': 3, 
    'Jueves': 4, 
    'Viernes': 5, 
    'Sábado': 6, 
    'Domingo': 7
}

DAY_NUMBER_TO_NAME = {
    1: 'Lunes',
    2: 'Martes',
    3: 'Miércoles',
    4: 'Jueves',
    5: 'Viernes',
    6: 'Sábado',
    7: 'Domingo'
}

def day_name_to_number(day_name: str) -> int:
    """Convierte nombre de día en español a número (1-7, lunes-domingo)"""
    # Devolver el número correspondiente o 1 (lunes) como valor por defecto
    return DAY_NAME_TO_NUMBER.get(day_name, 1)

def day_number_to_name(day_number: int) -> str:
    """Convierte número (1-7) a nombre de día en español"""
    # Devolver el nombre correspondiente o 'Lunes' como valor por defecto
    return DAY_NUMBER_TO_NAME.get(day_number, 'Lunes')

def format_plan_result(row: tuple) -> Dict[str, Any]:
    """Formatea una fila de resultado de la BD a un diccionario de plan."""
    meal_plan = {
        "id": row[0], 
        "user_id": row[1], 
        "plan_name": row[2],
        "start_date": row[3].isoformat() if isinstance(row[3], datetime.date) else row[3],
        "end_date": row[4].isoformat() if isinstance(row[4], datetime.date) else row[4],
        "description": row[5], 
        "is_active": row[6],
        "target_calories": row[7],
        "target_protein_g": float(row[8]) if isinstance(row[8], decimal.Decimal) else row[8],
        "target_carbs_g": float(row[9]) if isinstance(row[9], decimal.Decimal) else row[9],
        "target_fat_g": float(row[10]) if isinstance(row[10], decimal.Decimal) else row[10],
        "goal": row[11],
        "created_at": row[12].isoformat() if isinstance(row[12], datetime.datetime) else row[12],
        "updated_at": row[13].isoformat() if isinstance(row[13], datetime.datetime) else row[13]
    }
    return meal_plan

def format_meal_plan_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formatea un item de plan de comida para respuesta API.
    Convierte day_of_week de número a texto si es necesario.
    """
    # Copia para no modificar el original
    formatted_item = item.copy()
    
    # Convertir day_of_week de número a texto si es un número
    if 'day_of_week' in formatted_item and isinstance(formatted_item['day_of_week'], int):
        formatted_item['day_of_week'] = day_number_to_name(formatted_item['day_of_week'])
    
    # Convertir decimales a float para JSON
    for decimal_field in ['calories', 'protein_g', 'carbohydrates_g', 'fat_g', 'quantity']:
        if decimal_field in formatted_item and isinstance(formatted_item[decimal_field], decimal.Decimal):
            formatted_item[decimal_field] = float(formatted_item[decimal_field])
    
    # Convertir fechas a ISO
    for date_field in ['plan_date', 'created_at', 'updated_at']:
        if date_field in formatted_item:
            if isinstance(formatted_item[date_field], datetime.date):
                formatted_item[date_field] = formatted_item[date_field].isoformat()
    
    return formatted_item

def get_day_of_week_from_date(date_obj_or_str: Optional[Union[str, datetime.date]]) -> int:
    """
    Determina el día de la semana (1-7) a partir de una fecha.
    
    Args:
        date_obj_or_str: Objeto datetime.date o string en formato ISO (%Y-%m-%d)
        
    Returns:
        int: Número de día (1=lunes ... 7=domingo)
    """
    if not date_obj_or_str:
        return 1  # Valor por defecto: lunes
        
    try:
        # Si es un string, convertir a objeto date
        if isinstance(date_obj_or_str, str):
            from datetime import datetime
            date_obj = datetime.strptime(date_obj_or_str, "%Y-%m-%d").date()
        # Si ya es un objeto date o datetime, usarlo directamente
        elif isinstance(date_obj_or_str, datetime.date):
            date_obj = date_obj_or_str
        else:
            logger.error(f"Tipo de fecha no soportado: {type(date_obj_or_str)}")
            return 1
        
        # Obtener día de la semana (0=lunes en la librería datetime de Python)
        weekday_num = date_obj.weekday()
        # Sumar 1 para que lunes=1, ... domingo=7
        return weekday_num + 1
        
    except Exception as e:
        logger.error(f"Error al calcular día de la semana desde fecha {date_obj_or_str}: {e}")
        return 1  # Valor por defecto: lunes