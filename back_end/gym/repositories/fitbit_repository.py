# Archivo: back_end/gym/repositories/fitbit_repository.py

import logging
import json
from datetime import datetime, timezone, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Corregir la importación - cambiar de ...config a ..config (un nivel menos)
from ..config import DB_CONFIG

# Configuración de logging
logger = logging.getLogger(__name__)

class FitbitRepository:
    """Repositorio para gestionar los tokens de Fitbit en la base de datos."""
    
    @staticmethod
    def _execute_db_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Ejecuta una consulta SQL en la base de datos.
        
        Args:
            query (str): Consulta SQL
            params (tuple, optional): Parámetros para la consulta
            fetch_one (bool): Si se debe devolver un solo resultado
            fetch_all (bool): Si se deben devolver todos los resultados
            commit (bool): Si se debe hacer commit de la transacción
            
        Returns:
            result: Resultado de la consulta o None si ocurre un error
        """
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute(query, params)
            
            result = None
            if fetch_one:
                result = cur.fetchone()
            elif fetch_all:
                result = cur.fetchall()
                
            if commit:
                conn.commit()
                
            cur.close()
            conn.close()
            
            return result
            
        except psycopg2.Error as e:
            logger.error(f"Error de base de datos: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            raise
    
    @staticmethod
    def get_tokens(user_id):
        """
        Obtiene los tokens de Fitbit para un usuario.
        
        Args:
            user_id (str): ID del usuario
            
        Returns:
            dict: Información de los tokens o None si no existe
        """
        try:
            query = """
                SELECT client_id, access_token, refresh_token, expires_at
                FROM fitbit_tokens
                WHERE user_uuid = %s
            """
            
            result = FitbitRepository._execute_db_query(query, (str(user_id),), fetch_one=True)
            
            if not result:
                return {
                    "is_connected": False,
                    "message": "Usuario no conectado a Fitbit"
                }
            
            return {
                "is_connected": True,
                "client_id": result['client_id'],
                "access_token": result['access_token'],
                "refresh_token": result['refresh_token'],
                "expires_at": result['expires_at'].isoformat() if result['expires_at'] else None
            }
            
        except Exception as e:
            logger.error(f"Error al obtener tokens de Fitbit: {str(e)}")
            return {
                "is_connected": False,
                "message": f"Error al obtener tokens: {str(e)}"
            }
    
    @staticmethod
    def save_tokens(user_id, tokens_data):
        """
        Guarda o actualiza los tokens de Fitbit para un usuario.
        
        Args:
            user_id (str): ID del usuario
            tokens_data (dict): Datos de los tokens a guardar
            
        Returns:
            bool: True si se guardaron correctamente, False en caso contrario
        """
        try:
            # Primero, asegurarse de que la tabla existe
            create_table_query = """
                CREATE TABLE IF NOT EXISTS fitbit_tokens (
                    id SERIAL PRIMARY KEY,
                    user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    client_id VARCHAR(255) NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_fitbit_user_uuid ON fitbit_tokens(user_uuid);
            """
            
            FitbitRepository._execute_db_query(create_table_query, commit=True)
            
            # Calcular la fecha de expiración
            expires_in = tokens_data.get('expires_in', 28800)  # 8 horas por defecto
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            # Verificar si ya existen tokens para ese usuario
            check_query = "SELECT id FROM fitbit_tokens WHERE user_uuid = %s"
            exists = FitbitRepository._execute_db_query(check_query, (user_id,), fetch_one=True)
            
            if exists:
                # Actualizar tokens existentes
                update_query = """
                    UPDATE fitbit_tokens 
                    SET 
                        access_token = %s,
                        refresh_token = %s,
                        expires_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_uuid = %s
                """
                
                FitbitRepository._execute_db_query(
                    update_query, 
                    (
                        tokens_data.get('access_token'),
                        tokens_data.get('refresh_token'),
                        expires_at,
                        user_id
                    ),
                    commit=True
                )
            else:
                # Insertar nuevos tokens
                insert_query = """
                    INSERT INTO fitbit_tokens 
                    (user_uuid, client_id, access_token, refresh_token, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                """
                
                FitbitRepository._execute_db_query(
                    insert_query, 
                    (
                        user_id,
                        tokens_data.get('client_id', 'default_client'),
                        tokens_data.get('access_token'),
                        tokens_data.get('refresh_token'),
                        expires_at
                    ),
                    commit=True
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar tokens de Fitbit: {str(e)}")
            return False
    
    @staticmethod
    def delete_tokens(user_id):
        """
        Elimina los tokens de Fitbit para un usuario.
        
        Args:
            user_id (str): ID del usuario
            
        Returns:
            bool: True si se eliminaron correctamente, False en caso contrario
        """
        try:
            delete_query = "DELETE FROM fitbit_tokens WHERE user_uuid = %s"
            
            FitbitRepository._execute_db_query(delete_query, (user_id,), commit=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar tokens de Fitbit: {str(e)}")
            return False
    
    @staticmethod
    def save_auth_state(state, expires_in=600):
        """
        Guarda un estado de autenticación temporal.
        
        Args:
            state (str): Estado de autenticación
            expires_in (int): Tiempo de expiración en segundos
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Calcular fecha de expiración
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            # Eliminar estados expirados
            cleanup_query = "DELETE FROM fitbit_auth_temp WHERE expires_at < CURRENT_TIMESTAMP"
            FitbitRepository._execute_db_query(cleanup_query, commit=True)
            
            # Insertar nuevo estado
            insert_query = """
                INSERT INTO fitbit_auth_temp (state, expires_at)
                VALUES (%s, %s)
            """
            
            FitbitRepository._execute_db_query(insert_query, (state, expires_at), commit=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar estado de autenticación: {str(e)}")
            return False
    
    @staticmethod
    def verify_auth_state(state):
        """
        Verifica si un estado de autenticación es válido.
        
        Args:
            state (str): Estado de autenticación
            
        Returns:
            bool: True si el estado es válido, False en caso contrario
        """
        try:
            query = """
                SELECT id FROM fitbit_auth_temp
                WHERE state = %s AND expires_at > CURRENT_TIMESTAMP
            """
            
            result = FitbitRepository._execute_db_query(query, (state,), fetch_one=True)
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error al verificar estado de autenticación: {str(e)}")
            return False