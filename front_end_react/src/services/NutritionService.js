// src/services/NutritionService.js
// This file now re-exports from the new structure for backward compatibility

import * as NutritionServices from './nutrition';

// Export each service individually
export const {
  IngredientService,
  MealService,
  MealPlanService,
  NutritionCalculator,
  LocalStorageHelper
} = NutritionServices;

// Default export for backward compatibility
export default NutritionServices.default;