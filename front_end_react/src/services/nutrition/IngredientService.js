// src/services/nutrition/IngredientService.js
// Service for managing ingredients

import axios from 'axios';
import { API_BASE } from './constants';

/**
 * Service for managing ingredients
 */
class IngredientServiceClass {
  /**
   * Get all ingredients with optional search filter
   * @param {string} search - Optional search term
   * @returns {Array} Array of ingredients
   */
  async getAll(search = '') {
    try {
      const response = await axios.get(`${API_BASE}/ingredients`, {
        params: { search }
      });
      
      // Handle different response formats
      if (response.data?.ingredients) {
        return response.data.ingredients;
      }
      if (Array.isArray(response.data)) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error fetching ingredients:', error);
      throw error;
    }
  }

  /**
   * Get a single ingredient by ID
   * @param {number} id - Ingredient ID
   * @returns {Object} Ingredient data
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
   * @param {Object} data - Ingredient data
   * @returns {Object} Created ingredient
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
   * @param {number} id - Ingredient ID
   * @param {Object} data - Updated ingredient data
   * @returns {Object} Updated ingredient
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
   * @param {number} id - Ingredient ID
   * @returns {boolean} Success status
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

// Create and export the singleton instance
export const IngredientService = new IngredientServiceClass();