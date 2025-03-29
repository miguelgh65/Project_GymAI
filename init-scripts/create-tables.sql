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

-- Crear índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_rutinas_user_id ON rutinas(user_id);

-- Índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_fitbit_tokens_user_id ON fitbit_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_fitbit_auth_temp_user_id ON fitbit_auth_temp(user_id);