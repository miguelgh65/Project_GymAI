# Archivo: fitness_agent/agent/tools/exercise_tools.py

import datetime
import json
import logging
from typing import Any, Dict, List, Optional

import psycopg2

# Configurar logger
logger = logging.getLogger("fitness_agent")

# Tratar de importar decorador
try:
    from fitness_agent.agent.nodes.router_node import traceable
except ImportError:
    # Simple decorator fallback
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Tratar de importar configuración de la DB
try:
    from config import DB_CONFIG
except ImportError:
    # Configuración predeterminada como fallback
    logger.warning("Could not import DB_CONFIG, using default configuration")
    DB_CONFIG = {
        'dbname': 'gymdb',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'postgres_gymdb',
        'port': '5432',
        'options': f'-c search_path=gym,public'
    }

@traceable(run_type="tool")
def get_recent_exercises(user_id: str, days: int = 7, exercise_name: str = None) -> str:
    """
    Obtiene los ejercicios recientes del usuario.
    
    Args:
        user_id: ID del usuario
        days: Número de días hacia atrás
        exercise_name: Nombre del ejercicio para filtrar (opcional)
        
    Returns:
        Información sobre los ejercicios recientes en formato JSON
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')
        
        # Try to convert user_id to int for user_uuid lookup
        try:
            user_uuid = int(user_id)
            has_uuid = True
        except ValueError:
            user_uuid = None
            has_uuid = False
        
        # Build query - if exercise_name is provided, filter by exercise name
        if exercise_name:
            if has_uuid:
                query = """
                    SELECT fecha, ejercicio, repeticiones, duracion
                    FROM ejercicios
                    WHERE fecha >= %s AND (user_id = %s OR user_uuid = %s) AND LOWER(ejercicio) = LOWER(%s)
                    ORDER BY fecha DESC
                """
                cur.execute(query, (cutoff_str, user_id, user_uuid, exercise_name))
            else:
                query = """
                    SELECT fecha, ejercicio, repeticiones, duracion
                    FROM ejercicios
                    WHERE fecha >= %s AND user_id = %s AND LOWER(ejercicio) = LOWER(%s)
                    ORDER BY fecha DESC
                """
                cur.execute(query, (cutoff_str, user_id, exercise_name))
        else:
            if has_uuid:
                query = """
                    SELECT fecha, ejercicio, repeticiones, duracion
                    FROM ejercicios
                    WHERE fecha >= %s AND (user_id = %s OR user_uuid = %s)
                    ORDER BY fecha DESC
                """
                cur.execute(query, (cutoff_str, user_id, user_uuid))
            else:
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
            fecha = row[0].strftime('%Y-%m-%d %H:%M:%S')
            ejercicio = row[1]
            repeticiones = row[2]
            duracion = row[3]
            
            entry = {"fecha": fecha, "ejercicio": ejercicio}
            
            # Process repeticiones (could be JSON or string)
            if repeticiones:
                if isinstance(repeticiones, str):
                    try:
                        series = json.loads(repeticiones)
                        entry["series"] = series
                    except json.JSONDecodeError:
                        entry["series"] = repeticiones
                else:
                    entry["series"] = repeticiones
                    
            # Add duration if available
            if duracion:
                entry["duracion"] = duracion
                
            logs.append(entry)
        
        cur.close()
        conn.close()
        
        return json.dumps(logs, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error getting recent exercises: {e}")
        return f"Error al obtener ejercicios recientes: {str(e)}"

@traceable(run_type="tool")
def get_exercise_stats(user_id: str, exercise_name: str = None) -> str:
    """
    Obtiene estadísticas para un ejercicio específico.
    
    Args:
        user_id: ID del usuario
        exercise_name: Nombre del ejercicio (opcional)
        
    Returns:
        Estadísticas del ejercicio en formato JSON
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Try to convert user_id to int for user_uuid lookup
        try:
            user_uuid = int(user_id)
            has_uuid = True
        except ValueError:
            user_uuid = None
            has_uuid = False
        
        # Si se especifica un ejercicio, obtener sus estadísticas
        if exercise_name:
            # Query para obtener todos los ejercicios del tipo específico
            if has_uuid:
                query = """
                    SELECT fecha, repeticiones 
                    FROM ejercicios 
                    WHERE (user_id = %s OR user_uuid = %s) AND LOWER(ejercicio) = LOWER(%s) AND repeticiones IS NOT NULL
                    ORDER BY fecha
                """
                cur.execute(query, (user_id, user_uuid, exercise_name))
            else:
                query = """
                    SELECT fecha, repeticiones 
                    FROM ejercicios 
                    WHERE user_id = %s AND LOWER(ejercicio) = LOWER(%s) AND repeticiones IS NOT NULL
                    ORDER BY fecha
                """
                cur.execute(query, (user_id, exercise_name))
            
            rows = cur.fetchall()
            
            # Calcular estadísticas
            stats = {
                "nombre_ejercicio": exercise_name,
                "total_sesiones": len(rows)
            }
            
            if rows:
                # Listas para acumular datos
                max_pesos = []
                volumen_por_sesion = []
                fechas = []
                
                for row in rows:
                    fecha = row[0].strftime('%Y-%m-%d %H:%M:%S')
                    fechas.append(fecha)
                    rep_data = row[1]
                    
                    # Parsear datos de repeticiones
                    try:
                        if isinstance(rep_data, str):
                            series = json.loads(rep_data)
                        else:
                            series = rep_data
                        
                        # Calcular peso máximo y volumen para esta sesión
                        max_peso_sesion = 0
                        volumen_sesion = 0
                        
                        for serie in series:
                            if isinstance(serie, dict):
                                reps = serie.get('repeticiones', 0)
                                peso = serie.get('peso', 0)
                                max_peso_sesion = max(max_peso_sesion, peso)
                                volumen_sesion += reps * peso
                        
                        max_pesos.append(max_peso_sesion)
                        volumen_por_sesion.append(volumen_sesion)
                    except (json.JSONDecodeError, TypeError, AttributeError) as e:
                        logger.warning(f"Error parsing repetition data: {e}")
                
                # Añadir estadísticas
                if max_pesos:
                    stats["max_peso"] = max(max_pesos)
                    stats["promedio_peso_max"] = sum(max_pesos) / len(max_pesos)
                
                if volumen_por_sesion:
                    stats["max_volumen"] = max(volumen_por_sesion)
                    stats["promedio_volumen"] = sum(volumen_por_sesion) / len(volumen_por_sesion)
                
                # Calcular progresión
                if len(max_pesos) >= 2:
                    primer_peso = max_pesos[0]
                    ultimo_peso = max_pesos[-1]
                    if primer_peso > 0:
                        progresion = ((ultimo_peso - primer_peso) / primer_peso) * 100
                        stats["progresion_peso"] = round(progresion, 2)
                
                # Añadir primera y última fecha
                if fechas:
                    stats["primera_sesion"] = fechas[0]
                    stats["ultima_sesion"] = fechas[-1]
            
            cur.close()
            conn.close()
            
            return json.dumps(stats, ensure_ascii=False)
        else:
            # Si no se especifica ejercicio, obtener estadísticas generales
            if has_uuid:
                query = """
                    SELECT ejercicio, COUNT(*) as total_sesiones
                    FROM ejercicios 
                    WHERE user_id = %s OR user_uuid = %s
                    GROUP BY ejercicio
                    ORDER BY total_sesiones DESC
                """
                cur.execute(query, (user_id, user_uuid))
            else:
                query = """
                    SELECT ejercicio, COUNT(*) as total_sesiones
                    FROM ejercicios 
                    WHERE user_id = %s
                    GROUP BY ejercicio
                    ORDER BY total_sesiones DESC
                """
                cur.execute(query, (user_id,))
            
            rows = cur.fetchall()
            
            ejercicios_stats = {
                "total_ejercicios": len(rows),
                "ejercicios": {}
            }
            
            for row in rows:
                ejercicio = row[0]
                total = row[1]
                ejercicios_stats["ejercicios"][ejercicio] = total
            
            cur.close()
            conn.close()
            
            return json.dumps(ejercicios_stats, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error getting exercise stats: {e}")
        return f"Error al obtener estadísticas de ejercicios: {str(e)}"

@traceable(run_type="tool")
def recommend_exercise_progression(user_id: str, exercise_name: str) -> str:
    """
    Recomienda una progresión de ejercicio basada en el historial del usuario.
    
    Args:
        user_id: ID del usuario
        exercise_name: Nombre del ejercicio
        
    Returns:
        Recomendación de progresión en formato JSON
    """
    try:
        # Obtener estadísticas recientes del ejercicio
        stats_data = get_exercise_stats(user_id, exercise_name)
        stats = json.loads(stats_data)
        
        # Obtener el último workout
        recent_data = get_recent_exercises(user_id, days=30, exercise_name=exercise_name)
        recent_workouts = json.loads(recent_data)
        
        # Preparar la recomendación
        recommendation = {
            "ejercicio": exercise_name,
            "estadisticas_actuales": stats,
            "recomendacion": {}
        }
        
        # Si hay workouts recientes, usar el último como base
        if recent_workouts and len(recent_workouts) > 0:
            ultimo_workout = recent_workouts[0]
            series = ultimo_workout.get("series", [])
            
            if series and len(series) > 0:
                # Calcular siguientes series recomendadas (incremento aproximado del 5%)
                nuevas_series = []
                
                for serie in series:
                    if isinstance(serie, dict):
                        reps = serie.get("repeticiones", 0)
                        peso = serie.get("peso", 0)
                        
                        # Incrementar peso en ~5% (redondeado a 2.5kg)
                        nuevo_peso = round(peso * 1.05 / 2.5) * 2.5
                        
                        if nuevo_peso <= peso:
                            nuevo_peso = peso + 2.5
                        
                        nuevas_series.append({
                            "repeticiones": reps,
                            "peso": nuevo_peso
                        })
                
                recommendation["recomendacion"] = {
                    "series_recomendadas": nuevas_series,
                    "explicacion": "Incremento del 5% en el peso manteniendo las mismas repeticiones."
                }
            else:
                recommendation["recomendacion"] = {
                    "mensaje": "No hay suficientes datos para realizar una recomendación precisa."
                }
        else:
            recommendation["recomendacion"] = {
                "mensaje": "No hay suficientes datos recientes para realizar una recomendación."
            }
        
        return json.dumps(recommendation, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error creating exercise progression recommendation: {e}")
        return f"Error al crear recomendación de progresión: {str(e)}"