# Archivo: routes/dashboard.py (CON LOGS DE DEBUG PARA PROGRESO)

import os
import sys
import logging
import json
from datetime import datetime
import math # Necesario para e y otros cálculos si usas otras fórmulas

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

# Asumiendo que config y middlewares están accesibles
from config import DB_CONFIG
from back_end.gym.middlewares import get_current_user # Asegúrate que esta importación funciona

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["dashboard", "stats"],
)

# Función para calcular e1RM (Brzycki)
def calculate_e1rm_brzycki(weight: float, reps: int) -> float | None:
    """Calcula el 1RM estimado usando la fórmula de Brzycki."""
    if reps <= 0 or weight <= 0: return 0
    if reps == 1: return weight
    if reps > 15: return None # Límite opcional

    denominator = 1.0278 - (0.0278 * reps)
    if denominator <= 0: return None

    e1rm = weight / denominator
    return round(e1rm, 2)


@router.get("/ejercicios_stats", response_class=JSONResponse)
async def get_ejercicios_stats(
    request: Request,
    ejercicio: str = Query(None, description="Nombre del ejercicio para filtrar"),
    desde: str = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    hasta: str = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    user = Depends(get_current_user)
):
    # Verificación de usuario (usando google_id)
    if not user or not user.get('google_id'):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado o sin ID de Google válido.")
    user_id_for_query = user['google_id']
    logger.info(f"Obteniendo estadísticas para usuario Google ID: {user_id_for_query}")

    conn = None
    cur = None
    try:
        # Construcción de query_conditions y query_params (usando google_id)
        query_conditions = ["user_id = %s"]
        query_params = [user_id_for_query]
        if ejercicio:
            query_conditions.append("ejercicio ILIKE %s")
            query_params.append(f"%{ejercicio}%")
        if desde:
            try:
                datetime.strptime(desde, '%Y-%m-%d')
                query_conditions.append("fecha >= %s")
                query_params.append(desde)
            except ValueError: raise HTTPException(status_code=400, detail="Formato 'desde' inválido.")
        if hasta:
            try:
                datetime.strptime(hasta, '%Y-%m-%d')
                hasta_con_hora = f"{hasta} 23:59:59"
                query_conditions.append("fecha <= %s")
                query_params.append(hasta_con_hora)
            except ValueError: raise HTTPException(status_code=400, detail="Formato 'hasta' inválido.")
        where_clause = " AND ".join(query_conditions)

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # cur.execute("SET search_path TO gym, public;") # Si es necesario

        # Obtener lista de ejercicios únicos (usando google_id)
        ejercicios_query = "SELECT DISTINCT ejercicio FROM gym.ejercicios WHERE user_id = %s ORDER BY ejercicio"
        cur.execute(ejercicios_query, (user_id_for_query,))
        ejercicios_list = [row[0] for row in cur.fetchall()]

        # Inicializar resultados
        exercise_data = []
        summary = {}
        entries_by_exercise = {}

        # Obtener datos crudos (usando google_id)
        data_query = f"""
            SELECT fecha, repeticiones, ejercicio
            FROM gym.ejercicios
            WHERE {where_clause} AND repeticiones IS NOT NULL AND repeticiones != 'null'
            ORDER BY fecha
        """
        cur.execute(data_query, query_params)
        rows = cur.fetchall()
        logger.info(f"Consulta devolvió {len(rows)} filas para Google ID {user_id_for_query}")

        # --- Inicio Procesamiento de Datos (con cálculo de e1RM) ---
        for row in rows:
            # ... (lógica de procesamiento de cada fila, cálculo de métricas por sesión
            #      incluyendo max_e1rm_session, como en la versión anterior) ...
            fecha, series_json, nombre_ejercicio = row
            current_exercise_name = nombre_ejercicio if not ejercicio else ejercicio
            if current_exercise_name not in entries_by_exercise: entries_by_exercise[current_exercise_name] = []
            if series_json:
                try:
                    series = json.loads(series_json) if isinstance(series_json, str) else series_json
                    if not isinstance(series, list): continue
                    max_peso_session = 0
                    total_volumen_session = 0
                    total_reps_session = 0
                    max_e1rm_session = 0
                    valid_series_count = 0
                    for serie in series:
                        if isinstance(serie, dict) and 'repeticiones' in serie and 'peso' in serie:
                            try:
                                reps = int(serie.get('repeticiones', 0))
                                peso = float(serie.get('peso', 0))
                                if reps > 0 and peso > 0:
                                    total_reps_session += reps
                                    total_volumen_session += reps * peso
                                    max_peso_session = max(max_peso_session, peso)
                                    valid_series_count += 1
                                    e1rm_serie = calculate_e1rm_brzycki(peso, reps)
                                    if e1rm_serie is not None: max_e1rm_session = max(max_e1rm_session, e1rm_serie)
                            except (ValueError, TypeError): continue
                    if valid_series_count > 0:
                        avg_peso_session = total_volumen_session / total_reps_session if total_reps_session > 0 else 0
                        entries_by_exercise[current_exercise_name].append({
                            "fecha": fecha.strftime('%Y-%m-%d'),
                            "max_peso": max_peso_session,
                            "avg_peso": round(avg_peso_session, 2),
                            "total_reps": total_reps_session,
                            "volumen": round(total_volumen_session, 2),
                            "max_e1rm_session": max_e1rm_session
                        })
                except json.JSONDecodeError: continue
                except Exception: continue
        # --- Fin Procesamiento de Datos ---


        # Calcular resumen si se filtró por un ejercicio específico
        if ejercicio and ejercicio in entries_by_exercise:
            exercise_data = entries_by_exercise[ejercicio]
            total_sesiones = len(exercise_data)
            if total_sesiones > 0:
                max_weight_ever = max(entry['max_peso'] for entry in exercise_data)
                max_volume_session = max(entry['volumen'] for entry in exercise_data)
                max_reps_session = max(entry['total_reps'] for entry in exercise_data)
                max_e1rm_ever = max(entry['max_e1rm_session'] for entry in exercise_data)

                # <<< INICIO BLOQUE DE CÁLCULO DE PROGRESO CON LOGS >>>
                logger.info(f"--- DEBUG Progreso ---")
                logger.info(f"Total sesiones para cálculo: {total_sesiones}")
                weight_progress = 0
                progress_percent = 0
                if total_sesiones >= 2:
                    # Asegurarse que exercise_data está ordenado por fecha (ya debería por el SQL)
                    first_session = exercise_data[0]
                    last_session = exercise_data[-1]
                    # Añadir logs para ver qué sesiones se están comparando
                    logger.info(f"Primera sesión (fecha {first_session.get('fecha')}): max_peso = {first_session.get('max_peso')}")
                    logger.info(f"Última sesión (fecha {last_session.get('fecha')}): max_peso = {last_session.get('max_peso')}")

                    # Asegurarse que los pesos son números antes de calcular
                    try:
                        # Usar .get con default 0 por si la clave faltara (aunque no debería)
                        first_peso = float(first_session.get('max_peso', 0))
                        last_peso = float(last_session.get('max_peso', 0))

                        weight_progress = last_peso - first_peso
                        logger.info(f"Progreso absoluto peso: {weight_progress}")

                        if first_peso > 0:
                            progress_percent = (weight_progress / first_peso) * 100
                            logger.info(f"Progreso porcentual calculado: {progress_percent}")
                        else:
                            logger.info("Peso inicial es 0, progreso porcentual es 0.")
                            progress_percent = 0
                    except (TypeError, ValueError) as e:
                        logger.error(f"Error al convertir pesos para cálculo de progreso: {e}")
                        progress_percent = 0 # Error en conversión, progreso 0
                else:
                    logger.info("Menos de 2 sesiones, progreso es 0.")
                    progress_percent = 0
                logger.info(f"Valor final progress_percent antes de añadir a summary: {progress_percent}")
                # <<< FIN BLOQUE DE CÁLCULO DE PROGRESO CON LOGS >>>

                summary = {
                    "total_sesiones": total_sesiones,
                    "max_weight_ever": max_weight_ever,
                    "max_volume_session": max_volume_session,
                    "max_reps_session": max_reps_session,
                    "max_e1rm_ever": max_e1rm_ever,
                    "progress_percent": round(progress_percent, 2) # Usar el valor calculado y loggeado
                }
            else: # No hay datos válidos para este ejercicio en el rango
                summary = {"total_sesiones": 0, "max_e1rm_ever": 0, "progress_percent": 0}
        else:
             summary = None # O {} si prefieres

        # Construir la respuesta final
        response_content = {
            "success": True,
            "ejercicios_disponibles": ejercicios_list,
            "filtro_ejercicio": ejercicio,
            "datos_agrupados": entries_by_exercise,
            "datos": exercise_data if ejercicio else [],
            "resumen": summary if ejercicio and summary is not None else {}
        }

        # Log opcional para ver la respuesta completa justo antes de enviarla
        # logger.info("--- DEBUG BACKEND RESPONSE ---")
        # try: logger.info(json.dumps(response_content, indent=2, default=str))
        # except Exception as print_err: logger.info(f"Raw response_content: {response_content}")
        # logger.info("--- FIN DEBUG BACKEND RESPONSE ---")

        return JSONResponse(content=response_content)

    # Manejo de excepciones
    except HTTPException as http_exc: raise http_exc
    except psycopg2.Error as db_err:
        logger.error(f"Error DB: {db_err}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error BBDD.")
    except Exception as e:
        logger.exception(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail="Error inesperado.")
    finally:
        if cur: cur.close()
        if conn: conn.close()


