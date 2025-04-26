// src/components/nutrition/calculator/constants.js

/**
 * Constantes para la calculadora de macros
 */

// Distribuciones predefinidas de macros
export const PRESET_DISTRIBUTIONS = {
    balanced: { name: "Equilibrado", carbs: 50, protein: 25, fat: 25 },
    high_protein: { name: "Alto en proteínas", carbs: 40, protein: 35, fat: 25 },
    low_carb: { name: "Bajo en carbohidratos", carbs: 30, protein: 35, fat: 35 },
    keto: { name: "Cetogénico", carbs: 10, protein: 30, fat: 60 },
    custom: { name: "Personalizado", carbs: 50, protein: 25, fat: 25 }
  };
  
  // Recomendaciones de macros
  export const MACRO_RECOMMENDATIONS = {
    protein: {
      min: 10,
      max: 35,
      recommended: "10-35% de las calorías diarias"
    },
    carbs: {
      min: 45,
      max: 65,
      recommended: "45-65% de las calorías diarias"
    },
    fat: {
      min: 20,
      max: 35,
      recommended: "20-35% de las calorías diarias"
    }
  };
  
  // Calorías por gramo de cada macronutriente
  export const CALORIES_PER_GRAM = {
    protein: 4,
    carbs: 4,
    fat: 9
  };
  
  // Valores por defecto para el formulario
  export const DEFAULT_FORM_VALUES = {
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
  
  // Valores por defecto para la distribución de macros
  export const DEFAULT_MACRO_DISTRIBUTION = {
    carbs: 50,
    protein: 25,
    fat: 25
  };