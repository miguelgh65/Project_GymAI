# Archivo: back_end/gym/repositories/fitbit_repository.py
import os
import logging
from datetime import datetime, timedelta
import json

import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'postgres_gymdb'),
    'port': os.getenv('DB_PORT', '5432'),
    'options': f'-c search_path={os.getenv("DB_SCHEMA", "gym")},public'
}

class FitbitRepository:
    """Repositorio para acceder y gestionar tokens de Fitbit en la BD."""
    
    @staticmethod
    def _execute_db_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Función auxiliar genérica para ejecutar consultas a la BD.
        
        Args:
            query (str): Consulta SQL
            params (tuple): Parámetros para la consulta
            fetch_one (bool): Devolver una fila
            fetch_all (bool): Devolver todas las filas
            commit (bool): Realizar commit
            
        Returns:
            mixed: Resultado de la consulta según los parámetros
        """
        conn = None
        cur = None
        result = None
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            cur.execute(query, params)
            
            if commit:
                conn.commit()
                result = True
            elif fetch_one:
                result = cur.fetchone()
            elif fetch_all:
                result = cur.fetchall()
                
        except psycopg2.Error as db_err:
            logger.error(f"Error de base de datos: {db_err}")
            if conn: conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Error inesperado en la base de datos: {e}")
            if conn: conn.rollback()
            raise
        finally:
            if cur: cur.close()
            if conn: conn.close()
            
        return result
    
    @staticmethod
    def get_tokens(user_id):
        """
        Obtiene los tokens de Fitbit para un usuario.
        
        Args:
            user_id (str): ID del usuario
            
        Returns:
            dict: Datos de los tokens o None si hay error
        """
        try:
            query = """
                SELECT client_id, access_token, refresh_token, expires_at
                FROM fitbit_tokens
                WHERE user_id = %s
            """
            
            result = FitbitRepository._execute_db_query(query, (str(user_id),), fetch_one=True)
            
            if result:
                client_id, access_token, refresh_token, expires_at = result
                
                expires_at_iso = expires_at.isoformat() if isinstance(expires_at, datetime) else str(expires_at)
                
                return {
                    "is_connected": True,
                    "client_id": client_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at_iso
                }
            else:
                return {"is_connected": False}
                
        except Exception as e:
            logger.exception(f"Error al obtener tokens de Fitbit: {str(e)}")
            return {"is_connected": False, "error": str(e)}
    
    @staticmethod
    def save_tokens(user_id, tokens):
        """
        Guarda o actualiza los tokens de Fitbit en la BD.
        
        Args:
            user_id (str): ID del usuario
            tokens (dict): Tokens de Fitbit
            
        Returns:
            bool: True si se guardaron correctamente, False en caso contrario
        """
        try:
            # Crear tabla si no existe
            create_table_query = """
                CREATE TABLE IF NOT EXISTS fitbit_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL UNIQUE,
                    client_id VARCHAR(255) NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_fitbit_user_id ON fitbit_tokens(user_id);
            """
            
            FitbitRepository._execute_db_query(create_table_query, commit=True)
            
            # Calcular fecha de expiración
            expires_in = tokens.get('expires_in', 28800)  # 8 horas por defecto
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Upsert de tokens
            upsert_query = """
                INSERT INTO fitbit_tokens
                    (user_id, client_id, access_token, refresh_token, expires_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    client_id = EXCLUDED.client_id,
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
            """
            
            params = (
                str(user_id),
                os.getenv('FITBIT_CLIENT_ID'),
                tokens.get('access_token'),
                tokens.get('refresh_token'),
                expires_at
            )
            
            success = FitbitRepository._execute_db_query(upsert_query, params, commit=True)
            
            if success:
                logger.info(f"Tokens de Fitbit guardados para usuario {user_id}")
            
            return success
            
        except Exception as e:
            logger.exception(f"Error al guardar tokens de Fitbit: {str(e)}")
            return False
    
    @staticmethod
    def delete_tokens(user_id):
        """
        Elimina los tokens de Fitbit de un usuario.
        
        Args:
            user_id (str): ID del usuario
            
        Returns:
            bool: True si se eliminaron correctamente, False en caso contrario
        """
        try:
            query = "DELETE FROM fitbit_tokens WHERE user_id = %s"
            
            success = FitbitRepository._execute_db_query(query, (str(user_id),), commit=True)
            
            if success:
                logger.info(f"Tokens de Fitbit eliminados para usuario {user_id}")
            
            return success
            
        except Exception as e:
            logger.exception(f"Error al eliminar tokens de Fitbit: {str(e)}")
            return False