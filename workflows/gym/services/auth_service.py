import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import string
import json
import datetime
import psycopg2
from google.oauth2 import id_token
from google.auth.transport import requests
from config import DB_CONFIG

# Cargar configuración de Google Auth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5050/google-callback')

def verify_google_token(token):
    """
    Verifica un token de ID de Google y devuelve la información del usuario.
    
    Args:
        token (str): El token de ID de Google a verificar
        
    Returns:
        dict: Información del usuario si el token es válido, None en caso contrario
    """
    try:
        # Verificar el token con Google
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Verificar que el token es para nuestra aplicación
        if idinfo['aud'] != GOOGLE_CLIENT_ID:
            return None
        
        return idinfo
    except Exception as e:
        print(f"Error verificando token de Google: {e}")
        return None

def get_or_create_user(google_id=None, telegram_id=None, email=None, display_name=None, profile_picture=None):
    """
    Obtiene o crea un usuario basado en su ID de Google o Telegram.
    
    Args:
        google_id (str, optional): ID de Google del usuario
        telegram_id (str, optional): ID de Telegram del usuario
        email (str, optional): Email del usuario
        display_name (str, optional): Nombre a mostrar del usuario
        profile_picture (str, optional): URL de la foto de perfil
        
    Returns:
        int: ID interno del usuario
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        user_id = None
        
        # Primero intentar buscar por Google ID si se proporciona
        if google_id:
            cur.execute("SELECT id FROM users WHERE google_id = %s", (google_id,))
            result = cur.fetchone()
            if result:
                user_id = result[0]
        
        # Si no se encontró por Google ID, buscar por Telegram ID
        if not user_id and telegram_id:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
            result = cur.fetchone()
            if result:
                user_id = result[0]
        
        # Si se encontró el usuario, actualizar sus datos si es necesario
        if user_id:
            update_fields = []
            params = []
            
            if google_id and telegram_id:
                # Actualizar el Google ID si el usuario se autenticó primero con Telegram
                update_fields.append("google_id = %s")
                params.append(google_id)
            
            if telegram_id and google_id:
                # Actualizar el Telegram ID si el usuario se autenticó primero con Google
                update_fields.append("telegram_id = %s")
                params.append(telegram_id)
            
            if email:
                update_fields.append("email = %s")
                params.append(email)
            
            if display_name:
                update_fields.append("display_name = %s")
                params.append(display_name)
            
            if profile_picture:
                update_fields.append("profile_picture = %s")
                params.append(profile_picture)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                params.append(user_id)
                cur.execute(query, params)
        else:
            # Si no se encontró el usuario, crearlo
            cur.execute(
                """
                INSERT INTO users (telegram_id, google_id, email, display_name, profile_picture)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (telegram_id, google_id, email, display_name, profile_picture)
            )
            user_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return user_id
    except Exception as e:
        print(f"Error en get_or_create_user: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def migrate_user_data(old_user_id, new_user_id):
    """
    Migra los datos de un usuario a otro (útil cuando se vinculan cuentas).
    
    Args:
        old_user_id (str): ID anterior del usuario (normalmente Telegram ID)
        new_user_id (int): Nuevo ID interno del usuario
        
    Returns:
        bool: True si la migración fue exitosa, False en caso contrario
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Migrar ejercicios
        cur.execute(
            "UPDATE ejercicios SET user_uuid = %s WHERE user_id = %s",
            (new_user_id, old_user_id)
        )
        
        # Migrar rutinas
        cur.execute(
            "UPDATE rutinas SET user_uuid = %s WHERE user_id = %s",
            (new_user_id, old_user_id)
        )
        
        # Migrar tokens de Fitbit
        cur.execute(
            "UPDATE fitbit_tokens SET user_uuid = %s WHERE user_id = %s",
            (new_user_id, old_user_id)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error en migrate_user_data: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def get_user_by_id(user_id):
    """
    Obtiene la información de un usuario por su ID interno.
    
    Args:
        user_id (int): ID interno del usuario
        
    Returns:
        dict: Información del usuario o None si no se encuentra
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT id, telegram_id, google_id, email, display_name, profile_picture,
                  created_at, updated_at
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'telegram_id': result[1],
                'google_id': result[2],
                'email': result[3],
                'display_name': result[4],
                'profile_picture': result[5],
                'created_at': result[6],
                'updated_at': result[7]
            }
        else:
            return None
    except Exception as e:
        print(f"Error en get_user_by_id: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def get_user_id_by_telegram(telegram_id):
    """
    Obtiene el ID interno de un usuario por su ID de Telegram.
    
    Args:
        telegram_id (str): ID de Telegram del usuario
        
    Returns:
        int: ID interno del usuario o None si no se encuentra
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error en get_user_id_by_telegram: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def get_user_id_by_google(google_id):
    """
    Obtiene el ID interno de un usuario por su ID de Google.
    
    Args:
        google_id (str): ID de Google del usuario
        
    Returns:
        int: ID interno del usuario o None si no se encuentra
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE google_id = %s", (google_id,))
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error en get_user_id_by_google: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def generate_link_code(user_id):
    """
    Genera un código único para vincular cuentas de Telegram con Google.
    
    Args:
        user_id (int): ID interno del usuario
        
    Returns:
        str: Código de vinculación generado
    """
    try:
        # Generar código aleatorio de 6 caracteres
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Establecer tiempo de expiración (10 minutos)
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Comprobar si la tabla existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'link_codes'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        # Crear la tabla si no existe
        if not table_exists:
            cur.execute("""
                CREATE TABLE link_codes (
                    code VARCHAR(10) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    used BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Crear índice para búsquedas
            cur.execute("CREATE INDEX idx_link_codes_user_id ON link_codes(user_id)")
        
        # Eliminar códigos previos no usados del mismo usuario
        cur.execute(
            "DELETE FROM link_codes WHERE user_id = %s AND used = FALSE",
            (user_id,)
        )
        
        # Insertar nuevo código
        cur.execute(
            """
            INSERT INTO link_codes (code, user_id, expires_at, used)
            VALUES (%s, %s, %s, FALSE)
            """,
            (code, user_id, expires_at)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return code
    except Exception as e:
        print(f"Error en generate_link_code: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def verify_link_code(code, telegram_id):
    """
    Verifica un código de vinculación y conecta la cuenta de Telegram.
    
    Args:
        code (str): Código de vinculación
        telegram_id (str): ID de Telegram del usuario
        
    Returns:
        bool: True si la vinculación fue exitosa, False en caso contrario
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Buscar código válido y no expirado
        cur.execute(
            """
            SELECT user_id FROM link_codes
            WHERE code = %s AND used = FALSE AND expires_at > NOW()
            """,
            (code.upper(),)
        )
        
        result = cur.fetchone()
        if not result:
            cur.close()
            conn.close()
            return False
        
        user_id = result[0]
        
        # Marcar código como usado
        cur.execute(
            "UPDATE link_codes SET used = TRUE WHERE code = %s",
            (code.upper(),)
        )
        
        # Obtener datos actuales del usuario
        cur.execute(
            """
            SELECT google_id, email, display_name, profile_picture 
            FROM users WHERE id = %s
            """,
            (user_id,)
        )
        
        user_data = cur.fetchone()
        if not user_data:
            conn.commit()
            cur.close()
            conn.close()
            return False
        
        google_id, email, display_name, profile_picture = user_data
        
        # Actualizar o crear usuario con el Telegram ID vinculado
        cur.execute(
            """
            UPDATE users
            SET telegram_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (telegram_id, user_id)
        )
        
        # Migrar datos si es necesario
        existing_user_id = get_user_id_by_telegram(telegram_id)
        if existing_user_id and existing_user_id != user_id:
            # Actualizar referencias en tablas
            tables = ["ejercicios", "rutinas", "fitbit_tokens"]
            for table in tables:
                cur.execute(
                    f"""
                    UPDATE {table} 
                    SET user_uuid = %s 
                    WHERE user_uuid = %s OR user_id = %s
                    """,
                    (user_id, existing_user_id, telegram_id)
                )
            
            # Eliminar el usuario antiguo
            cur.execute("DELETE FROM users WHERE id = %s", (existing_user_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error en verify_link_code: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False