# database_routine.py - Funciones para gestionar rutinas

import datetime
import json
import logging
import psycopg2
from typing import Dict, Any, List, Optional

from .database_common import connect_db

# Importaciones específicas para este módulo
try:
    from utils.date_utils import get_weekday_name
except ImportError:
    logging.warning("Utilizando stub para get_weekday_name (ImportError)")
    def get_weekday_name(day_num): return f"Día {day_num}"

# Logger específico para este módulo
logger = logging.getLogger(__name__)

def save_routine(user_id, routine_data):
    """
    Guarda la rutina de un usuario.

    Args:
        user_id (str): ID del usuario.
        routine_data (dict): Datos de la rutina.

    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    conn = None
    user_id_str = str(user_id)
    try:
        logger.info(f"Guardando/Actualizando rutina para usuario ID={user_id_str}")
        conn, cur = connect_db()

        # Eliminar rutina anterior
        cur.execute("DELETE FROM gym.rutinas WHERE user_id = %s", (user_id_str,))
        logger.debug(f"Rutina antigua eliminada para usuario {user_id_str}")

        dias_insertados = 0
        for dia, ejercicios in routine_data.items():
            try:
                dia_semana = int(dia)
                if not 1 <= dia_semana <= 7: continue
                if not isinstance(ejercicios, list): continue
                ejercicios_json = json.dumps(ejercicios)

                # Insertar día de rutina
                cur.execute(
                    """
                    INSERT INTO gym.rutinas (user_id, dia_semana, ejercicios)
                    VALUES (%s, %s, %s::jsonb)
                    """,
                    (user_id_str, dia_semana, ejercicios_json)
                )
                dias_insertados += 1
            except ValueError: 
                logger.warning(f"Clave día no numérica '{dia}', user {user_id_str}. Ignorando.") 
                continue
            except (TypeError, json.JSONDecodeError) as json_err: 
                logger.error(f"Error JSON día {dia}, user {user_id_str}: {json_err}")
                continue

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
    Obtiene la rutina completa de un usuario.

    Args:
        user_id (str): ID del usuario.

    Returns:
        dict or None: Rutina del usuario o None si hay un error.
    """
    conn = None
    user_id_str = str(user_id)
    try:
        logger.info(f"Obteniendo rutina completa para usuario ID={user_id_str}")
        conn, cur = connect_db()

        cur.execute(
            """
            SELECT dia_semana, ejercicios FROM gym.rutinas
            WHERE user_id = %s ORDER BY dia_semana
            """,
            (user_id_str,)
        )

        rows = cur.fetchall()
        rutina = {}
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