# database_common.py - Configuración y funciones comunes

import os
import sys
import datetime
import json
import traceback
import logging
import psycopg2

# Asumiendo que config está en el directorio padre 'gym' o accesible
try:
    from ..config import DB_CONFIG
except ImportError:
    try:
        from config import DB_CONFIG
    except ImportError:
        logging.critical("No se pudo importar DB_CONFIG. Verifica la estructura del proyecto.")
        DB_CONFIG = {}

# Configuración del logger
logger = logging.getLogger(__name__)

def connect_db():
    """
    Crea una conexión a la base de datos con configuración adecuada.
    
    Returns:
        tuple: (conn, cur) - Conexión y cursor configurados
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO gym, public;")
        return conn, cur
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        raise