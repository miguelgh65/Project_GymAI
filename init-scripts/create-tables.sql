-- create-tables.sql
-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS gym;

-- Establecer la ruta de búsqueda para encontrar las tablas
SET search_path TO gym, public;

-- Crear tabla para gestionar usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE,
    email VARCHAR(255),
    display_name VARCHAR(255),
    profile_picture VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de códigos de vinculación
CREATE TABLE IF NOT EXISTS link_codes (
    code VARCHAR(10) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    used BOOLEAN DEFAULT FALSE
);

-- Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Crear tabla ejercicios
CREATE TABLE IF NOT EXISTS ejercicios (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP,
    ejercicio VARCHAR(255),
    repeticiones JSONB,
    duracion INTEGER,
    user_id VARCHAR(255),
    user_uuid INTEGER REFERENCES users(id)
);

-- Crear tabla de rutinas
CREATE TABLE IF NOT EXISTS rutinas (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES users(id),
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    ejercicios JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, dia_semana),
    UNIQUE (user_uuid, dia_semana)
);

-- Tabla para tokens de Fitbit
CREATE TABLE IF NOT EXISTS fitbit_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES users(id),
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id),
    UNIQUE (user_uuid)
);

-- Tabla temporal para autenticación de Fitbit
CREATE TABLE IF NOT EXISTS fitbit_auth_temp (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE (user_id, client_id)
);