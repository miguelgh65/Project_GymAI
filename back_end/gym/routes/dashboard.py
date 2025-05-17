# Archivo: back_end/gym/routes/dashboard.py
import os
import sys
import logging
import json
from datetime import datetime
import math

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Importaciones correctas
from back_end.gym.middlewares import get_current_user
from back_end.gym.config import DB_CONFIG

# Configurar logger
logger = logging.getLogger(__name__)

# Crear router con el prefijo correcto
router = APIRouter(
    prefix="/api",
    tags=["dashboard", "stats"],
)

# Modelo para respuesta
class DashboardResponse(BaseModel):
    success: bool
    message: str
    datos: Optional[List[Dict[str, Any]]] = None
    ejercicios_disponibles: Optional[List[str]] = None
    resumen: Optional[Dict[str, Any]] = None

# Función para calcular e1RM (Brzycki)
def calculate_e1rm_brzycki(weight: float, reps: int) -> float:
    """Calcula el 1RM estimado usando la fórmula de Brzycki."""
    if reps <= 0 or weight <= 0: 
        return 0
    if reps == 1: 
        return weight
    if reps > 15: 
        return 0  # Límite opcional

    denominator = 1.0278 - (0.0278 * reps)
    if denominator <= 0: 
        return 0

    e1rm = weight / denominator
    return round(e1rm, 2)

