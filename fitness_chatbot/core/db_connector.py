import logging
import psycopg2
import psycopg2.extras
import os
from typing import Any, Dict, List, Optional, Tuple, Union

# Configurar logger
logger = logging.getLogger("fitness_chatbot")

class DatabaseConnector:
    """Conector para la base de datos PostgreSQL"""
    
    @staticmethod
    def get_db_config() -> Dict[str, str]:
        """
        Obtiene la configuración de la base de datos desde variables de entorno.
        
        Returns:
            Dict con configuración de conexión
        """
        return {
            'dbname': os.getenv('DB_NAME', 'gymdb'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'options': f"-c search_path={os.getenv('DB_SCHEMA', 'gym')},nutrition,public"
        }
    
    @staticmethod
    def get_connection():
        """
        Crea y devuelve una conexión a la base de datos.
        
        Returns:
            Conexión a PostgreSQL
        
        Raises:
            ConnectionError: Si hay un error de conexión
        """
        try:
            config = DatabaseConnector.get_db_config()
            conn = psycopg2.connect(**config)
            return conn
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {str(e)}")
            raise ConnectionError(f"Error conectando a PostgreSQL: {str(e)}")
    
    @staticmethod
    async def execute_query(
        query: str, 
        params: Optional[Union[Tuple, List, Dict]] = None, 
        fetch_all: bool = False, 
        fetch_one: bool = False
    ) -> Any:
        """
        Ejecuta una consulta SQL con manejo adecuado de conexión.
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            fetch_all: Si es True, devuelve todas las filas
            fetch_one: Si es True, devuelve una sola fila
        
        Returns:
            Resultados de la consulta o True si se ejecutó correctamente
        
        Raises:
            Exception: Si hay un error al ejecutar la consulta
        """
        conn = None
        try:
            conn = DatabaseConnector.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, params or ())
                
                if fetch_all:
                    rows = cursor.fetchall()
                    # Convertir a lista de diccionarios para facilitar su uso
                    return [dict(row) for row in rows]
                elif fetch_one:
                    row = cursor.fetchone()
                    # Devolver como diccionario si hay resultado
                    return dict(row) if row else None
                
                conn.commit()
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error ejecutando consulta: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise Exception(f"Error ejecutando consulta: {str(e)}")
        finally:
            if conn:
                conn.close()