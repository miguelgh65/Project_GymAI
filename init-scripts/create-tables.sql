-- Crear tabla ejercicios si no existe
CREATE TABLE IF NOT EXISTS ejercicios (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP,
    ejercicio VARCHAR(255),
    repeticiones JSONB,
    duracion INTEGER,
    user_id INTEGER
);
-- Ejecuta este script SQL en tu base de datos PostgreSQL

-- Tabla para almacenar tokens de Fitbit
CREATE TABLE IF NOT EXISTS fitbit_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla temporal para el proceso de autenticación
CREATE TABLE IF NOT EXISTS fitbit_auth_temp (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE (user_id, client_id)
);

-- Add to init-scripts/create-tables.sql or execute directly

-- Crear tabla para las rutinas de entrenamiento
CREATE TABLE IF NOT EXISTS rutinas (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    ejercicios JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, dia_semana)
);
-- Crear tabla para gestionar usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(255),
    google_id VARCHAR(255),
    email VARCHAR(255),
    display_name VARCHAR(255),
    profile_picture VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(telegram_id),
    UNIQUE(google_id)
);

-- Añadir columna user_uuid a la tabla ejercicios
ALTER TABLE ejercicios 
ADD COLUMN IF NOT EXISTS user_uuid INTEGER REFERENCES users(id);

-- Añadir columna user_uuid a la tabla rutinas
ALTER TABLE rutinas
ADD COLUMN IF NOT EXISTS user_uuid INTEGER REFERENCES users(id);

-- Añadir columna user_uuid a la tabla fitbit_tokens
ALTER TABLE fitbit_tokens
ADD COLUMN IF NOT EXISTS user_uuid INTEGER REFERENCES users(id);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_rutinas_user_id ON rutinas(user_id);
CREATE INDEX IF NOT EXISTS idx_fitbit_tokens_user_id ON fitbit_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_fitbit_auth_temp_user_id ON fitbit_auth_temp(user_id);