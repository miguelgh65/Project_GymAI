# fitness-agent/agent/tools/exercise_tools.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
import json
import os

from fitness_agent.agent.schemas import ExerciseSet, Exercise

@tool
def get_recent_exercises(user_id: str, days: int = 7) -> str:
    """
    Obtiene los ejercicios recientes del usuario.
    
    Args:
        user_id: ID del usuario
        days: Número de días hacia atrás
        
    Returns:
        Información sobre los ejercicios recientes en formato JSON
    """
    try:
        # Aquí normalmente harías una consulta a la base de datos
        # Por ahora retornamos datos de ejemplo
        
        # Simular una consulta a la BD
        cutoff = datetime.now() - timedelta(days=days)
        
        # Datos de ejemplo
        sample_exercises = [
            {
                "fecha": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                "ejercicio": "Press Banca",
                "series": [
                    {"repeticiones": 10, "peso": 80},
                    {"repeticiones": 8, "peso": 85},
                    {"repeticiones": 6, "peso": 90}
                ]
            },
            {
                "fecha": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                "ejercicio": "Sentadillas",
                "series": [
                    {"repeticiones": 12, "peso": 100},
                    {"repeticiones": 10, "peso": 110},
                    {"repeticiones": 8, "peso": 120}
                ]
            },
            {
                "fecha": (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S'),
                "ejercicio": "Dominadas",
                "series": [
                    {"repeticiones": 10, "peso": 0},
                    {"repeticiones": 8, "peso": 0},
                    {"repeticiones": 6, "peso": 0}
                ]
            }
        ]
        
        return json.dumps(sample_exercises)
    except Exception as e:
        return f"Error al obtener ejercicios recientes: {str(e)}"

@tool
def get_exercise_stats(user_id: str, exercise_name: str) -> str:
    """
    Obtiene estadísticas de un ejercicio específico para el usuario.
    
    Args:
        user_id: ID del usuario
        exercise_name: Nombre del ejercicio
        
    Returns:
        Estadísticas del ejercicio en formato JSON
    """
    try:
        # Simular estadísticas de ejercicio
        stats = {
            "nombre_ejercicio": exercise_name,
            "max_peso": 100,
            "series_totales": 36,
            "repeticiones_totales": 288,
            "volumen_total": 25200,
            "frecuencia_semanal": 1.5,
            "progresion_ultimo_mes": "+5kg"
        }
        
        return json.dumps(stats)
    except Exception as e:
        return f"Error al obtener estadísticas: {str(e)}"

@tool
def recommend_exercise_progression(user_id: str, exercise_name: str) -> str:
    """
    Recomienda una progresión para un ejercicio específico.
    
    Args:
        user_id: ID del usuario
        exercise_name: Nombre del ejercicio
        
    Returns:
        Recomendación de progresión
    """
    try:
        # Obtener estadísticas simuladas para basar la recomendación
        stats_json = get_exercise_stats(user_id, exercise_name)
        stats = json.loads(stats_json)
        
        max_peso = stats.get("max_peso", 0)
        
        # Lógica simplificada de recomendación
        new_weight = max_peso * 1.05  # 5% de incremento
        
        recommendation = {
            "ejercicio": exercise_name,
            "peso_actual_maximo": max_peso,
            "peso_recomendado": round(new_weight, 1),
            "esquema_recomendado": "4 series de 6-8 repeticiones",
            "explicacion": f"Basado en tu historial, recomiendo aumentar el peso a {round(new_weight, 1)}kg y reducir ligeramente las repeticiones para mantener la progresión de fuerza."
        }
        
        return json.dumps(recommendation)
    except Exception as e:
        return f"Error al generar recomendación: {str(e)}"

# Lista de herramientas disponibles para el nodo de ejercicios
exercise_tools = [
    get_recent_exercises,
    get_exercise_stats,
    recommend_exercise_progression
]