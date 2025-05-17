# database_routine_utils.py - Funciones auxiliares para rutinas

import datetime
import logging
import psycopg2
from typing import Dict, Any, List

from .database_common import connect_db

# Importaciones específicas para este módulo
try:
    from utils.date_utils import get_weekday_name
except ImportError:
    logging.warning("Utilizando stub para get_weekday_name (ImportError)")
    def get_weekday_name(day_num): return f"Día {day_num}"

# Logger específico para este módulo
logger = logging.getLogger(__name__)

def get_today_routine(user_id):
    """
    Obtiene la rutina del día actual para un usuario y marca los realizados.

    Args:
        user_id (str): ID del usuario.

    Returns:
        dict: Información de la rutina del día o mensaje de error.
    """
    conn = None
    user_id_str = str(user_id)
    dia_actual = datetime.datetime.now().isoweekday()
    dia_nombre_actual = get_weekday_name(dia_actual)

    try:
        logger.info(f"Obteniendo rutina de hoy ({dia_nombre_actual}) para usuario {user_id_str}")
        conn, cur = connect_db()

        # Query 1: Obtener rutina planeada
        query_rutina = """
            SELECT ejercicios FROM gym.rutinas
            WHERE user_id = %s AND dia_semana = %s
        """
        params_rutina = (user_id_str, dia_actual)
        logger.debug(f"Ejecutando Query 1 (rutina planeada): params = {params_rutina}")
        cur.execute(query_rutina, params_rutina)
        row_rutina = cur.fetchone()

        if not row_rutina:
            logger.info(f"No hay rutina definida para hoy ({dia_nombre_actual}) para usuario {user_id_str}")
            return {"success": False, "message": "No hay rutina definida para hoy.", "dia_nombre": dia_nombre_actual, "rutina": []}

        # Decodificar JSON
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
        params_realizados = (user_id_str, hoy_fecha)
        logger.debug(f"Ejecutando Query 2 (ejercicios realizados): params = {params_realizados}")
        cur.execute(query_realizados, params_realizados)
        ejercicios_realizados_set = {row[0] for row in cur.fetchall()}
        logger.debug(f"Ejercicios realizados hoy por {user_id_str}: {ejercicios_realizados_set}")

        # Construir resultado
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
        user_id (str): ID del usuario.

    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    conn = None
    user_id_str = str(user_id)
    try:
        hoy_fecha = datetime.date.today()
        logger.info(f"Intentando reiniciar estado de rutina (eliminar logs) para hoy ({hoy_fecha}) - Usuario: {user_id_str}")
        conn, cur = connect_db()

        query = """
            DELETE FROM gym.ejercicios
            WHERE user_id = %s AND fecha::date = %s
        """
        logger.info(f"--- DEBUG RESET: Ejecutando DELETE query para user {user_id_str} en fecha {hoy_fecha}")
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