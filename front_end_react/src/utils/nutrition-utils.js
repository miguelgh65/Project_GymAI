// src/utils/nutrition-utils.js
// Nutritional utility functions

/**
 * Calculate nutrition summary from macros
 * @param {Object} macros - Macronutrients object with calories, proteins, carbohydrates, fats
 * @returns {Object} Formatted nutrition summary
 */
export const getNutritionSummary = (macros = {}) => {
  const { calories = 0, proteins = 0, carbohydrates = 0, fats = 0 } = macros;
  
  // Calculate calorie composition
  const proteinCalories = proteins * 4;
  const carbCalories = carbohydrates * 4;
  const fatCalories = fats * 9;
  
  // Total calories may be provided, or we calculate from macros
  const totalCalculatedCalories = proteinCalories + carbCalories + fatCalories;
  const totalCalories = calories || totalCalculatedCalories;
  
  // Calculate percentages
  const proteinPercentage = Math.round((proteinCalories / totalCalories) * 100) || 0;
  const carbPercentage = Math.round((carbCalories / totalCalories) * 100) || 0;
  const fatPercentage = Math.round((fatCalories / totalCalories) * 100) || 0;
  
  return {
    calories: Math.round(totalCalories),
    macros: {
      proteins: {
        grams: Math.round(proteins * 10) / 10,
        calories: Math.round(proteinCalories),
        percentage: proteinPercentage
      },
      carbs: {
        grams: Math.round(carbohydrates * 10) / 10,
        calories: Math.round(carbCalories),
        percentage: carbPercentage
      },
      fats: {
        grams: Math.round(fats * 10) / 10,
        calories: Math.round(fatCalories),
        percentage: fatPercentage
      }
    }
  };
};

/**
 * Calculate a simple macronutrient distribution
 * @param {number} calories - Total calories
 * @param {string} goal - Goal (lose, maintain, gain)
 * @returns {Object} Macro distribution in grams
 */
export const calculateSimpleMacros = (calories, goal = 'maintain') => {
  let proteinPct, carbsPct, fatPct;
  
  if (goal === 'lose') {
    proteinPct = 0.40; // 40%
    fatPct = 0.35;     // 35%
    carbsPct = 0.25;   // 25%
  } else if (goal === 'gain') {
    proteinPct = 0.30; // 30%
    fatPct = 0.30;     // 30%
    carbsPct = 0.40;   // 40%
  } else {
    // maintain
    proteinPct = 0.30; // 30%
    fatPct = 0.30;     // 30%
    carbsPct = 0.40;   // 40%
  }
  
  // Calculate grams
  const proteinGrams = Math.round((calories * proteinPct) / 4);
  const carbGrams = Math.round((calories * carbsPct) / 4);
  const fatGrams = Math.round((calories * fatPct) / 9);
  
  return {
    proteins: proteinGrams,
    carbs: carbGrams,
    fats: fatGrams,
    calories
  };
};