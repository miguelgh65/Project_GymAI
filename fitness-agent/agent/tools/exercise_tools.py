# Archivo: workflows/gym/services/langgraph_agent/tools.py

import json
import datetime
import psycopg2
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from config import DB_CONFIG

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
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')
        
        query = """
            SELECT fecha, ejercicio, repeticiones, duracion
            FROM ejercicios
            WHERE fecha >= %s AND user_id = %s
            ORDER BY fecha DESC
        """
        cur.execute(query, (cutoff_str, user_id))
        rows = cur.fetchall()
        
        logs = []
        for row in rows:
            data = row[2] if row[2] is not None else row[3]
            logs.append({
                "fecha": row[0].strftime('%Y-%m-%d %H:%M:%S'),
                "ejercicio": row[1],
                "data": data
            })
        
        cur.close()
        conn.close()
        
        return json.dumps(logs)
    except Exception as e:
        return f"Error al obtener ejercicios recientes: {str(e)}"

@tool
def get_today_workout(user_id: str) -> str:
    """
    Obtiene el entrenamiento del día actual para el usuario.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Ejercicios para hoy en formato JSON
    """
    try:
        from utils.date_utils import get_weekday_name
        dia_actual = datetime.datetime.now().isoweekday()
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT ejercicios FROM rutinas WHERE user_id = %s AND dia_semana = %s",
            (user_id, dia_actual)
        )
        
        row = cur.fetchone()
        
        if not row:
            return json.dumps({
                "success": False,
                "message": "No hay rutina definida para hoy.",
                "dia_nombre": get_weekday_name(dia_actual)
            })
        
        if isinstance(row[0], str):
            ejercicios_hoy = json.loads(row[0])
        else:
            ejercicios_hoy = row[0]
        
        # Verificar ejercicios ya realizados
        hoy = datetime.datetime.now().strftime('%Y-%m-%d')
        cur.execute(
            """
            SELECT ejercicio FROM ejercicios 
            WHERE user_id = %s AND fecha::date = %s::date
            """,
            (user_id, hoy)
        )
        
        ejercicios_realizados = [row[0] for row in cur.fetchall()]
        
        rutina_resultado = []
        for ejercicio in ejercicios_hoy:
            rutina_resultado.append({
                "ejercicio": ejercicio,
                "realizado": ejercicio in ejercicios_realizados
            })
        
        cur.close()
        conn.close()
        
        return json.dumps({
            "success": True,
            "message": "Rutina para hoy obtenida correctamente.",
            "rutina": rutina_resultado,
            "dia_nombre": get_weekday_name(dia_actual)
        })
        
    except Exception as e:
        return f"Error al obtener rutina de hoy: {str(e)}"