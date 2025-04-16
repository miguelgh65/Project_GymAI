// src/services/nutrition/index.js
// Main export file for nutrition services

import { IngredientService } from './IngredientService';
import { MealService } from './MealService';
import { MealPlanService } from './MealPlanService';
import { NutritionCalculator } from './NutritionCalculator';
import { LocalStorageHelper } from './utils';

// Export individually
export {
  IngredientService,
  MealService,
  MealPlanService,
  NutritionCalculator,
  LocalStorageHelper
};

// Default export for backward compatibility
export default {
  IngredientService,
  MealService,
  MealPlanService,
  NutritionCalculator
};