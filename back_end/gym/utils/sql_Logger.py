# back_end/gym/utils/sql_logger.py
import logging
import time
import functools
import inspect
import psycopg2
from typing import Any, Callable

# Configurar logger específico para SQL
logger = logging.getLogger("sql_debug")
logger.setLevel(logging.DEBUG)

# Handler para archivo
file_handler = logging.FileHandler("sql_debug.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Variable para habilitar/deshabilitar debug
SQL_DEBUG_ENABLED = True

def log_sql_query(query: str, params: Any) -> None:
    """Registra una consulta SQL y sus parámetros."""
    if not SQL_DEBUG_ENABLED:
        return
    
    try:
        # Registrar consulta
        logger.debug(f"SQL QUERY: {query}")
        logger.debug(f"PARAMS: {params}")
        
        # Intentar mostrar consulta con parámetros reemplazados (para depuración)
        if params:
            # Intento simple de reemplazo (no manejará todos los casos)
            param_marker = "%s"
            parts = query.split(param_marker)
            if len(parts) > 1:
                filled_query = ""
                for i, part in enumerate(parts):
                    filled_query += part
                    if i < len(params) and i < len(parts) - 1:
                        # Formatear valor según su tipo
                        param = params[i]
                        if param is None:
                            filled_query += "NULL"
                        elif isinstance(param, str):
                            filled_query += f"'{param}'"
                        else:
                            filled_query += str(param)
                
                logger.debug(f"QUERY APROX: {filled_query}")
    except Exception as e:
        logger.error(f"Error al registrar consulta SQL: {str(e)}")

def log_connection(f: Callable) -> Callable:
    """Decorador para registrar conexiones a la base de datos."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not SQL_DEBUG_ENABLED:
            return f(*args, **kwargs)
        
        # Obtener información de la llamada
        caller_frame = inspect.currentframe().f_back
        caller_info = inspect.getframeinfo(caller_frame)
        
        start_time = time.time()
        logger.debug(f"CONEXIÓN INICIADA desde {caller_info.filename}:{caller_info.lineno}")
        
        try:
            result = f(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"CONEXIÓN COMPLETADA en {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"ERROR DE CONEXIÓN después de {elapsed:.2f}ms: {str(e)}")
            raise
    
    return wrapper

def inject_sql_logging():
    """
    Inyecta logging en las funciones clave de psycopg2.
    ADVERTENCIA: Esto modifica el comportamiento global de psycopg2.
    """
    if not SQL_DEBUG_ENABLED:
        return
    
    # Guardar la función original
    original_connect = psycopg2.connect
    
    # Reemplazar con versión con logging
    @functools.wraps(original_connect)
    def connect_with_logging(*args, **kwargs):
        logger.debug(f"NUEVA CONEXIÓN A BD: kwargs={kwargs}")
        
        start_time = time.time()
        conn = original_connect(*args, **kwargs)
        elapsed = (time.time() - start_time) * 1000
        
        logger.debug(f"CONEXIÓN ESTABLECIDA en {elapsed:.2f}ms")
        
        # Guardar funciones originales del cursor
        original_cursor = conn.cursor
        original_commit = conn.commit
        original_rollback = conn.rollback
        
        # Reemplazar método cursor
        @functools.wraps(original_cursor)
        def cursor_with_logging(*cursor_args, **cursor_kwargs):
            logger.debug(f"NUEVO CURSOR: kwargs={cursor_kwargs}")
            cursor = original_cursor(*cursor_args, **cursor_kwargs)
            
            # Guardar función original de ejecución
            original_execute = cursor.execute
            
            # Reemplazar método execute
            @functools.wraps(original_execute)
            def execute_with_logging(query, params=None):
                start_time = time.time()
                log_sql_query(query, params)
                
                try:
                    result = original_execute(query, params)
                    elapsed = (time.time() - start_time) * 1000
                    
                    if hasattr(cursor, 'statusmessage'):
                        logger.debug(f"QUERY COMPLETADA en {elapsed:.2f}ms: {cursor.statusmessage}")
                    else:
                        logger.debug(f"QUERY COMPLETADA en {elapsed:.2f}ms")
                    
                    return result
                except Exception as e:
                    elapsed = (time.time() - start_time) * 1000
                    logger.error(f"ERROR EN QUERY después de {elapsed:.2f}ms: {str(e)}")
                    raise
            
            # Reemplazar método en cursor
            cursor.execute = execute_with_logging
            return cursor
        
        # Reemplazar método commit
        @functools.wraps(original_commit)
        def commit_with_logging():
            start_time = time.time()
            logger.debug("INICIANDO COMMIT")
            
            try:
                result = original_commit()
                elapsed = (time.time() - start_time) * 1000
                logger.debug(f"COMMIT COMPLETADO en {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"ERROR EN COMMIT después de {elapsed:.2f}ms: {str(e)}")
                raise
        
        # Reemplazar método rollback
        @functools.wraps(original_rollback)
        def rollback_with_logging():
            start_time = time.time()
            logger.debug("INICIANDO ROLLBACK")
            
            try:
                result = original_rollback()
                elapsed = (time.time() - start_time) * 1000
                logger.debug(f"ROLLBACK COMPLETADO en {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"ERROR EN ROLLBACK después de {elapsed:.2f}ms: {str(e)}")
                raise
        
        # Reemplazar métodos en conexión
        conn.cursor = cursor_with_logging
        conn.commit = commit_with_logging
        conn.rollback = rollback_with_logging
        
        return conn
    
    # Reemplazar función global
    psycopg2.connect = connect_with_logging
    
    logger.info("Logging SQL inyectado en psycopg2")