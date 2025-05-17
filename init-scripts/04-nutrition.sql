-- ----------------------------------------
-- ESQUEMA NUTRITION - Todo relacionado con nutrición
-- ----------------------------------------

-- Tabla de perfiles nutricionales de usuarios
CREATE TABLE IF NOT EXISTS nutrition.user_nutrition_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_uuid INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
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
    user_uuid INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
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
    user_uuid INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
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
