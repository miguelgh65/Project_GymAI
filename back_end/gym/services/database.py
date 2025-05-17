# Archivo: services/database.py (CORREGIDO v2)

import os
import sys
import datetime
import json
import traceback
import logging
import psycopg2

# Asumiendo que config está en el directorio padre 'gym' o accesible
try:
    from ..config import DB_CONFIG # Usar .. si config.py está un nivel arriba
except ImportError:
    # Fallback si la estructura es diferente
    try:
        from config import DB_CONFIG
    except ImportError:
        logging.critical("No se pudo importar DB_CONFIG. Verifica la estructura del proyecto.")
        DB_CONFIG = {} # Placeholder para evitar más errores

# Asumiendo que schemas está en models/ y utils en utils/ al mismo nivel que services/ o accesible
try:
    # Ajusta la ruta si es necesario (ej: from ..models.schemas import ...)
    from models.schemas import ExerciseData
    # Ajusta la ruta si es necesario (ej: from ..utils.date_utils import ...)
    from utils.date_utils import get_weekday_name # Necesario para get_today_routine
except ImportError:
    # Stubs si es necesario
    logging.warning("Stubs activados para ExerciseData y/o get_weekday_name debido a ImportError.")
    class ExerciseData:
        @staticmethod
        def model_validate(data): return data # Simplificación
        def get_exercises(self): return [] # Simplificación
    def get_weekday_name(day_num): return "Día Desconocido"

logger = logging.getLogger(__name__) # Configura un logger

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
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO gym, public;")

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
                series_json = json.dumps([s.model_dump() for s in exercise.series])
                logger.debug(f"  - Series: {series_json}")
                
                # Insertar en la base de datos
                cur.execute(
                    """
                    INSERT INTO gym.ejercicios (fecha, ejercicio, repeticiones, user_id, comentarios, rir)
                    VALUES (NOW(), %s, %s::jsonb, %s, %s, %s)
                    """,
                    (nombre_ejercicio, series_json, user_id_str, comentarios, rir)
                )
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
    Obtiene los logs de ejercicios de un usuario usando su ID de Google.

    Args:
        user_id (str): ID de Google del usuario.
        days (int): Número de días hacia atrás para obtener logs.

    Returns:
        list or None: Lista de logs o None si hay un error.
    """
    conn = None
    # --- CORRECCIÓN: Convertir a string aquí ---
    user_id_str = str(user_id)
    # --- FIN CORRECCIÓN ---
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        logger.info(f"Obteniendo logs de los últimos {days} días para usuario {user_id_str}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO gym, public;")

        query = """
            SELECT fecha, ejercicio, repeticiones, duracion
            FROM gym.ejercicios
            WHERE fecha >= %s AND user_id = %s
            ORDER BY fecha DESC
        """
        # Pasar user_id_str (string) a la consulta
        cur.execute(query, (cutoff, user_id_str))

        rows = cur.fetchall()
        logger.info(f"Se encontraron {len(rows)} registros de log para usuario {user_id_str}")

        logs = []
        for row in rows:
            data = row[2] if row[2] is not None else row[3]
            logs.append({
                "fecha": row[0].isoformat() if isinstance(row[0], datetime.datetime) else row[0],
                "ejercicio": row[1],
                "data": data
            })
        return logs
    except Exception as e:
        logger.error(f"Error al obtener logs para usuario {user_id_str}: {e}", exc_info=True)
        return None
    finally:
        if conn:
            try: conn.close()
            except Exception as close_error: logger.error(f"Error al cerrar la conexión: {close_error}")

def save_routine(user_id, routine_data):
    """
    Guarda la rutina de un usuario usando su ID de Google.

    Args:
        user_id (str): ID de Google del usuario.
        routine_data (dict): Datos de la rutina.

    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    conn = None
    # --- CORRECCIÓN: Convertir a string aquí ---
    user_id_str = str(user_id)
    # --- FIN CORRECCIÓN ---
    try:
        logger.info(f"Guardando/Actualizando rutina para usuario ID={user_id_str}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO gym, public;")

        # Pasar user_id_str (string) al DELETE
        cur.execute("DELETE FROM gym.rutinas WHERE user_id = %s", (user_id_str,))
        logger.debug(f"Rutina antigua eliminada para usuario {user_id_str}")

        dias_insertados = 0
        for dia, ejercicios in routine_data.items():
            try:
                dia_semana = int(dia)
                if not 1 <= dia_semana <= 7: continue
                if not isinstance(ejercicios, list): continue
                ejercicios_json = json.dumps(ejercicios)

                # Pasar user_id_str (string) al INSERT
                cur.execute(
                    """
                    INSERT INTO gym.rutinas (user_id, dia_semana, ejercicios)
                    VALUES (%s, %s, %s::jsonb)
                    """,
                    (user_id_str, dia_semana, ejercicios_json)
                )
                dias_insertados += 1
            # ... (manejo de errores de día/json sin cambios) ...
            except ValueError: logger.warning(f"Clave día no numérica '{dia}', user {user_id_str}. Ignorando."); continue
            except (TypeError, json.JSONDecodeError) as json_err: logger.error(f"Error JSON día {dia}, user {user_id_str}: {json_err}"); continue

        conn.commit()
        logger.info(f"✅ Rutina guardada/actualizada ({dias_insertados} días) para usuario {user_id_str}.")
        return True
    except Exception as e:
        logger.error(f"Error al guardar rutina para usuario {user_id_str}: {e}", exc_info=True)
        if conn: conn.rollback()
        return False
    finally:
        if conn:
            try: conn.close()
            except Exception as close_error: logger.error(f"Error al cerrar la conexión: {close_error}")

