-- PostgreSQL Database Initialization Script
-- Version: 2025-04-20

-- Set configurations
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS gym;
CREATE SCHEMA IF NOT EXISTS nutrition;

-- Set ownership (if running as postgres user)
ALTER SCHEMA gym OWNER TO postgres;
ALTER SCHEMA nutrition OWNER TO postgres;

-- Set search path to prioritize our schemas
SET search_path TO gym, nutrition, public;

-- GYM SCHEMA TABLES

-- Users table (in gym schema as per actual database)
CREATE TABLE IF NOT EXISTS gym.users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE,
    email VARCHAR(255),
    display_name VARCHAR(255),
    profile_picture VARCHAR(512),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ejercicios table
CREATE TABLE IF NOT EXISTS gym.ejercicios (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITHOUT TIME ZONE,
    ejercicio VARCHAR(255),
    repeticiones JSONB,
    duracion INTEGER,
    user_id VARCHAR(255),
    user_uuid INTEGER REFERENCES gym.users(id)
);

-- Rutinas table
CREATE TABLE IF NOT EXISTS gym.rutinas (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES gym.users(id),
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    ejercicios JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, dia_semana),
    UNIQUE (user_uuid, dia_semana)
);

-- Link codes table
CREATE TABLE IF NOT EXISTS gym.link_codes (
    code VARCHAR(10) PRIMARY KEY,
    user_id INTEGER REFERENCES gym.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    used BOOLEAN DEFAULT FALSE
);

-- Fitbit tokens table
CREATE TABLE IF NOT EXISTS gym.fitbit_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    user_uuid INTEGER REFERENCES gym.users(id) UNIQUE,
    client_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fitbit auth temp table
CREATE TABLE IF NOT EXISTS gym.fitbit_auth_temp (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    UNIQUE (user_id, client_id)
);

-- NUTRITION SCHEMA TABLES

-- Ingredients table
CREATE TABLE IF NOT EXISTS nutrition.ingredients (
    id SERIAL PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL UNIQUE,
    calories INTEGER NOT NULL,
    proteins NUMERIC(10,2) NOT NULL,
    carbohydrates NUMERIC(10,2) NOT NULL,
    fats NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_base BOOLEAN DEFAULT FALSE
);

-- Meals table
CREATE TABLE IF NOT EXISTS nutrition.meals (
    id SERIAL PRIMARY KEY,
    meal_name VARCHAR(255) NOT NULL,
    recipe TEXT,
    ingredients TEXT,
    calories NUMERIC(10,2) NOT NULL,
    proteins NUMERIC(10,2) NOT NULL,
    carbohydrates NUMERIC(10,2) NOT NULL,
    fats NUMERIC(10,2) NOT NULL,
    image_url VARCHAR(512),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Meal ingredients table
CREATE TABLE IF NOT EXISTS nutrition.meal_ingredients (
    id SERIAL PRIMARY KEY,
    meal_id INTEGER NOT NULL REFERENCES nutrition.meals(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES nutrition.ingredients(id) ON DELETE CASCADE,
    quantity NUMERIC(10,2) DEFAULT 0 NOT NULL CHECK (quantity >= 0),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(meal_id, ingredient_id)
);

-- Meal plans table
CREATE TABLE IF NOT EXISTS nutrition.meal_plans (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    plan_name VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    target_calories INTEGER,
    target_protein_g NUMERIC(10,2) DEFAULT NULL,
    target_carbs_g NUMERIC(10,2) DEFAULT NULL,
    target_fat_g NUMERIC(10,2) DEFAULT NULL,
    goal VARCHAR(50) DEFAULT NULL,
    CHECK (target_calories IS NULL OR target_calories >= 0),
    CHECK (target_protein_g IS NULL OR target_protein_g >= 0),
    CHECK (target_carbs_g IS NULL OR target_carbs_g >= 0),
    CHECK (target_fat_g IS NULL OR target_fat_g >= 0)
);

-- Meal plan items table
CREATE TABLE IF NOT EXISTS nutrition.meal_plan_items (
    id SERIAL PRIMARY KEY,
    meal_plan_id INTEGER REFERENCES nutrition.meal_plans(id) ON DELETE CASCADE,
    meal_id INTEGER REFERENCES nutrition.meals(id),
    day_of_week INTEGER,
    meal_type VARCHAR(50),
    quantity NUMERIC(10,2) DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    plan_date DATE,
    unit VARCHAR(20) DEFAULT 'g'
);

-- Daily tracking table
CREATE TABLE IF NOT EXISTS nutrition.daily_tracking (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    tracking_date DATE NOT NULL,
    completed_meals JSONB,
    calorie_note TEXT,
    actual_calories INTEGER,
    actual_protein INTEGER, -- <<< ADDED THIS LINE (use NUMERIC(10,2) if you need decimals)
    excess_deficit INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tracking_date)
);

-- User nutrition profiles table
CREATE TABLE IF NOT EXISTS nutrition.user_nutrition_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    sex VARCHAR(10) NOT NULL CHECK (sex IN ('male', 'female', 'other')),
    age INTEGER NOT NULL CHECK (age > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    weight NUMERIC(10,2) NOT NULL CHECK (weight > 0),
    body_fat_percentage NUMERIC(5,2) CHECK (body_fat_percentage IS NULL OR (body_fat_percentage >= 0 AND body_fat_percentage <= 100)),
    activity_level VARCHAR(50) NOT NULL,
    goal VARCHAR(50) NOT NULL,
    bmr NUMERIC(10,2) NOT NULL,
    bmi NUMERIC(5,2) NOT NULL,
    daily_calories NUMERIC(10,2) NOT NULL,
    proteins_grams NUMERIC(10,2) NOT NULL,
    carbs_grams NUMERIC(10,2) NOT NULL,
    fats_grams NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    formula VARCHAR(50),
    goal_intensity VARCHAR(50),
    units VARCHAR(10),
    tdee NUMERIC(10,2)
);

-- Import data from CSV files
-- NOTE: Adjust column names if necessary to match your actual CSV files
\copy nutrition.ingredients (ingredient_name, calories, proteins, carbohydrates, fats) FROM '/docker-entrypoint-initdb.d/ingredients_macros.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',');
\copy nutrition.meals (meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url) FROM '/docker-entrypoint-initdb.d/list_meals.csv' WITH (FORMAT CSV, HEADER true, DELIMITER ',');

-- Create indexes for performance
-- Gym schema indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON gym.users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON gym.users(google_id);
CREATE INDEX IF NOT EXISTS idx_fitbit_user_id ON gym.fitbit_tokens(user_id);

-- Nutrition schema indexes
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON nutrition.meal_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_items_meal_plan_id ON nutrition.meal_plan_items(meal_plan_id);
CREATE INDEX IF NOT EXISTS idx_daily_tracking_user_date ON nutrition.daily_tracking(user_id, tracking_date);
CREATE INDEX IF NOT EXISTS idx_daily_tracking_date ON nutrition.daily_tracking(tracking_date DESC);

-- End of initialization script