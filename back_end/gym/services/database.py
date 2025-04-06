# Archivo: services/database.py (o como se llame tu archivo)

import os
import sys
# Asegúrate que esta ruta es correcta para tu proyecto
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
import json
import traceback
import logging # Añadir logging

import psycopg2
from config import DB_CONFIG
# Asumiendo que schemas está en models/
try:
    from models.schemas import ExerciseData
    from utils.date_utils import get_weekday_name # Necesario para get_today_routine
except ImportError:
    # Stubs si es necesario
    class ExerciseData:
        @staticmethod
        def model_validate(data): return data # Simplificación
        def get_exercises(self): return [] # Simplificación
    def get_weekday_name(day_num): return "Día Desconocido"

logger = logging.getLogger(__name__) # Configura un logger

def insert_into_db(json_data, user_id) -> bool:
    """
    Inserta los datos de ejercicios en la base de datos utilizando solo user_id.
    
    Args:
        json_data (dict): Datos de ejercicios en formato JSON.
        user_id (str): ID de Google del usuario.
        
    Returns:
        bool: True si la inserción fue exitosa, False en caso contrario.
    """
    conn = None
    try:
        logger.debug("\n🔍 Recibido JSON para inserción:")
        # logger.debug(json.dumps(json_data, indent=4, ensure_ascii=False)) # Puede ser muy verboso
        parsed = ExerciseData.model_validate(json_data)
        exercises = parsed.get_exercises()
        logger.info(f"Intentando insertar {len(exercises)} ejercicios para usuario {user_id}.")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Asegurarnos de usar el esquema correcto
        cur.execute("SET search_path TO gym, public;")
        
        for exercise in exercises:
            nombre_ejercicio = exercise.ejercicio
            # Usar la fecha/hora actual de la base de datos es más robusto
            # fecha_hora_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
            logger.debug(f"Preparando inserción para {nombre_ejercicio}")
            
            if exercise.series is not None:
                series_json = json.dumps([s.model_dump() for s in exercise.series])
                
                # Solo insertar con user_id (string)
                user_id_str = str(user_id)
                
                cur.execute(
                    """
                    INSERT INTO gym.ejercicios 
                    (fecha, ejercicio, repeticiones, user_id) 
                    VALUES (NOW(), %s, %s::jsonb, %s)
                    """,
                    (nombre_ejercicio, series_json, user_id_str)
                )
            elif exercise.duracion is not None:
                cur.execute(
                    """
                    INSERT INTO gym.ejercicios 
                    (fecha, ejercicio, duracion, user_id) 
                    VALUES (NOW(), %s, %s, %s)
                    """,
                    (nombre_ejercicio, exercise.duracion, str(user_id))
                )
        
        conn.commit()
        logger.info(f"✅ Inserción exitosa para usuario {user_id}.")
        return True
    except Exception as e:
        logger.error(f"❌ Error al insertar en la base de datos para usuario {user_id}: {e}", exc_info=True)
        # traceback.print_exc() # logger.error con exc_info=True ya lo hace
        if conn:
            conn.rollback()
        return False
    finally:
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
    try:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        # No es necesario formatear a string si la columna fecha es timestamp o date
        
        logger.info(f"Obteniendo logs de los últimos {days} días para usuario {user_id}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Asegurarnos de usar el esquema correcto
        cur.execute("SET search_path TO gym, public;")
        
        # Buscar logs usando el user_id (Google ID)
        query = """
            SELECT fecha, ejercicio, repeticiones, duracion
            FROM gym.ejercicios
            WHERE fecha >= %s AND user_id = %s
            ORDER BY fecha DESC
        """
        cur.execute(query, (cutoff, user_id))
        
        rows = cur.fetchall()
        logger.info(f"Se encontraron {len(rows)} registros de log para usuario {user_id}")

        logs = []
        for row in rows:
            # Intenta obtener 'repeticiones', si no, 'duracion'
            data = row[2] if row[2] is not None else row[3]
            # Podrías querer formatear la fecha aquí si es necesario
            logs.append({
                "fecha": row[0].isoformat() if isinstance(row[0], datetime.datetime) else row[0], # Formato ISO
                "ejercicio": row[1],
                "data": data 
            })
        return logs
    except Exception as e:
        logger.error(f"Error al obtener logs para usuario {user_id}: {e}", exc_info=True)
        # traceback.print_exc()
        return None # Devolver None para indicar error
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                 logger.error(f"Error al cerrar la conexión: {close_error}")

def save_routine(user_id, routine_data):
    """
    Guarda la rutina de un usuario usando su ID.
    
    Args:
        user_id (str): ID del usuario (Google ID).
        routine_data (dict): Datos de la rutina.
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    conn = None
    try:
        logger.info(f"Guardando/Actualizando rutina para usuario ID={user_id}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Asegurarnos de usar el esquema gym
        cur.execute("SET search_path TO gym, public;")
        
        # Usar UPSERT (INSERT ... ON CONFLICT UPDATE) es más eficiente que DELETE + INSERT
        # O simplemente, DELETE e INSERT como lo tienes funciona bien si no hay problemas de concurrencia.
        
        # Eliminar rutina existente (tu método actual)
        cur.execute("DELETE FROM gym.rutinas WHERE user_id = %s", (user_id,))
        logger.debug(f"Rutina antigua eliminada para usuario {user_id}")
        
        # Insertar la nueva rutina
        dias_insertados = 0
        for dia, ejercicios in routine_data.items():
            try:
                dia_semana = int(dia)
                if not 1 <= dia_semana <= 7:
                    logger.warning(f"Clave de día inválida '{dia}' encontrada para usuario {user_id}. Ignorando.")
                    continue
                    
                # Asegurarse que 'ejercicios' es una lista
                if not isinstance(ejercicios, list):
                    logger.warning(f"Formato de ejercicios inválido para día {dia} usuario {user_id}. Se esperaba lista, se recibió {type(ejercicios)}. Ignorando.")
                    continue
                    
                ejercicios_json = json.dumps(ejercicios)
                
                # Usar explícitamente gym.rutinas
                cur.execute(
                    """
                    INSERT INTO gym.rutinas 
                    (user_id, dia_semana, ejercicios) 
                    VALUES (%s, %s, %s::jsonb)
                    """,
                    (user_id, dia_semana, ejercicios_json)
                )
                dias_insertados += 1
            except ValueError:
                logger.warning(f"Clave de día no numérica '{dia}' encontrada para usuario {user_id}. Ignorando.")
                continue
            except (TypeError, json.JSONDecodeError) as json_err:
                logger.error(f"Error al procesar JSON de ejercicios para día {dia} usuario {user_id}: {json_err}")
                # Podrías decidir continuar o fallar toda la operación
                continue 
                
        conn.commit()
        logger.info(f"✅ Rutina guardada/actualizada ({dias_insertados} días) para usuario {user_id}.")
        return True
    except Exception as e:
        logger.error(f"Error al guardar rutina para usuario {user_id}: {e}", exc_info=True)
        # traceback.print_exc()
        if conn:
            conn.rollback() # Asegúrate de hacer rollback en caso de error
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error al cerrar la conexión: {close_error}")

def get_routine(user_id):
    """
    Obtiene la rutina completa de un usuario usando su ID de Google.
    
    Args:
        user_id (str): ID de Google del usuario.
        
    Returns:
        dict or None: Rutina del usuario o None si hay un error.
    """
    conn = None
    try:
        logger.info(f"Obteniendo rutina completa para usuario ID={user_id}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SET search_path TO gym, public;")
        
        cur.execute(
            """
            SELECT dia_semana, ejercicios 
            FROM gym.rutinas 
            WHERE user_id = %s 
            ORDER BY dia_semana
            """,
            (user_id,)
        )
        
        rows = cur.fetchall()
        
        rutina = {}
        for row in rows:
            dia_semana = row[0]
            # Psycopg2 usualmente decodifica JSONB a dict directamente
            if isinstance(row[1], str): 
                 try:
                     ejercicios = json.loads(row[1])
                 except json.JSONDecodeError:
                     logger.warning(f"Error decodificando JSON para día {dia_semana}, usuario {user_id}. Contenido: {row[1]}")
                     ejercicios = [] # O manejar el error de otra forma
            elif isinstance(row[1], list):
                 ejercicios = row[1]
            else:
                 logger.warning(f"Tipo inesperado para ejercicios día {dia_semana}, usuario {user_id}: {type(row[1])}")
                 ejercicios = []
                 
            rutina[str(dia_semana)] = ejercicios
        
        logger.info(f"Rutina obtenida para usuario {user_id} ({len(rutina)} días definidos)")
        return rutina
    
    except Exception as e:
        logger.error(f"Error al obtener rutina para usuario {user_id}: {e}", exc_info=True)
        # traceback.print_exc()
        return None # Devolver None para indicar error
    
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error al cerrar la conexión: {close_error}")

def get_today_routine(user_id):
    """
    Obtiene la rutina del día actual para un usuario y marca los realizados.
    
    Args:
        user_id (str): ID de Google del usuario.
        
    Returns:
        dict: Información de la rutina del día o mensaje de error.
    """
    conn = None
    dia_actual = datetime.datetime.now().isoweekday() # Lunes=1, Domingo=7
    dia_nombre_actual = get_weekday_name(dia_actual)

    try:
        logger.info(f"Obteniendo rutina de hoy ({dia_nombre_actual}) para usuario {user_id}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SET search_path TO gym, public;")
        
        # Obtener la rutina planeada para hoy
        cur.execute(
            """
            SELECT ejercicios 
            FROM gym.rutinas 
            WHERE user_id = %s AND dia_semana = %s
            """,
            (user_id, dia_actual)
        )
        
        row_rutina = cur.fetchone()
        
        if not row_rutina:
            logger.info(f"No hay rutina definida para hoy ({dia_nombre_actual}) para usuario {user_id}")
            return {
                "success": False, # Indicamos que no hay rutina definida
                "message": "No hay rutina definida para hoy.",
                "dia_nombre": dia_nombre_actual,
                "rutina": [] # Devolver lista vacía en lugar de None
            }
        
        # Decodificar ejercicios planeados
        ejercicios_planeados = []
        if isinstance(row_rutina[0], str):
            try:
                ejercicios_planeados = json.loads(row_rutina[0])
            except json.JSONDecodeError:
                 logger.error(f"Error decodificando JSON de rutina para hoy, usuario {user_id}. Contenido: {row_rutina[0]}")
                 # Devolvemos error ya que la rutina existe pero está corrupta
                 raise ValueError("Formato de rutina inválido en la base de datos.")
        elif isinstance(row_rutina[0], list):
             ejercicios_planeados = row_rutina[0]
        else:
            logger.error(f"Tipo inesperado para rutina de hoy, usuario {user_id}: {type(row_rutina[0])}")
            raise ValueError("Tipo de dato de rutina inválido en la base de datos.")
            
        if not isinstance(ejercicios_planeados, list):
             logger.error(f"Ejercicios planeados no son una lista después de procesar para usuario {user_id}. Tipo: {type(ejercicios_planeados)}")
             raise ValueError("Formato de ejercicios planeados inválido.")

        # Obtener los nombres de ejercicios ya registrados hoy
        hoy_fecha = datetime.date.today() # Usar solo la fecha
        
        cur.execute(
            """
            SELECT DISTINCT ejercicio 
            FROM gym.ejercicios 
            WHERE user_id = %s AND fecha::date = %s
            """,
            (user_id, hoy_fecha)
        )
            
        # Usar un set para búsqueda rápida
        ejercicios_realizados_set = {row[0] for row in cur.fetchall()}
        logger.debug(f"Ejercicios realizados hoy por {user_id}: {ejercicios_realizados_set}")
        
        # Construir el resultado marcando realizados
        rutina_resultado = []
        for ejercicio_nombre in ejercicios_planeados:
            # Asegurarnos que el ejercicio es un string
            if isinstance(ejercicio_nombre, str):
                rutina_resultado.append({
                    "ejercicio": ejercicio_nombre,
                    "realizado": ejercicio_nombre in ejercicios_realizados_set
                })
            else:
                logger.warning(f"Elemento no string encontrado en rutina planeada para {user_id}: {ejercicio_nombre}")

        return {
            "success": True,
            "message": "Rutina para hoy obtenida correctamente.",
            "rutina": rutina_resultado,
            "dia_nombre": dia_nombre_actual
        }
    except Exception as e:
        logger.error(f"Error al obtener rutina de hoy para usuario {user_id}: {e}", exc_info=True)
        # traceback.print_exc()
        return {
            "success": False, 
            "message": f"Error interno al obtener la rutina de hoy.",
            "dia_nombre": dia_nombre_actual, # Devolver el día incluso si hay error
            "rutina": [] # Devolver lista vacía en caso de error
        }
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error al cerrar la conexión: {close_error}")


# <<< INICIO NUEVA FUNCIÓN reset_today_routine_status >>>
# <<< INICIO FUNCIÓN reset_today_routine_status CON LOGS DE DEBUG >>>
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
    try:
        hoy_fecha = datetime.date.today() # Obtener solo la fecha de hoy
        logger.info(f"Intentando reiniciar estado de rutina (eliminar logs) para hoy ({hoy_fecha}) - Usuario: {user_id}")

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Asegurarnos de usar el esquema correcto
        cur.execute("SET search_path TO gym, public;")

        # Eliminar TODOS los registros de ejercicios para este usuario y la fecha de HOY
        query = """
            DELETE FROM gym.ejercicios
            WHERE user_id = %s AND fecha::date = %s
        """

        # <<< LOG ANTES DE EJECUTAR DELETE >>>
        logger.info(f"--- DEBUG RESET: Ejecutando DELETE query para user {user_id} en fecha {hoy_fecha}")
        
        cur.execute(query, (user_id, hoy_fecha))

        # rowcount nos dice cuántas filas fueron eliminadas
        num_deleted = cur.rowcount

        # <<< LOG DESPUÉS DE EJECUTAR DELETE >>>
        logger.info(f"--- DEBUG RESET: Filas eliminadas: {num_deleted}")

        conn.commit() # Confirmar la transacción

        logger.info(f"✅ Estado de rutina reiniciado para usuario {user_id}. Se eliminaron {num_deleted} registros de ejercicios de hoy.")
        return True

    except Exception as e:
        logger.error(f"❌ Error al reiniciar estado de rutina para usuario {user_id}: {e}", exc_info=True)
        if conn:
            conn.rollback() # Revertir cambios si hubo error
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"Error al cerrar la conexión tras intentar reiniciar rutina: {close_error}")
# <<< FIN FUNCIÓN reset_today_routine_status CON LOGS DE DEBUG >>>
