# back_end/gym/routes/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
import logging
import psycopg2
import datetime
import json
from ..dependencies import get_current_user
from pydantic import BaseModel
from .. import config
from ..db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(tags=["dashboard"])

# Modelo para respuesta
class DashboardResponse(BaseModel):
    success: bool
    message: str
    datos: Optional[List[Dict[str, Any]]] = None
    ejercicios_disponibles: Optional[List[str]] = None
    resumen: Optional[Dict[str, Any]] = None

# Ruta para obtener lista de ejercicios y estadísticas
@router.get("/api/ejercicios_stats", response_model=DashboardResponse)
async def get_ejercicios_stats(
    user: dict = Depends(get_current_user),
    ejercicio: Optional[str] = None,
    desde: Optional[str] = None,
    hasta: Optional[str] = None
):
    try:
        # Validar que exista usuario
        if not user or not user.get('google_id'):
            raise HTTPException(status_code=401, detail="Autenticación requerida")
        
        # Obtener el ID de Google del usuario
        google_id = user.get('google_id')
        logger.info(f"Obteniendo estadísticas para usuario Google ID: {google_id}")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Si no se especifica un ejercicio, devolver solo la lista de ejercicios disponibles
        if not ejercicio:
            # Obtener solo ejercicios que tienen datos (no null en repeticiones o series_json)
            query = """
                SELECT DISTINCT ejercicio 
                FROM gym.ejercicios 
                WHERE user_id = %s AND (repeticiones IS NOT NULL OR series_json IS NOT NULL)
                ORDER BY ejercicio
            """
            cur.execute(query, (google_id,))
            ejercicios_disponibles = [row[0] for row in cur.fetchall()]
            
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
        
        # Consulta principal - MODIFICADA para adaptarse al nuevo esquema
        data_query = f"""
            SELECT fecha, repeticiones, ejercicio, series_json, comentarios, rir
            FROM gym.ejercicios
            WHERE user_id = %s AND ejercicio = %s{date_filter} AND (repeticiones IS NOT NULL OR series_json IS NOT NULL)
            ORDER BY fecha
        """
        
        cur.execute(data_query, query_params)
        rows = cur.fetchall()
        
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
                        series_json = json.loads(series_json_raw)
                    else:
                        series_json = series_json_raw
                    
                    # Asegurar que sea una lista
                    if isinstance(series_json, list):
                        series_list = series_json
                        
                        # Extraer pesos y repeticiones
                        pesos = [serie.get('peso', 0) for serie in series_list]
                        reps = [serie.get('repeticiones', 0) for serie in series_list]
                        
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
                            total_volume = sum(peso * rep for peso, rep in zip(pesos, reps) if peso is not None and rep is not None)
                            if total_volume > volumen_max_session:
                                volumen_max_session = total_volume
                            
                            # Calcular e1RM estimado (fórmula Epley: peso × (1 + reps/30))
                            e1rms = [peso * (1 + rep/30) for peso, rep in zip(pesos, reps) if peso is not None and rep is not None and rep > 0]
                            if e1rms:
                                max_e1rm = max(e1rms)
                                if max_e1rm > e1rm_max_ever:
                                    e1rm_max_ever = max_e1rm
            except Exception as e:
                logger.error(f"Error procesando series_json: {e}")
                # Continuar con los valores por defecto
            
            # Si repeticiones no viene en la entrada o es NULL, calcular a partir de series
            if total_repeticiones is None and series_list:
                total_repeticiones = sum(serie.get('repeticiones', 0) for serie in series_list if serie.get('repeticiones') is not None)
            
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
            
            processed_data.append(entry)
        
        # Calcular porcentaje de progreso
        progress_percent = 0
        if first_weight and last_weight and first_weight > 0:
            progress_percent = ((last_weight - first_weight) / first_weight) * 100
        
        # Crear resumen
        summary = {
            'total_sesiones': len(processed_data),
            'max_weight_ever': round(peso_max_ever, 2),
            'max_volume_session': round(volumen_max_session, 2),
            'progress_percent': round(progress_percent, 2),
            'max_e1rm_ever': round(e1rm_max_ever, 2)
        }
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Datos para '{ejercicio}' obtenidos correctamente",
            "datos": processed_data,
            "resumen": summary
        }
    
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
@router.get("/api/calendar_heatmap")
async def get_calendar_heatmap(
    year: Optional[int] = Query(None, description="Año para el mapa de calor"),
    user: dict = Depends(get_current_user)
):
    try:
        if not user or not user.get('google_id'):
            raise HTTPException(status_code=401, detail="Autenticación requerida")
        
        google_id = user.get('google_id')
        
        # Si no se especifica año, usar el actual
        if not year:
            year = datetime.datetime.now().year
        
        logger.info(f"Obteniendo datos de calendario para usuario Google ID: {google_id}, Año: {year}")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Consulta para obtener conteo de ejercicios por día
        query = """
            SELECT fecha::date as day, COUNT(*) as count
            FROM gym.ejercicios
            WHERE user_id = %s AND EXTRACT(YEAR FROM fecha) = %s
            GROUP BY day
            ORDER BY day
        """
        
        cur.execute(query, (google_id, year))
        
        # Formatear resultados
        result = []
        for row in cur.fetchall():
            result.append({
                "date": row[0].strftime("%Y-%m-%d"),
                "count": row[1]
            })
        
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