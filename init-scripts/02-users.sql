-- ----------------------------------------
-- ESQUEMA PUBLIC - Usuarios y Autenticación
-- ----------------------------------------

-- Crear tabla para gestionar usuarios (en esquema public)
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE,
    email VARCHAR(255),
    display_name VARCHAR(255),
    profile_picture VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de códigos de vinculación
CREATE TABLE IF NOT EXISTS public.link_codes (
    code VARCHAR(10) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    used BOOLEAN DEFAULT FALSE
);
