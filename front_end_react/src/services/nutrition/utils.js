// src/services/nutrition/utils.js
// Utilities for nutrition services

import { LOCAL_STORAGE_MEAL_PLANS_KEY } from './constants';

/**
 * Helper for local storage operations
 */
export const LocalStorageHelper = {
  /**
   * Get all meal plans from local storage
   */
  getLocalMealPlans() {
    try {
      const data = localStorage.getItem(LOCAL_STORAGE_MEAL_PLANS_KEY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error reading local meal plans:', error);
      return [];
    }
  },

  /**
   * Save meal plans to local storage
   */
  saveLocalMealPlans(plans) {
    try {
      localStorage.setItem(LOCAL_STORAGE_MEAL_PLANS_KEY, JSON.stringify(plans));
      return true;
    } catch (error) {
      console.error('Error saving local meal plans:', error);
      return false;
    }
  },

  /**
   * Add a new meal plan to local storage
   */
  addLocalMealPlan(plan) {
    try {
      const plans = this.getLocalMealPlans();
      // Ensure ID is a string for consistency
      if (plan.id) {
        plan.id = plan.id.toString();
      } else {
        // Generate temporary local ID
        plan.id = `local-${Date.now()}`;
      }
      plans.push(plan);
      this.saveLocalMealPlans(plans);
      return plan;
    } catch (error) {
      console.error('Error adding local meal plan:', error);
      return null;
    }
  },

  /**
   * Update an existing meal plan in local storage
   */
  updateLocalMealPlan(id, planData) {
    try {
      const plans = this.getLocalMealPlans();
      const index = plans.findIndex(p => p.id.toString() === id.toString());
      if (index !== -1) {
        plans[index] = { ...plans[index], ...planData, id: plans[index].id };
        this.saveLocalMealPlans(plans);
        return plans[index];
      }
      return null;
    } catch (error) {
      console.error(`Error updating local meal plan ${id}:`, error);
      return null;
    }
  },

  /**
   * Delete a meal plan from local storage
   */
  deleteLocalMealPlan(id) {
    try {
      const plans = this.getLocalMealPlans();
      const filtered = plans.filter(p => p.id.toString() !== id.toString());
      this.saveLocalMealPlans(filtered);
      return true;
    } catch (error) {
      console.error(`Error deleting local meal plan ${id}:`, error);
      return false;
    }
  }
};

/**
 * Calculate nutrition summary from macros
 * @param {Object} macros - Macronutrients in grams
 * @returns {Object} Formatted nutrition summary
 */
export const getNutritionSummary = (macros) => {
  const { calories, proteins, carbohydrates, fats } = macros;
  
  // Calculate calorie composition
  const proteinCalories = proteins * 4;
  const carbCalories = carbohydrates * 4;
  const fatCalories = fats * 9;
  
  const totalCalories = proteinCalories + carbCalories + fatCalories;
  
  // Calculate percentages
  const proteinPercentage = Math.round((proteinCalories / totalCalories) * 100) || 0;
  const carbPercentage = Math.round((carbCalories / totalCalories) * 100) || 0;
  const fatPercentage = Math.round((fatCalories / totalCalories) * 100) || 0;
  
  return {
    calories: Math.round(calories),
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