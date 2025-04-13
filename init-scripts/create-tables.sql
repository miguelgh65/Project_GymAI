-- ./init-scripts/create-tables.sql (Refactorizado para usar Google ID como FK)

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS gym;

-- Establecer la ruta de búsqueda para encontrar las tablas
SET search_path TO gym, public;

-- -------------------------------------
-- TABLAS PRINCIPALES
-- -------------------------------------

-- Crear tabla para gestionar usuarios (google_id es clave lógica)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY, -- ID interno, NO se usará como FK principal
    telegram_id VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE NOT NULL, -- Clave principal lógica, DEBE ser NOT NULL y UNIQUE
    email VARCHAR(255),
    display_name VARCHAR(255),
    profile_picture VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de códigos de vinculación (Sigue usando users.id interno)
CREATE TABLE IF NOT EXISTS link_codes (
    code VARCHAR(10) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL, -- Vincula al ID interno antes de tener google_id
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    used BOOLEAN DEFAULT FALSE
);

-- Crear tabla ejercicios (Usa google_id)
CREATE TABLE IF NOT EXISTS ejercicios (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE,
    ejercicio VARCHAR(255),
    repeticiones JSONB,
    duracion INTEGER,
    user_id VARCHAR(255) NOT NULL, -- Identificador principal del usuario (Google ID)
    -- user_uuid INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Eliminado
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- Considera añadir un índice en user_id si harás muchas búsquedas por usuario
    -- CREATE INDEX IF NOT EXISTS idx_ejercicios_user_id ON ejercicios(user_id);
);

-- Crear tabla de rutinas (Usa google_id)
CREATE TABLE IF NOT EXISTS rutinas (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL, -- Identificador principal del usuario (Google ID)
    -- user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE, -- Eliminado
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    ejercicios JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, dia_semana) -- Unicidad por Google ID y día
);

-- Tabla para tokens de Fitbit (Usa google_id)
CREATE TABLE IF NOT EXISTS fitbit_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE, -- Identificador principal del usuario (Google ID), debe ser único
    -- user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE, -- Eliminado
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- UNIQUE (user_uuid) -- Eliminado, unique ahora en user_id
);

-- Tabla temporal para autenticación de Fitbit (Sin cambios, no depende del user id)
CREATE TABLE IF NOT EXISTS fitbit_auth_temp (
    id SERIAL PRIMARY KEY,
    state VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Tabla para perfiles nutricionales de usuarios (Usa google_id)
CREATE TABLE IF NOT EXISTS user_nutrition_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE, -- Identificador principal (Google ID), único por usuario
    -- user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL, -- Eliminado
    sex VARCHAR(10) NOT NULL CHECK (sex IN ('male', 'female', 'other')),
    age INTEGER NOT NULL CHECK (age > 0),
    height INTEGER NOT NULL CHECK (height > 0), -- en cm
    weight DECIMAL(5, 2) NOT NULL CHECK (weight > 0), -- en kg
    body_fat_percentage DECIMAL(4, 2) CHECK (body_fat_percentage >= 0 AND body_fat_percentage <= 100),
    activity_level VARCHAR(50) NOT NULL,
    goal VARCHAR(50) NOT NULL,
    bmr DECIMAL(10, 2) NOT NULL,
    bmi DECIMAL(5, 2) NOT NULL,
    daily_calories DECIMAL(10, 2) NOT NULL,
    proteins_grams DECIMAL(10, 2) NOT NULL,
    carbs_grams DECIMAL(10, 2) NOT NULL,
    fats_grams DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- UNIQUE (user_uuid) -- Eliminado, unique ahora en user_id
);

-- Tabla para planes de dieta (Usa google_id)
CREATE TABLE IF NOT EXISTS meal_plans (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL, -- Identificador principal (Google ID)
    -- user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL, -- Eliminado
    plan_name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON meal_plans(user_id); -- Índice útil
);

-- -------------------------------------
-- TABLAS DE DATOS (Ingredientes, Comidas) Y CARGA DESDE CSV
-- -------------------------------------

-- Tabla de ingredientes (Sin cambios, no depende del user id)
CREATE TABLE IF NOT EXISTS ingredients (
    id SERIAL PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL UNIQUE,
    calories INTEGER NOT NULL CHECK (calories >= 0),
    proteins DECIMAL(10, 2) NOT NULL CHECK (proteins >= 0),
    carbohydrates DECIMAL(10, 2) NOT NULL CHECK (carbohydrates >= 0),
    fats DECIMAL(10, 2) NOT NULL CHECK (fats >= 0),
    preparation VARCHAR(50) DEFAULT 'raw',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- *** IMPORTAR DATOS PARA ingredients ***
\copy gym.ingredients (ingredient_name, calories, proteins, carbohydrates, fats) FROM '/docker-entrypoint-initdb.d/ingredients_macros.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',');


-- Tabla de comidas (Sin cambios, no depende del user id)
CREATE TABLE IF NOT EXISTS meals (
    id SERIAL PRIMARY KEY,
    meal_name VARCHAR(255) NOT NULL,
    recipe TEXT,
    ingredients TEXT,
    calories DECIMAL(10, 2) NOT NULL CHECK (calories >= 0),
    proteins DECIMAL(10, 2) NOT NULL CHECK (proteins >= 0),
    carbohydrates DECIMAL(10, 2) NOT NULL CHECK (carbohydrates >= 0),
    fats DECIMAL(10, 2) NOT NULL CHECK (fats >= 0),
    image_url VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- *** IMPORTAR DATOS PARA meals ***
\copy gym.meals (meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url) FROM '/docker-entrypoint-initdb.d/list_meals.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',');


-- Tabla para elementos específicos del plan (comidas asignadas) (Sin cambios, depende de meal_plans.id)
CREATE TABLE IF NOT EXISTS meal_plan_items (
    id SERIAL PRIMARY KEY,
    meal_plan_id INTEGER REFERENCES meal_plans(id) ON DELETE CASCADE NOT NULL,
    meal_id INTEGER REFERENCES meals(id) ON DELETE SET NULL,
    day_of_week INTEGER CHECK (day_of_week BETWEEN 1 AND 7),
    meal_time VARCHAR(50),
    quantity DECIMAL(10, 2) DEFAULT 1.0 CHECK (quantity > 0),
    notes TEXT,
    assigned_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------
-- ÍNDICES FINALES (Adaptados)
-- -------------------------------------
-- Índices para users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Índices para tablas dependientes (usando user_id VARCHAR)
CREATE INDEX IF NOT EXISTS idx_ejercicios_user_id ON ejercicios(user_id);
CREATE INDEX IF NOT EXISTS idx_rutinas_user_id ON rutinas(user_id);
-- CREATE INDEX IF NOT EXISTS idx_fitbit_tokens_user_id ON fitbit_tokens(user_id); -- Ya es UNIQUE
-- CREATE INDEX IF NOT EXISTS idx_user_nutrition_profiles_user_id ON user_nutrition_profiles(user_id); -- Ya es UNIQUE
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON meal_plans(user_id);

-- Índices para tablas de nutrición
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(ingredient_name);
CREATE INDEX IF NOT EXISTS idx_meals_name ON meals(meal_name);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_meal_plan_id ON meal_plan_items(meal_plan_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_meal_id ON meal_plan_items(meal_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_assigned_date ON meal_plan_items(assigned_date);

-- Fin del script