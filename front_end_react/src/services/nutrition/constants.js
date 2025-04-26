// src/services/nutrition/constants.js

/**
 * Constantes centralizadas para los servicios de nutrición
 * y componentes relacionados
 */

// Base URL para las peticiones a la API
export const API_BASE = '/api/nutrition';

// Claves para localStorage
export const LOCAL_STORAGE_MEAL_PLANS_KEY = 'meal_plans';
export const LOCAL_STORAGE_ACTIVE_PLAN_KEY = 'active_meal_plan';
export const LOCAL_STORAGE_MEALS_KEY = 'meals';
export const LOCAL_STORAGE_INGREDIENTS_KEY = 'ingredients';
export const LOCAL_STORAGE_PROFILE_KEY = 'nutrition_profile';
export const LOCAL_STORAGE_TEMP_TARGETS_KEY = 'temp_nutrition_targets';

// Códigos de error para la API
export const ERROR_CODES = {
  PROFILE_NOT_FOUND: 'PROFILE_NOT_FOUND',
  INVALID_DATA: 'INVALID_DATA',
  SERVER_ERROR: 'SERVER_ERROR'
};

// Valores por defecto para cuando no hay conexión con el servidor
export const DEFAULT_CALORIE_VALUES = {
  bmr: 1800,
  tdee: 2500,
  goal_calories: 2500
};

// Formatos de fecha
export const DATE_FORMAT = 'YYYY-MM-DD';

// Macronutrientes y sus propiedades
export const MACROS = {
  protein: {
    name: 'Proteínas',
    calories_per_gram: 4,
    color: '#4caf50',
    recommended_range: '10-35%',
    min_percentage: 10,
    max_percentage: 35
  },
  carbs: {
    name: 'Carbohidratos',
    calories_per_gram: 4,
    color: '#2196f3',
    recommended_range: '45-65%',
    min_percentage: 45,
    max_percentage: 65
  },
  fat: {
    name: 'Grasas',
    calories_per_gram: 9,
    color: '#ff9800',
    recommended_range: '20-35%',
    min_percentage: 20,
    max_percentage: 35
  }
};

// Distribuciones predefinidas de macros
export const PRESET_DISTRIBUTIONS = {
  balanced: { name: "Equilibrado", carbs: 50, protein: 25, fat: 25 },
  high_protein: { name: "Alto en proteínas", carbs: 40, protein: 35, fat: 25 },
  low_carb: { name: "Bajo en carbohidratos", carbs: 30, protein: 35, fat: 35 },
  keto: { name: "Cetogénico", carbs: 10, protein: 30, fat: 60 },
  custom: { name: "Personalizado", carbs: 50, protein: 25, fat: 25 }
};

// Valores por defecto para la calculadora
export const DEFAULT_CALCULATOR_VALUES = {
  units: 'metric',
  formula: 'mifflin_st_jeor',
  gender: 'male',
  age: 30,
  height: 175, // cm
  weight: 75, // kg
  body_fat_percentage: null,
  activity_level: 'moderate',
  goal: 'maintain',
  goal_intensity: 'normal'
};

// Distribución de macros por defecto
export const DEFAULT_MACRO_DISTRIBUTION = {
  carbs: 50,
  protein: 25,
  fat: 25
};

// Otras constantes que podrían ser necesarias
export const DAYS_OF_WEEK = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
export const MEAL_TYPES = ['Desayuno', 'Comida', 'Cena', 'Snack'];

// Constantes para las partes relacionadas con planes de comida
export const MEAL_PLAN_STATUS = {
  ACTIVE: 'active',
  DRAFT: 'draft',
  COMPLETED: 'completed',
  ARCHIVED: 'archived'
};

// Constantes para tracking
export const TRACKING_CONSTANTS = {
  MAX_MEALS_PER_DAY: 6,
  DEFAULT_CALORIE_GOAL: 2000
};