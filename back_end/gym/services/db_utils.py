# back_end/gym/services/db_utils.py
import logging
import psycopg2
from typing import Optional, List, Dict, Any, Tuple, Union
from ..config import DB_CONFIG

# Configurar logger
logger = logging.getLogger(__name__)

def execute_db_query(query: str, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Función auxiliar para ejecutar consultas a la base de datos.
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros para la consulta SQL
        fetch_one: Si es True, devuelve solo la primera fila del resultado
        fetch_all: Si es True, devuelve todas las filas del resultado
        commit: Si es True, realiza un commit después de ejecutar la consulta
        
    Returns:
        El resultado de la consulta según los parámetros especificados
    """
    conn = None
    cur = None
    result = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Asegurarse que estamos en el esquema correcto
        cur.execute("SET search_path TO nutrition, public")
        
        cur.execute(query, params)

        if commit:
            conn.commit()
            result = cur.rowcount if cur.rowcount is not None else True
        elif fetch_one:
            result = cur.fetchone()
        elif fetch_all:
            result = cur.fetchall()

    except psycopg2.Error as db_err:
        logger.error(f"Error de base de datos: {db_err}", exc_info=True)
        if conn: conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Error inesperado en la base de datos: {e}", exc_info=True)
        if conn: conn.rollback()
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return result