def get_routine(user_id):
    """
    Obtiene la rutina completa de un usuario usando su ID de Google.

    Args:
        user_id (str): ID de Google del usuario.

    Returns:
        dict or None: Rutina del usuario o None si hay un error.
    """
    conn = None
    # --- CORRECCIÓN: Convertir a string aquí ---
    user_id_str = str(user_id)
    # --- FIN CORRECCIÓN ---
    try:
        logger.info(f"Obteniendo rutina completa para usuario ID={user_id_str}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO gym, public;")

        # Pasar user_id_str (string) a la consulta
        cur.execute(
            """
            SELECT dia_semana, ejercicios FROM gym.rutinas
            WHERE user_id = %s ORDER BY dia_semana
            """,
            (user_id_str,)
        )

        rows = cur.fetchall()
        rutina = {}
        # ... (lógica de procesamiento de resultados sin cambios) ...
        for row in rows:
            dia_semana = row[0]
            ejercicios = []
            if isinstance(row[1], str):
                 try: ejercicios = json.loads(row[1])
                 except json.JSONDecodeError: logger.warning(f"Error JSON rutina día {dia_semana}, user {user_id_str}.")
            elif isinstance(row[1], list): ejercicios = row[1]
            else: logger.warning(f"Tipo inesperado rutina día {dia_semana}, user {user_id_str}: {type(row[1])}")
            if isinstance(ejercicios, list): rutina[str(dia_semana)] = ejercicios
            else: rutina[str(dia_semana)] = []

        logger.info(f"Rutina obtenida para usuario {user_id_str} ({len(rutina)} días definidos)")
        return rutina
    except Exception as e:
        logger.error(f"Error al obtener rutina para usuario {user_id_str}: {e}", exc_info=True)
        return None
    finally:
        if conn:
            try: conn.close()
            except Exception as close_error: logger.error(f"Error al cerrar la conexión: {close_error}")

