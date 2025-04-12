// src/services/NutritionService.js
import axios from 'axios';

// Base API URL prefix
const API_BASE = '/api/nutrition';

/**
 * Service for managing ingredients
 */
class IngredientServiceClass {
  /**
   * Get all ingredients with optional search filter
   */
  async getAll(search = '') {
    try {
      const response = await axios.get(`${API_BASE}/ingredients`, {
        params: { search }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching ingredients:', error);
      throw error;
    }
  }

  /**
   * Get a single ingredient by ID
   */
  async getById(id) {
    try {
      const response = await axios.get(`${API_BASE}/ingredients/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching ingredient ${id}:`, error);
      throw error;
    }
  }

  /**
   * Create a new ingredient
   */
  async create(data) {
    try {
      const response = await axios.post(`${API_BASE}/ingredients`, data);
      return response.data;
    } catch (error) {
      console.error('Error creating ingredient:', error);
      throw error;
    }
  }

  /**
   * Update an existing ingredient
   */
  async update(id, data) {
    try {
      const response = await axios.put(`${API_BASE}/ingredients/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating ingredient ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete an ingredient
   */
  async delete(id) {
    try {
      await axios.delete(`${API_BASE}/ingredients/${id}`);
      return true;
    } catch (error) {
      console.error(`Error deleting ingredient ${id}:`, error);
      throw error;
    }
  }
}

/**
 * Service for managing meals
 */
class MealServiceClass {
  /**
   * Get all meals with optional search filter
   */
  async getAll(search = '') {
    try {
      const response = await axios.get(`${API_BASE}/meals`, {
        params: { search }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching meals:', error);
      throw error;
    }
  }

  /**
   * Get a single meal by ID
   * @param {number} id - The meal ID
   * @param {boolean} withIngredients - Whether to include ingredients in the response
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

/**
 * Service for managing meal plans
 */
class MealPlanServiceClass {
  /**
   * Get all meal plans
   * @param {boolean|null} isActive - Filter by active status, or null for all
   */
  async getAll(isActive = null) {
    try {
      const params = {};
      if (isActive !== null) {
        params.is_active = isActive;
      }
      
      const response = await axios.get(`${API_BASE}/meal-plans`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching meal plans:', error);
      throw error;
    }
  }

  /**
   * Get a single meal plan by ID
   * @param {number} id - The meal plan ID
   * @param {boolean} withItems - Whether to include items in the response
   */
  async getById(id, withItems = true) {
    try {
      const response = await axios.get(`${API_BASE}/meal-plans/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching meal plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Create a new meal plan
   */
  async create(data) {
    try {
      const response = await axios.post(`${API_BASE}/meal-plans`, data);
      return response.data;
    } catch (error) {
      console.error('Error creating meal plan:', error);
      throw error;
    }
  }

  /**
   * Update an existing meal plan
   */
  async update(id, data) {
    try {
      const response = await axios.put(`${API_BASE}/meal-plans/${id}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating meal plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete a meal plan
   */
  async delete(id) {
    try {
      await axios.delete(`${API_BASE}/meal-plans/${id}`);
      return true;
    } catch (error) {
      console.error(`Error deleting meal plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Get meal plans by date range
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   */
  async getMealPlansByDateRange(startDate, endDate) {
    try {
      // This is a placeholder implementation, as the actual endpoint may differ
      // If your backend doesn't support this directly, you might need custom implementation
      console.warn('Backend may not support getMealPlansByDateRange directly.');
      
      // For now, we'll get active plans and filter them client-side
      const response = await this.getAll(true); // Get only active plans
      const plans = response.meal_plans || [];
      
      // Mock implementation - this should be adjusted based on your actual data structure
      // This assumes plans have a start_date and end_date property
      const inRange = plans.filter(plan => {
        const planStart = new Date(plan.start_date || '1970-01-01');
        const planEnd = new Date(plan.end_date || '2999-12-31');
        const rangeStart = new Date(startDate);
        const rangeEnd = new Date(endDate);
        
        return planStart <= rangeEnd && planEnd >= rangeStart;
      });
      
      return inRange;
    } catch (error) {
      console.error('Error fetching meal plans by date range:', error);
      throw error;
    }
  }
}

// Create singleton instances
export const IngredientService = new IngredientServiceClass();
export const MealService = new MealServiceClass();
export const MealPlanService = new MealPlanServiceClass();

// Legacy export for backward compatibility
export default {
  IngredientService,
  MealService,
  MealPlanService
};