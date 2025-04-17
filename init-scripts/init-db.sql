-- ./back_end/gym/init-db.sql (Versión FINAL corregida - 2025-04-18)

-- Crear esquemas si no existen
CREATE SCHEMA IF NOT EXISTS gym;
CREATE SCHEMA IF NOT EXISTS nutrition; -- Añadido schema nutrition

-- Establecer la ruta de búsqueda para encontrar las tablas
-- Añadido nutrition al search_path, priorizado
SET search_path TO nutrition, gym, public;

-- -------------------------------------
-- TABLAS PRINCIPALES (Schema 'gym' o 'public' por defecto)
-- -------------------------------------

-- Crear tabla para gestionar usuarios
CREATE TABLE IF NOT EXISTS users ( -- Asumiendo schema 'gym' o 'public'
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    profile_picture VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de códigos de vinculación
CREATE TABLE IF NOT EXISTS link_codes ( -- Asumiendo schema 'gym' o 'public'
    code VARCHAR(10) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    used BOOLEAN DEFAULT FALSE
);

-- Crear tabla ejercicios
CREATE TABLE IF NOT EXISTS ejercicios ( -- Asumiendo schema 'gym' o 'public'
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE,
    ejercicio VARCHAR(255),
    repeticiones JSONB,
    duracion INTEGER,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de rutinas
CREATE TABLE IF NOT EXISTS rutinas ( -- Asumiendo schema 'gym' o 'public'
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    ejercicios JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, dia_semana)
);

-- Tabla para tokens de Fitbit
CREATE TABLE IF NOT EXISTS fitbit_tokens ( -- Asumiendo schema 'gym' o 'public'
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla temporal para autenticación de Fitbit
CREATE TABLE IF NOT EXISTS fitbit_auth_temp ( -- Asumiendo schema 'gym' o 'public'
    id SERIAL PRIMARY KEY,
    state VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- -------------------------------------
-- TABLAS DE NUTRICIÓN (Schema 'nutrition')
-- -------------------------------------

-- Tabla para perfiles nutricionales de usuarios
CREATE TABLE IF NOT EXISTS nutrition.user_nutrition_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    sex VARCHAR(10) NOT NULL CHECK (sex IN ('male', 'female', 'other')),
    age INTEGER NOT NULL CHECK (age > 0),
    height INTEGER NOT NULL CHECK (height > 0), -- en cm
    weight DECIMAL(5, 2) NOT NULL CHECK (weight > 0), -- en kg
    body_fat_percentage DECIMAL(4, 2) CHECK (body_fat_percentage IS NULL OR (body_fat_percentage >= 0 AND body_fat_percentage <= 100)), -- Permitir NULL
    activity_level VARCHAR(50) NOT NULL,
    goal VARCHAR(50) NOT NULL,
    bmr DECIMAL(10, 2),
    bmi DECIMAL(5, 2),
    daily_calories DECIMAL(10, 2),
    proteins_grams DECIMAL(10, 2),
    carbs_grams DECIMAL(10, 2),
    fats_grams DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para planes de dieta (con columnas target/goal)
CREATE TABLE IF NOT EXISTS nutrition.meal_plans (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    plan_name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    target_calories INTEGER DEFAULT NULL CHECK (target_calories IS NULL OR target_calories >= 0),
    target_protein_g DECIMAL(10, 2) DEFAULT NULL CHECK (target_protein_g IS NULL OR target_protein_g >= 0),
    target_carbs_g DECIMAL(10, 2) DEFAULT NULL CHECK (target_carbs_g IS NULL OR target_carbs_g >= 0),
    target_fat_g DECIMAL(10, 2) DEFAULT NULL CHECK (target_fat_g IS NULL OR target_fat_g >= 0),
    goal VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de ingredientes
CREATE TABLE IF NOT EXISTS nutrition.ingredients (
    id SERIAL PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL UNIQUE,
    calories INTEGER DEFAULT 0 CHECK (calories >= 0),
    proteins DECIMAL(10, 2) DEFAULT 0 CHECK (proteins >= 0),
    carbohydrates DECIMAL(10, 2) DEFAULT 0 CHECK (carbohydrates >= 0),
    fats DECIMAL(10, 2) DEFAULT 0 CHECK (fats >= 0),
    preparation VARCHAR(50) DEFAULT 'raw',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- *** IMPORTAR DATOS PARA ingredients ***
\copy nutrition.ingredients (ingredient_name, calories, proteins, carbohydrates, fats) FROM '/docker-entrypoint-initdb.d/ingredients_macros.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',');


-- Tabla de comidas
CREATE TABLE IF NOT EXISTS nutrition.meals (
    id SERIAL PRIMARY KEY,
    meal_name VARCHAR(255) NOT NULL,
    recipe TEXT,
    ingredients TEXT,
    calories DECIMAL(10, 2) DEFAULT 0 CHECK (calories >= 0),
    proteins DECIMAL(10, 2) DEFAULT 0 CHECK (proteins >= 0),
    carbohydrates DECIMAL(10, 2) DEFAULT 0 CHECK (carbohydrates >= 0),
    fats DECIMAL(10, 2) DEFAULT 0 CHECK (fats >= 0),
    image_url VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- *** IMPORTAR DATOS PARA meals ***
\copy nutrition.meals (meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url) FROM '/docker-entrypoint-initdb.d/list_meals.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',');

-- Tabla para relacionar comidas con ingredientes específicos
CREATE TABLE IF NOT EXISTS nutrition.meal_ingredients (
   id SERIAL PRIMARY KEY,
   meal_id INT NOT NULL REFERENCES nutrition.meals(id) ON DELETE CASCADE,
   ingredient_id INT NOT NULL REFERENCES nutrition.ingredients(id) ON DELETE CASCADE,
   quantity DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   UNIQUE(meal_id, ingredient_id)
);


-- Tabla para elementos específicos del plan (comidas asignadas)
-- >>> VERSIÓN FINALMENTE CORREGIDA <<<
CREATE TABLE IF NOT EXISTS nutrition.meal_plan_items (
    id SERIAL PRIMARY KEY,
    meal_plan_id INTEGER REFERENCES nutrition.meal_plans(id) ON DELETE CASCADE NOT NULL,
    meal_id INTEGER REFERENCES nutrition.meals(id) ON DELETE SET NULL,
    plan_date DATE, -- Columna añadida
    day_of_week INTEGER CHECK (day_of_week BETWEEN 1 AND 7), -- Mantener si aún es útil
    meal_type VARCHAR(50), -- Columna renombrada
    quantity DECIMAL(10, 2) DEFAULT 100.0 CHECK (quantity > 0),
    unit VARCHAR(20) DEFAULT 'g', -- Columna añadida
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- >>> Fin Definición Corregida <<<

-- -------------------------------------
-- ÍNDICES FINALES (Adaptados)
-- -------------------------------------
-- Índices para users (asumiendo schema 'gym' o 'public')
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Índices para tablas dependientes (usando user_id VARCHAR)
-- Ajustar schema si es necesario
CREATE INDEX IF NOT EXISTS idx_ejercicios_user_id ON ejercicios(user_id);
CREATE INDEX IF NOT EXISTS idx_rutinas_user_id ON rutinas(user_id);
CREATE INDEX IF NOT EXISTS idx_user_nutrition_profiles_user_id ON nutrition.user_nutrition_profiles(user_id); -- Ya es UNIQUE
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON nutrition.meal_plans(user_id);

-- Índices para tablas de nutrición (Schema 'nutrition')
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON nutrition.ingredients(ingredient_name);
CREATE INDEX IF NOT EXISTS idx_meals_name ON nutrition.meals(meal_name);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_meal_plan_id ON nutrition.meal_plan_items(meal_plan_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_meal_id ON nutrition.meal_plan_items(meal_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_plan_date ON nutrition.meal_plan_items(plan_date);

-- Fin del script