# Ruta para obtener lista de ejercicios y estadísticas
@router.get("/ejercicios_stats", response_model=DashboardResponse)
async def get_ejercicios_stats(
    request: Request,
    ejercicio: Optional[str] = None,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    user = Depends(get_current_user)
):
    try:
        # Validar que exista usuario
        if not user or not user.get('google_id'):
            raise HTTPException(status_code=401, detail="Autenticación requerida")
        
        # Obtener el ID de Google del usuario
        google_id = user.get('google_id')
        logger.info(f"Obteniendo estadísticas para usuario Google ID: {google_id}")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Si no se especifica un ejercicio, devolver solo la lista de ejercicios disponibles
        if not ejercicio:
            # Obtener solo ejercicios que tienen datos
            # No filtrar por repeticiones o series_json no nulas
            query = """
                SELECT DISTINCT ejercicio 
                FROM gym.ejercicios 
                WHERE user_id = %s
                ORDER BY ejercicio
            """
            logger.info(f"Consulta para listar ejercicios: {query}")
            cur.execute(query, (google_id,))
            ejercicios_disponibles = [row[0] for row in cur.fetchall()]
            logger.info(f"Ejercicios disponibles: {ejercicios_disponibles}")
            
            # Cerrar conexión
            cur.close()
            conn.close()
            
            return {
                "success": True,
                "message": "Lista de ejercicios obtenida correctamente",
                "ejercicios_disponibles": ejercicios_disponibles,
                "datos": [],
                "resumen": {}
            }
        
        # Si se especifica un ejercicio, construir la consulta con filtros
        query_params = [google_id, ejercicio]
        
        # Construir la parte de la consulta para filtros de fecha
        date_filter = ""
        if desde:
            date_filter += " AND fecha >= %s"
            query_params.append(desde)
        if hasta:
            date_filter += " AND fecha <= %s"
            query_params.append(hasta)
        
        # Consulta principal - Adaptada para el nuevo esquema
        # NO FILTRAR por repeticiones o series_json no nulas para depuración
        data_query = f"""
            SELECT fecha, repeticiones, ejercicio, series_json, comentarios, rir
            FROM gym.ejercicios
            WHERE user_id = %s AND ejercicio = %s{date_filter}
            ORDER BY fecha
        """
        
        logger.info(f"Consulta para datos de ejercicio: {data_query}")
        logger.info(f"Parámetros: {query_params}")
        
        cur.execute(data_query, query_params)
        rows = cur.fetchall()
        
        logger.info(f"Filas devueltas para {ejercicio}: {len(rows)}")
        for i, row in enumerate(rows):
            logger.info(f"Fila {i+1}: {row}")
        
        # Estructuras para procesar los datos
        processed_data = []
        peso_max_ever = 0
        volumen_max_session = 0
        e1rm_max_ever = 0
        first_weight = None
        last_weight = None
        
        # Procesar cada fila
        for row in rows:
            fecha = row[0]
            total_repeticiones = row[1]  # Ahora es INTEGER directamente
            ejercicio_nombre = row[2]
            series_json_raw = row[3]  # JSONB con detalles
            comentarios = row[4]
            rir = row[5]
            
            logger.info(f"Procesando: fecha={fecha}, rep={total_repeticiones}, ejercicio={ejercicio_nombre}")
            logger.info(f"Series JSON: {series_json_raw}")
            logger.info(f"Tipo de series_json: {type(series_json_raw)}")
            
            # Inicializar valores
            max_peso = 0
            avg_peso = 0
            total_volume = 0
            max_e1rm = 0
            
            # Procesar series desde series_json
            series_list = []
            try:
                if series_json_raw:
                    # Convertir de string a objeto si es necesario
                    if isinstance(series_json_raw, str):
                        try:
                            logger.info(f"Convirtiendo series_json desde string")
                            series_json = json.loads(series_json_raw)
                            logger.info("Series JSON parseado correctamente desde string")
                        except json.JSONDecodeError as e:
                            logger.error(f"Error al parsear JSON: {e}")
                            series_json = None
                    else:
                        series_json = series_json_raw
                        logger.info("Usando series_json en formato no-string")
                    
                    logger.info(f"Series JSON parseado: {series_json}")
                    logger.info(f"Tipo de dato series_json: {type(series_json)}")
                    
                    # Asegurar que sea una lista o convertirlo a una
                    if isinstance(series_json, list):
                        series_list = series_json
                        logger.info(f"series_json es una lista con {len(series_list)} elementos")
                    elif isinstance(series_json, dict):
                        series_list = [series_json]
                        logger.info("series_json es un diccionario, lo convertimos a lista de un elemento")
                    else:
                        logger.warning(f"series_json no es lista ni diccionario: {type(series_json)}")
                        
                    # Extraer pesos y repeticiones
                    if series_list:
                        pesos = []
                        reps = []
                        
                        for serie in series_list:
                            if isinstance(serie, dict):
                                peso = serie.get('peso', 0)
                                rep = serie.get('repeticiones', 0)
                                
                                # Validar y convertir tipos si es necesario
                                try:
                                    peso = float(peso) if peso is not None else 0
                                    rep = int(rep) if rep is not None else 0
                                    
                                    if peso > 0 and rep > 0:
                                        pesos.append(peso)
                                        reps.append(rep)
                                except (TypeError, ValueError) as e:
                                    logger.error(f"Error al convertir peso={peso} o rep={rep}: {e}")
                        
                        logger.info(f"Pesos extraídos: {pesos}")
                        logger.info(f"Reps extraídas: {reps}")
                        
                        if pesos:
                            max_peso = max(pesos)
                            avg_peso = sum(pesos) / len(pesos)
                            
                            # Para estadísticas globales
                            if max_peso > peso_max_ever:
                                peso_max_ever = max_peso
                            
                            # Registrar primer y último peso para calcular progreso
                            if first_weight is None:
                                first_weight = max_peso
                            last_weight = max_peso
                            
                            # Calcular volumen (peso × reps)
                            total_volume = sum(peso * rep for peso, rep in zip(pesos, reps))
                            if total_volume > volumen_max_session:
                                volumen_max_session = total_volume
                            
                            # Calcular e1RM 
                            for peso, rep in zip(pesos, reps):
                                if peso > 0 and rep > 0:
                                    e1rm = calculate_e1rm_brzycki(peso, rep)
                                    if e1rm > max_e1rm:
                                        max_e1rm = e1rm
                                    if e1rm > e1rm_max_ever:
                                        e1rm_max_ever = e1rm
            except Exception as e:
                logger.error(f"Error procesando series_json: {e}", exc_info=True)
                # Continuar con los valores por defecto
            
            # Si repeticiones no viene en la entrada o es NULL, calcular a partir de series
            if total_repeticiones is None and series_list:
                total_repeticiones = 0
                for serie in series_list:
                    try:
                        reps = serie.get('repeticiones', 0)
                        total_repeticiones += int(reps) if reps is not None else 0
                    except (TypeError, ValueError) as e:
                        logger.error(f"Error al sumar repeticiones: {e}")
            
            logger.info(f"Valores calculados: max_peso={max_peso}, avg_peso={avg_peso}, total_volume={total_volume}, max_e1rm={max_e1rm}")
            
            # Crear entrada para este registro
            entry = {
                'fecha': fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha),
                'ejercicio': ejercicio_nombre,
                'max_peso': round(max_peso, 2) if max_peso else 0,
                'avg_peso': round(avg_peso, 2) if avg_peso else 0,
                'volumen': round(total_volume, 2) if total_volume else 0,
                'total_reps': total_repeticiones if total_repeticiones is not None else 0,
                'max_e1rm_session': round(max_e1rm, 2) if max_e1rm else 0,
                'comentarios': comentarios,
                'rir': rir
            }
            
            logger.info(f"Entrada procesada: {entry}")
            processed_data.append(entry)
        
        # Calcular porcentaje de progreso
        progress_percent = 0
        if first_weight and last_weight and first_weight > 0:
            logger.info(f"Progreso: {first_weight} -> {last_weight}")
            progress_percent = ((last_weight - first_weight) / first_weight) * 100
            logger.info(f"Porcentaje de progreso calculado: {progress_percent}%")
        
        # Crear resumen
        summary = {
            'total_sesiones': len(processed_data),
            'max_weight_ever': round(peso_max_ever, 2),
            'max_volume_session': round(volumen_max_session, 2),
            'progress_percent': round(progress_percent, 2),
            'max_e1rm_ever': round(e1rm_max_ever, 2)
        }
        
        logger.info(f"Resumen calculado: {summary}")
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
        # Respuesta final
        response = {
            "success": True,
            "message": f"Datos para '{ejercicio}' obtenidos correctamente",
            "datos": processed_data,
            "resumen": summary
        }
        logger.info(f"Devolviendo {len(processed_data)} registros procesados")
        
        return response
    
    except Exception as e:
        logger.error(f"Error DB: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error al obtener datos: {str(e)}",
            "datos": [],
            "resumen": {}
        }


