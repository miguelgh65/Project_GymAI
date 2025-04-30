# fitness_agent/agent/tools/nutrition_tools.py
from typing import Dict, List, Optional


def get_recent_nutrition_logs(user_id: str, days: int = 30) -> List[Dict]:
    """
    Placeholder para obtener registros nutricionales recientes.
    Por ahora, devuelve una lista vacía.
    
    Args:
        user_id: ID del usuario
        days: Número de días hacia atrás para buscar registros
    
    Returns:
        Lista vacía de registros nutricionales
    """
    return []

def calculate_macronutrients(user_id: str, days: int = 30) -> Dict[str, float]:
    """
    Placeholder para calcular macronutrientes.
    Por ahora, devuelve un diccionario con valores por defecto.
    
    Args:
        user_id: ID del usuario
        days: Número de días para calcular el promedio
    
    Returns:
        Diccionario con macronutrientes promedio por defecto
    """
    return {
        "proteinas": 0.0,
        "carbohidratos": 0.0,
        "grasas": 0.0
    }

def get_nutrition_recommendations(user_id: str) -> Dict[str, Any]:
    """
    Placeholder para obtener recomendaciones nutricionales.
    Por ahora, devuelve un diccionario vacío.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Diccionario vacío de recomendaciones
    """
    return {}