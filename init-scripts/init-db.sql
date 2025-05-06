-- Script SQL con esquemas bien organizados

-- Crear esquemas si no existen
CREATE SCHEMA IF NOT EXISTS gym;
CREATE SCHEMA IF NOT EXISTS nutrition;
CREATE SCHEMA IF NOT EXISTS config;

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
    user_uuid INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de rutinas
CREATE TABLE IF NOT EXISTS gym.rutinas (
    id SERIAL PRIMARY KEY,
    user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    ejercicios JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_uuid, dia_semana)
);

-- ----------------------------------------
-- ESQUEMA NUTRITION - Todo relacionado con nutrición
-- ----------------------------------------

-- Tabla de perfiles nutricionales de usuarios
CREATE TABLE IF NOT EXISTS nutrition.user_nutrition_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE,
    formula VARCHAR(50) NOT NULL,
    sex VARCHAR(10) NOT NULL CHECK (sex IN ('male', 'female', 'other')),
    age INTEGER NOT NULL CHECK (age > 0),
    height DECIMAL(6, 2) NOT NULL CHECK (height > 0),
    weight DECIMAL(5, 2) NOT NULL CHECK (weight > 0),
    body_fat_percentage DECIMAL(4, 2) CHECK (body_fat_percentage >= 0 AND body_fat_percentage <= 100),
    activity_level VARCHAR(50) NOT NULL,
    goal VARCHAR(50) NOT NULL,
    goal_intensity VARCHAR(50) NOT NULL,
    units VARCHAR(20) NOT NULL,
    bmr DECIMAL(10, 2) NOT NULL,
    tdee DECIMAL(10, 2) NOT NULL,
    bmi DECIMAL(5, 2) NOT NULL,
    daily_calories INTEGER NOT NULL,
    proteins_grams INTEGER NOT NULL,
    carbs_grams INTEGER NOT NULL,
    fats_grams INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de ingredientes
CREATE TABLE IF NOT EXISTS nutrition.ingredients (
    id SERIAL PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL UNIQUE,
    calories DECIMAL(10, 2) NOT NULL CHECK (calories >= 0),
    proteins DECIMAL(10, 2) NOT NULL CHECK (proteins >= 0),
    carbohydrates DECIMAL(10, 2) NOT NULL CHECK (carbohydrates >= 0),
    fats DECIMAL(10, 2) NOT NULL CHECK (fats >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de comidas
CREATE TABLE IF NOT EXISTS nutrition.meals (
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

-- Tabla para la relación meal-ingredient
CREATE TABLE IF NOT EXISTS nutrition.meal_ingredients (
    id SERIAL PRIMARY KEY,
    meal_id INTEGER REFERENCES nutrition.meals(id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES nutrition.ingredients(id) ON DELETE CASCADE,
    quantity DECIMAL(10, 2) NOT NULL CHECK (quantity > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (meal_id, ingredient_id)
);

-- Tabla para planes de comida
CREATE TABLE IF NOT EXISTS nutrition.meal_plans (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    target_calories INTEGER,
    target_protein_g DECIMAL(10, 2),
    target_carbs_g DECIMAL(10, 2),
    target_fat_g DECIMAL(10, 2),
    goal VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para elementos específicos del plan (comidas asignadas)
CREATE TABLE IF NOT EXISTS nutrition.meal_plan_items (
    id SERIAL PRIMARY KEY,
    meal_plan_id INTEGER REFERENCES nutrition.meal_plans(id) ON DELETE CASCADE NOT NULL,
    meal_id INTEGER REFERENCES nutrition.meals(id) ON DELETE SET NULL,
    plan_date DATE,
    day_of_week VARCHAR(20),
    meal_type VARCHAR(50),
    quantity DECIMAL(10, 2) DEFAULT 100.0 CHECK (quantity > 0),
    unit VARCHAR(10) DEFAULT 'g',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para seguimiento diario de nutrición
CREATE TABLE IF NOT EXISTS nutrition.daily_tracking (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tracking_date DATE NOT NULL,
    completed_meals JSONB NOT NULL DEFAULT '{}',
    calorie_note TEXT,
    actual_calories INTEGER,
    actual_protein INTEGER,
    excess_deficit INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, tracking_date)
);

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

-- ----------------------------------------
-- ESQUEMA CONFIG - Integración con APIs externas
-- ----------------------------------------

-- Tabla para tokens de Fitbit
CREATE TABLE IF NOT EXISTS config.fitbit_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES users(id) ON DELETE CASCADE,
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

-- ----------------------------------------
-- ÍNDICES PARA OPTIMIZACIÓN
-- ----------------------------------------
-- Índices para users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON public.users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON public.users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- Índices para ejercicios y rutinas
CREATE INDEX IF NOT EXISTS idx_ejercicios_user_id ON gym.ejercicios(user_id);
CREATE INDEX IF NOT EXISTS idx_ejercicios_fecha ON gym.ejercicios(fecha);
CREATE INDEX IF NOT EXISTS idx_rutinas_user_id ON gym.rutinas(user_id);
CREATE INDEX IF NOT EXISTS idx_rutinas_dia_semana ON gym.rutinas(dia_semana);

-- Índices para tablas de nutrición
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON nutrition.ingredients(ingredient_name);
CREATE INDEX IF NOT EXISTS idx_meals_name ON nutrition.meals(meal_name);
CREATE INDEX IF NOT EXISTS idx_nutrition_profiles_user_id ON nutrition.user_nutrition_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON nutrition.meal_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_meal_plan_id ON nutrition.meal_plan_items(meal_plan_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_meal_id ON nutrition.meal_plan_items(meal_id);
CREATE INDEX IF NOT EXISTS idx_daily_tracking_user_id ON nutrition.daily_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_tracking_date ON nutrition.daily_tracking(tracking_date);