# --- Endpoint /api/calendar_heatmap (sin cambios, usa google_id) ---
@router.get("/calendar_heatmap", response_class=JSONResponse)
async def get_calendar_heatmap(
    request: Request,
    year: int = Query(datetime.now().year),
    user = Depends(get_current_user)
):
     if not user or not user.get('google_id'):
        raise HTTPException(status_code=401, detail="Usuario no autenticado o sin ID Google.")
     user_id_for_query = user['google_id']
     logger.info(f"Obteniendo datos de calendario para usuario Google ID: {user_id_for_query}, Año: {year}")
     conn=None
     cur=None
     try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = """
            SELECT fecha::date as day, COUNT(DISTINCT ejercicio) as value
            FROM gym.ejercicios
            WHERE user_id = %s AND EXTRACT(YEAR FROM fecha) = %s
            GROUP BY day ORDER BY day
        """
        cur.execute(query, (user_id_for_query, year))
        rows = cur.fetchall()
        heatmap_data = [{"date": row[0].strftime('%Y-%m-%d'), "count": row[1]} for row in rows]
        return JSONResponse(content={"success": True, "year": year, "data": heatmap_data})
     except Exception as e:
        logger.exception(f"Error heatmap user {user_id_for_query}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo datos heatmap.")
     finally:
        if cur: cur.close()
        if conn: conn.close()