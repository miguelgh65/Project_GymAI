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