def get_today_routine(user_id):
    """
    Obtiene la rutina del día actual para un usuario y marca los realizados.

    Args:
        user_id (str): ID de Google del usuario.

    Returns:
        dict: Información de la rutina del día o mensaje de error.
    """
    conn = None
    # --- CORRECCIÓN: Convertir a string aquí ---
    user_id_str = str(user_id)
    # --- FIN CORRECCIÓN ---
    dia_actual = datetime.datetime.now().isoweekday()
    dia_nombre_actual = get_weekday_name(dia_actual)

    try:
        logger.info(f"Obteniendo rutina de hoy ({dia_nombre_actual}) para usuario {user_id_str}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO gym, public;")

        # Query 1: Obtener rutina planeada
        query_rutina = """
            SELECT ejercicios FROM gym.rutinas
            WHERE user_id = %s AND dia_semana = %s
        """
        params_rutina = (user_id_str, dia_actual) # Pasar user_id_str (string)
        logger.debug(f"Ejecutando Query 1 (rutina planeada): params = {params_rutina}")
        cur.execute(query_rutina, params_rutina)
        row_rutina = cur.fetchone()

        if not row_rutina:
            logger.info(f"No hay rutina definida para hoy ({dia_nombre_actual}) para usuario {user_id_str}")
            return {"success": False, "message": "No hay rutina definida para hoy.", "dia_nombre": dia_nombre_actual, "rutina": []}

        # Decodificar JSON (sin cambios)
        ejercicios_planeados = []
        if isinstance(row_rutina[0], str):
            try: ejercicios_planeados = json.loads(row_rutina[0])
            except json.JSONDecodeError: raise ValueError("Formato de rutina inválido en BD.")
        elif isinstance(row_rutina[0], list):
            ejercicios_planeados = row_rutina[0]
        else: raise ValueError("Tipo de dato de rutina inválido en BD.")
        if not isinstance(ejercicios_planeados, list): raise ValueError("Formato de ejercicios planeados inválido.")

        # Query 2: Obtener ejercicios realizados
        hoy_fecha = datetime.date.today()
        query_realizados = """
            SELECT DISTINCT ejercicio FROM gym.ejercicios
            WHERE user_id = %s AND fecha::date = %s
        """
        params_realizados = (user_id_str, hoy_fecha) # Pasar user_id_str (string)
        logger.debug(f"Ejecutando Query 2 (ejercicios realizados): params = {params_realizados}")
        cur.execute(query_realizados, params_realizados)
        ejercicios_realizados_set = {row[0] for row in cur.fetchall()}
        logger.debug(f"Ejercicios realizados hoy por {user_id_str}: {ejercicios_realizados_set}")

        # Construir resultado (sin cambios)
        rutina_resultado = []
        for ejercicio_nombre in ejercicios_planeados:
            if isinstance(ejercicio_nombre, str):
                 rutina_resultado.append({"ejercicio": ejercicio_nombre, "realizado": ejercicio_nombre in ejercicios_realizados_set})
            else: logger.warning(f"Elemento no string en rutina planeada para {user_id_str}: {ejercicio_nombre}")

        return {"success": True, "message": "Rutina para hoy obtenida correctamente.", "rutina": rutina_resultado, "dia_nombre": dia_nombre_actual}

    except psycopg2.Error as db_err:
        logger.error(f"Error DB al obtener rutina para user {user_id_str} día {dia_actual}: {db_err}", exc_info=True)
        return {"success": False, "message": f"Error DB: {db_err}", "dia_nombre": dia_nombre_actual, "rutina": []}
    except Exception as e:
        logger.error(f"Error general al obtener rutina de hoy para user {user_id_str}: {e}", exc_info=True)
        return {"success": False, "message": f"Error interno al obtener la rutina de hoy.", "dia_nombre": dia_nombre_actual, "rutina": []}
    finally:
        if conn:
            try: conn.close()
            except Exception as close_error: logger.error(f"Error al cerrar la conexión: {close_error}")


def reset_today_routine_status(user_id: str) -> bool:
    """
    Reinicia el estado de 'realizado' para la rutina de hoy de un usuario.
    Esto se logra eliminando los registros de ejercicios para el día actual.

    Args:
        user_id (str): ID de Google del usuario.

    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    conn = None
    # --- CORRECCIÓN: Convertir a string aquí ---
    user_id_str = str(user_id)
    # --- FIN CORRECCIÓN ---
    try:
        hoy_fecha = datetime.date.today()
        logger.info(f"Intentando reiniciar estado de rutina (eliminar logs) para hoy ({hoy_fecha}) - Usuario: {user_id_str}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO gym, public;")

        query = """
            DELETE FROM gym.ejercicios
            WHERE user_id = %s AND fecha::date = %s
        """
        logger.info(f"--- DEBUG RESET: Ejecutando DELETE query para user {user_id_str} en fecha {hoy_fecha}")
        # Pasar user_id_str (string) al DELETE
        cur.execute(query, (user_id_str, hoy_fecha))

        num_deleted = cur.rowcount
        logger.info(f"--- DEBUG RESET: Filas eliminadas: {num_deleted}")
        conn.commit()
        logger.info(f"✅ Estado de rutina reiniciado para usuario {user_id_str}. Se eliminaron {num_deleted} registros de ejercicios de hoy.")
        return True
    except Exception as e:
        logger.error(f"❌ Error al reiniciar estado de rutina para usuario {user_id_str}: {e}", exc_info=True)
        if conn: conn.rollback()
        return False
    finally:
        if conn:
            try: conn.close()
            except Exception as close_error: logger.error(f"Error al cerrar la conexión tras intentar reiniciar rutina: {close_error}")