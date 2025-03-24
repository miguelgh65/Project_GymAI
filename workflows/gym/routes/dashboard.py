import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify, render_template
import json
import psycopg2
from datetime import datetime
from config import DB_CONFIG

# Crear blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Página principal del dashboard de análisis."""
    user_id = request.args.get('user_id', "3892415")
    return render_template('dashboard.html', user_id=user_id)

@dashboard_bp.route('/api/ejercicios_stats', methods=['GET'])
def get_ejercicios_stats():
    """API para obtener estadísticas de los ejercicios."""
    user_id = request.args.get('user_id', "3892415")
    exercise = request.args.get('ejercicio', None)
    date_from = request.args.get('desde', None)
    date_to = request.args.get('hasta', None)
    
    # Construir la consulta base
    query_conditions = ["user_id = %s"]
    query_params = [user_id]
    
    if exercise:
        query_conditions.append("ejercicio = %s")
        query_params.append(exercise)
    
    if date_from:
        query_conditions.append("fecha >= %s")
        query_params.append(date_from)
    
    if date_to:
        query_conditions.append("fecha <= %s")
        query_params.append(date_to)
    
    where_clause = " AND ".join(query_conditions)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Obtener lista de ejercicios para el selector
        cur.execute(
            "SELECT DISTINCT ejercicio FROM ejercicios WHERE user_id = %s ORDER BY ejercicio",
            (user_id,)
        )
        ejercicios_list = [row[0] for row in cur.fetchall()]
        
        # Si se especificó un ejercicio, obtener sus datos detallados
        if exercise:
            # Para ejercicios de fuerza (con series y repeticiones)
            cur.execute(
                f"""
                SELECT fecha, repeticiones 
                FROM ejercicios 
                WHERE {where_clause} AND repeticiones IS NOT NULL
                ORDER BY fecha
                """,
                query_params
            )
            rows = cur.fetchall()
            
            exercise_data = []
            for row in rows:
                fecha = row[0]
                series_json = row[1]  # Esto es un JSON con las series
                
                # Calcular métricas para cada entrada
                if series_json:
                    try:
                        series = json.loads(series_json) if isinstance(series_json, str) else series_json
                        
                        # Calcular peso máximo, promedio y volumen total
                        max_peso = 0
                        total_volumen = 0
                        total_reps = 0
                        
                        for serie in series:
                            reps = serie.get('repeticiones', 0)
                            peso = serie.get('peso', 0)
                            
                            total_reps += reps
                            total_volumen += reps * peso
                            max_peso = max(max_peso, peso)
                        
                        avg_peso = total_volumen / total_reps if total_reps > 0 else 0
                        
                        exercise_data.append({
                            "fecha": fecha.strftime('%Y-%m-%d'),
                            "series": series,
                            "max_peso": max_peso,
                            "avg_peso": round(avg_peso, 2),
                            "total_reps": total_reps,
                            "volumen": total_volumen
                        })
                    except Exception as e:
                        print(f"Error al procesar series JSON: {e}")
            
            # Obtener métricas resumen
            total_sesiones = len(exercise_data)
            
            if total_sesiones > 0:
                max_weight_ever = max(entry['max_peso'] for entry in exercise_data)
                max_volume_session = max(entry['volumen'] for entry in exercise_data)
                max_reps_session = max(entry['total_reps'] for entry in exercise_data)
                avg_volume = sum(entry['volumen'] for entry in exercise_data) / total_sesiones
                
                # Calcular progreso (comparación entre primera y última sesión)
                if len(exercise_data) >= 2:
                    first_session = exercise_data[0]
                    last_session = exercise_data[-1]
                    weight_progress = last_session['max_peso'] - first_session['max_peso']
                    volume_progress = last_session['volumen'] - first_session['volumen']
                    progress_percent = (weight_progress / first_session['max_peso'] * 100) if first_session['max_peso'] > 0 else 0
                else:
                    weight_progress = 0
                    volume_progress = 0
                    progress_percent = 0
                
                summary = {
                    "total_sesiones": total_sesiones,
                    "max_weight_ever": max_weight_ever,
                    "max_volume_session": max_volume_session,
                    "max_reps_session": max_reps_session,
                    "avg_volume": round(avg_volume, 2),
                    "weight_progress": round(weight_progress, 2),
                    "volume_progress": round(volume_progress, 2),
                    "progress_percent": round(progress_percent, 2)
                }
            else:
                summary = {
                    "total_sesiones": 0,
                    "max_weight_ever": 0,
                    "max_volume_session": 0,
                    "max_reps_session": 0,
                    "avg_volume": 0,
                    "weight_progress": 0,
                    "volume_progress": 0,
                    "progress_percent": 0
                }
            
            result = {
                "success": True,
                "ejercicio": exercise,
                "datos": exercise_data,
                "resumen": summary
            }
        else:
            # Si no se especificó ejercicio, devolver solo la lista de ejercicios
            result = {
                "success": True,
                "ejercicios": ejercicios_list
            }
        
        cur.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al obtener estadísticas: {str(e)}"
        })

@dashboard_bp.route('/api/calendar_heatmap', methods=['GET'])
def get_calendar_heatmap():
    """Datos para el mapa de calor del calendario de actividad."""
    user_id = request.args.get('user_id', "3892415")
    year = request.args.get('year', datetime.now().year)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Consulta para obtener conteo de ejercicios por día
        query = """
            SELECT 
                fecha::date as day,
                COUNT(*) as count
            FROM ejercicios
            WHERE user_id = %s AND EXTRACT(YEAR FROM fecha) = %s
            GROUP BY day
            ORDER BY day
        """
        
        cur.execute(query, (user_id, year))
        rows = cur.fetchall()
        
        heatmap_data = []
        for row in rows:
            heatmap_data.append({
                "date": row[0].strftime('%Y-%m-%d'),
                "count": row[1]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": heatmap_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al obtener datos del calendario: {str(e)}"
        })