# Ruta para obtener datos del mapa de calor
@router.get("/calendar_heatmap")
async def get_calendar_heatmap(
    year: Optional[int] = Query(None, description="Año para el mapa de calor"),
    user = Depends(get_current_user)
):
    try:
        if not user or not user.get('google_id'):
            raise HTTPException(status_code=401, detail="Autenticación requerida")
        
        google_id = user.get('google_id')
        
        # Si no se especifica año, usar el actual
        if not year:
            year = datetime.now().year
        
        logger.info(f"Obteniendo datos de calendario para usuario Google ID: {google_id}, Año: {year}")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Consulta para obtener conteo de ejercicios por día
        query = """
            SELECT fecha::date as day, COUNT(*) as count
            FROM gym.ejercicios
            WHERE user_id = %s AND EXTRACT(YEAR FROM fecha) = %s
            GROUP BY day
            ORDER BY day
        """
        
        logger.info(f"Consulta de calendario: {query}")
        logger.info(f"Parámetros: {(google_id, year)}")
        
        cur.execute(query, (google_id, year))
        
        # Formatear resultados
        result = []
        for row in cur.fetchall():
            result.append({
                "date": row[0].strftime("%Y-%m-%d"),
                "count": row[1]
            })
        
        logger.info(f"Datos de calendario obtenidos: {len(result)} entradas")
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "message": "Datos de calendario obtenidos correctamente",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Error al obtener datos de calendario: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": []
        }