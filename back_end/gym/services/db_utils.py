# back_end/gym/services/db_utils.py
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Tuple, Optional, Union
from back_end.gym.config import DB_CONFIG

# Configurar logger
logger = logging.getLogger(__name__)

def execute_db_query(
    query: str,
    params: Union[Tuple, List] = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
    commit: bool = True,
    as_dict: bool = False,
    use_transaction: bool = False
) -> Any:
    """
    Ejecuta una consulta SQL en la base de datos con mejor manejo de transacciones.
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros para la consulta
        fetch_one: Si es True, retorna solo un resultado
        fetch_all: Si es True, retorna todos los resultados
        commit: Si es True, hace commit de la transacción
        as_dict: Si es True, retorna resultados como diccionarios
        use_transaction: Si es True, inicia una transacción explícita
        
    Returns:
        Resultado de la consulta según los parámetros especificados
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Usar cursor de diccionario si se solicita
        cursor_factory = RealDictCursor if as_dict else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        
        # Establecer esquema de nutrición para consultas relacionadas
        if 'meal_plans' in query or 'ingredients' in query or 'meals' in query or 'meal_plan_items' in query or 'meal_ingredients' in query:
            cur.execute("SET search_path TO nutrition, public")
        
        # Iniciar transacción explícita si se solicita
        if use_transaction:
            cur.execute("BEGIN")
            logger.debug("Iniciando transacción explícita")
        
        # Ejecutar la consulta con parámetros
        logger.debug(f"Ejecutando consulta: {query}")
        logger.debug(f"Parámetros: {params}")
        
        cur.execute(query, params)
        
        # Para comandos especiales como COMMIT o ROLLBACK
        if query.upper() in ("COMMIT", "ROLLBACK"):
            if query.upper() == "COMMIT":
                conn.commit()
            else:
                conn.rollback()
            return True
        
        # Obtener resultados según lo solicitado
        if fetch_one:
            result = cur.fetchone()
        elif fetch_all:
            result = cur.fetchall()
        else:
            # Para consultas que no retornan datos (INSERT, UPDATE, DELETE)
            result = cur.rowcount > 0
        
        # Commit si se solicita y no es parte de una transacción más grande
        if commit and not use_transaction:
            conn.commit()
            
        return result
    except Exception as e:
        # Rollback en caso de error si no se maneja por fuera
        if conn and not use_transaction:
            conn.rollback()
        logger.error(f"Error en la consulta SQL: {str(e)}")
        logger.error(f"Consulta: {query}")
        logger.error(f"Parámetros: {params}")
        raise
    finally:
        # Cerrar cursor y conexión
        if cur:
            cur.close()
        if conn and not use_transaction:
            conn.close()