-- ----------------------------------------
-- ESQUEMA CONFIG - Integración con APIs externas
-- ----------------------------------------

-- Tabla para tokens de Fitbit
CREATE TABLE IF NOT EXISTS config.fitbit_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_uuid)
);

-- Tabla temporal para autenticación de Fitbit
CREATE TABLE IF NOT EXISTS config.fitbit_auth_temp (
    id SERIAL PRIMARY KEY,
    state VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
