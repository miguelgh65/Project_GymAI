// src/services/nutrition/MealService.js
// Service for managing meals

import axios from 'axios';
import { API_BASE } from './constants';

/**
 * Service for managing meals
 */
class MealServiceClass {
  /**
   * Get all meals with optional search filter
   * @param {string} search - Optional search term
   * @returns {Object} Object with meals array
   */
  async getAll(search = '') {
    try {
      const response = await axios.get(`${API_BASE}/meals`, {
        params: { search }
      });
      
      // Handle different response formats
      if (response.data?.meals) {
        return response.data;
      }
      if (Array.isArray(response.data)) {
        return { meals: response.data };
      }
      
      return { meals: [] };
    } catch (error) {
      console.error('Error fetching meals:', error);
      return { meals: [] };
    }
  }

  /**
   * Get a single meal by ID
   * @param {number} id - Meal ID
   * @param {boolean} withIngredients - Whether to include ingredients in the response
   * @returns {Object} Meal data
   */
  async getById(id, withIngredients = false) {
    try {
      const response = await axios.get(`${API_BASE}/meals/${id}`, {
        params: { with_ingredients: withIngredients }
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching meal ${id}:`, error);
      throw error;
    }
  }

  /**
   * Get ingredients for a specific meal
   * @param {number} mealId - Meal ID
   * @returns {Array} Array of ingredients
   */
  async getIngredients(mealId) {
    try {
      const response = await axios.get(`${API_BASE}/meals/${mealId}/ingredients`);
      return response.data.ingredients || [];
    } catch (error) {
      console.error(`Error fetching ingredients for meal ${mealId}:`, error);
      throw error;
    }
  }

  /**
   * Create a new meal
   * @param {Object} data - Meal data
   * @returns {Object} Created meal
   */
  async create(data) {
    try {
      const response = await axios.post(`${API_BASE}/meals`, data);
      return response.data;
    } catch (error) {
      console.error('Error creating meal:', error);
      throw error;
    }
  }

  /**
   * Update an existing meal
   * @param {number} id - Meal ID
   * @param {Object} data - Updated meal data
   * @returns {Object} Updated meal
   */
  async update(id, data) {
    try {
      const response = await axios.put(`${API_BASE}/meals/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating meal ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete a meal
   * @param {number} id - Meal ID
   * @returns {boolean} Success status
   */
  async delete(id) {
    try {
      await axios.delete(`${API_BASE}/meals/${id}`);
      return true;
    } catch (error) {
      console.error(`Error deleting meal ${id}:`, error);
      throw error;
    }
  }

  /**
   * Add an ingredient to a meal
   * @param {number} mealId - Meal ID
   * @param {number} ingredientId - Ingredient ID
   * @param {number} quantity - Quantity in grams
   * @returns {Object} Meal ingredient relation
   */
  async addIngredient(mealId, ingredientId, quantity) {
    try {
      const response = await axios.post(`${API_BASE}/meal-ingredients`, {
        meal_id: mealId,
        ingredient_id: ingredientId,
        quantity: quantity
      });
      return response.data;
    } catch (error) {
      console.error(`Error adding ingredient to meal ${mealId}:`, error);
      throw error;
    }
  }

  /**
   * Remove an ingredient from a meal
   * @param {number} mealIngredientId - Meal ingredient relation ID
   * @returns {boolean} Success status
   */
  async removeIngredient(mealIngredientId) {
    try {
      await axios.delete(`${API_BASE}/meal-ingredients/${mealIngredientId}`);
      return true;
    } catch (error) {
      console.error(`Error removing ingredient ${mealIngredientId} from meal:`, error);
      throw error;
    }
  }
}

// Create and export the singleton instance
export const MealService = new MealServiceClass();