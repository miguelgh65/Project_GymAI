-- ----------------------------------------
-- ESQUEMA GYM - Ejercicios y Rutinas
-- ----------------------------------------

-- Tabla de ejercicios
CREATE TABLE IF NOT EXISTS gym.ejercicios (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE,
    ejercicio VARCHAR(255),
    repeticiones JSONB,
    duracion INTEGER,
    user_id VARCHAR(255),
    user_uuid INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de rutinas
CREATE TABLE IF NOT EXISTS gym.rutinas (
    id SERIAL PRIMARY KEY,
    user_uuid INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    ejercicios JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_uuid, dia_semana)
);
