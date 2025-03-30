import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_weekday_name(day_number):
    """
    Obtiene el nombre del día de la semana en español basado en su número.
    
    Args:
        day_number (int): Número del día de la semana (1=Lunes, 7=Domingo)
        
    Returns:
        str: Nombre del día de la semana en español
    """
    days = {
        1: "Lunes",
        2: "Martes",
        3: "Miércoles",
        4: "Jueves",
        5: "Viernes",
        6: "Sábado",
        7: "Domingo"
    }
    return days.get(day_number, "Desconocido")