# database_exercise.py - Funciones para gestionar ejercicios

import datetime
import json
import logging
from typing import List, Dict, Optional, Any

from .database_common import connect_db

# Importaciones específicas para este módulo
try:
    from models.schemas import ExerciseData
except ImportError:
    logging.warning("Utilizando stub para ExerciseData (ImportError)")
    class ExerciseData:
        @staticmethod
        def model_validate(data): return data
        def get_exercises(self): return []

# Logger específico para este módulo
logger = logging.getLogger(__name__)

def insert_into_db(json_data, user_id) -> bool:
    """
    Inserta los datos de ejercicios en la base de datos.

    Args:
        json_data (dict): Datos de ejercicios en formato JSON.
        user_id (str): ID del usuario.

    Returns:
        bool: True si la inserción fue exitosa, False en caso contrario.
    """
    conn = None
    # Convertir user_id a string si no lo es ya
    user_id_str = str(user_id)
    
    try:
        # Validar y procesar los datos recibidos
        logger.debug("\n🔍 Preparando datos para inserción en BD")
        parsed = ExerciseData.model_validate(json_data)
        exercises = parsed.get_exercises()
        
        if not exercises:
            logger.warning(f"No hay ejercicios válidos para insertar para usuario {user_id_str}")
            return False
            
        logger.info(f"Preparando inserción de {len(exercises)} ejercicios para usuario {user_id_str}")

        # Conectar a la base de datos
        conn, cur = connect_db()

        # Procesar cada ejercicio
        for exercise in exercises:
            nombre_ejercicio = exercise.ejercicio
            comentarios = exercise.comentarios
            rir = exercise.rir
            
            logger.debug(f"Procesando ejercicio: {nombre_ejercicio}")
            logger.debug(f"  - Comentarios: {comentarios}")
            logger.debug(f"  - RIR general: {rir}")

            if exercise.series is not None:
                # Ejercicio de fuerza con series
                # Calcular repeticiones totales y preparar JSON de series
                series_list = []
                total_reps = 0
                
                for serie in exercise.series:
                    # Sumar repeticiones al total
                    total_reps += serie.repeticiones
                    
                    # Convertir cada Serie a un diccionario simple
                    serie_dict = {
                        "repeticiones": serie.repeticiones,
                        "peso": serie.peso,
                        "rir": serie.rir
                    }
                    series_list.append(serie_dict)
                
                # Convertir la lista a JSON
                series_json = json.dumps(series_list)
                logger.debug(f"  - Series JSON: {series_json}")
                logger.debug(f"  - Total repeticiones: {total_reps}")
                
                # Utilizar 'repeticiones' para almacenar el total de repeticiones
                try:
                    cur.execute(
                        """
                        INSERT INTO gym.ejercicios 
                        (fecha, ejercicio, repeticiones, user_id, comentarios, rir, series_json)
                        VALUES 
                        (NOW(), %s, %s, %s, %s, %s, %s::jsonb)
                        """,
                        (
                            nombre_ejercicio,    # Ejercicio
                            total_reps,          # Total de repeticiones (en columna repeticiones)
                            user_id_str,         # User ID
                            comentarios,         # Comentarios
                            rir,                 # RIR
                            series_json          # JSON de series
                        )
                    )
                    logger.debug(f"  ✅ Ejercicio insertado con éxito: {nombre_ejercicio}, {total_reps} repeticiones totales")
                except Exception as insert_error:
                    logger.error(f"  ❌ Error al insertar ejercicio: {insert_error}")
                    # Intento alternativo si las columnas nuevas aún no existen
                    try:
                        logger.debug("  🔄 Intentando inserción compatible...")
                        cur.execute(
                            """
                            INSERT INTO gym.ejercicios 
                            (fecha, ejercicio, repeticiones, user_id, comentarios, rir)
                            VALUES (NOW(), %s, %s, %s, %s, %s)
                            """,
                            (nombre_ejercicio, total_reps, user_id_str, comentarios, rir)
                        )
                        logger.debug(f"  ✅ Ejercicio insertado (modo compatibilidad)")
                    except Exception as fallback_error:
                        logger.error(f"  ❌ Error en inserción alternativa: {fallback_error}")
                        raise
            elif exercise.duracion is not None:
                # Ejercicio de cardio con duración
                logger.debug(f"  - Duración: {exercise.duracion} minutos")
                
                # Insertar en la base de datos
                cur.execute(
                    """
                    INSERT INTO gym.ejercicios (fecha, ejercicio, duracion, user_id, comentarios, rir)
                    VALUES (NOW(), %s, %s, %s, %s, %s)
                    """,
                    (nombre_ejercicio, exercise.duracion, user_id_str, comentarios, rir)
                )

        # Confirmar la transacción
        conn.commit()
        logger.info(f"✅ Inserción exitosa para usuario {user_id_str}")
        return True
        
    except Exception as e:
        # Registrar error y hacer rollback
        logger.error(f"❌ Error al insertar en la base de datos para usuario {user_id_str}: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return False
        
    finally:
        # Cerrar conexión
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error al cerrar la conexión: {close_error}")

def get_exercise_logs(user_id, days=7):
    """
    Obtiene los logs de ejercicios de un usuario.

    Args:
        user_id (str): ID del usuario.
        days (int): Número de días hacia atrás para obtener logs.

    Returns:
        list or None: Lista de logs o None si hay un error.
    """
    conn = None
    user_id_str = str(user_id)
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        logger.info(f"Obteniendo logs de los últimos {days} días para usuario {user_id_str}")
        conn, cur = connect_db()

        # Consulta actualizada para incluir las nuevas columnas
        try:
            query = """
                SELECT fecha, ejercicio, repeticiones, duracion, comentarios, rir, series_json
                FROM gym.ejercicios
                WHERE fecha >= %s AND user_id = %s
                ORDER BY fecha DESC
            """
            cur.execute(query, (cutoff, user_id_str))
        except Exception as query_error:
            logger.warning(f"Error con la consulta extendida: {query_error}. Intentando consulta compatible...")
            # Consulta compatible por si las columnas nuevas no existen
            query = """
                SELECT fecha, ejercicio, repeticiones, duracion
                FROM gym.ejercicios
                WHERE fecha >= %s AND user_id = %s
                ORDER BY fecha DESC
            """
            cur.execute(query, (cutoff, user_id_str))

        rows = cur.fetchall()
        logger.info(f"Se encontraron {len(rows)} registros de log para usuario {user_id_str}")

        logs = []
        for row in rows:
            data = row[2] if row[2] is not None else row[3]
            log_entry = {
                "fecha": row[0].isoformat() if isinstance(row[0], datetime.datetime) else row[0],
                "ejercicio": row[1],
                "data": data
            }
            
            # Añadir campos adicionales si están disponibles
            if len(row) > 4 and row[4] is not None:
                log_entry["comentarios"] = row[4]
            if len(row) > 5 and row[5] is not None:
                log_entry["rir"] = row[5]
            if len(row) > 6 and row[6] is not None:
                log_entry["series_json"] = row[6]
                
            logs.append(log_entry)
            
        return logs
    except Exception as e:
        logger.error(f"Error al obtener logs para usuario {user_id_str}: {e}", exc_info=True)
        return None
    finally:
        if conn:
            try: conn.close()
            except Exception as close_error: logger.error(f"Error al cerrar la conexión: {close_error}")