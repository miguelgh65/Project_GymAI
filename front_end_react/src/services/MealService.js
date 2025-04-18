// src/services/nutrition/MealPlanService.js
// Service for managing meal plans

import axios from 'axios';
import { API_BASE, logDebug } from './constants';
import { LocalStorageHelper } from './utils';

/**
 * Service for managing meal plans with improved error handling and caching
 */
class MealPlanServiceClass {
  constructor() {
    // Reduce cache timeout for testing (30 seconds)
    this.CACHE_TIMEOUT = 30 * 1000;
    this.lastFetch = 0;
    this.cachedPlans = null;
  }

  /**
   * Helper to get plans directly from local storage
   * @param {boolean|null} isActive - Optional filter by active status
   * @returns {Array} Array of meal plans
   */
  getLocalPlansOnly(isActive = null) {
    try {
      const localData = localStorage.getItem('local_meal_plans');
      const plans = localData ? JSON.parse(localData) : [];
      
      if (isActive !== null) {
        return plans.filter(p => p.is_active === isActive);
      }
      return plans;
    } catch (err) {
      console.error("[MealPlanService] Error reading local plans:", err);
      return [];
    }
  }

  /**
   * Get all meal plans with improved error handling and local storage fallback
   * @param {boolean|null} isActive - Filter by active status, or null for all
   * @returns {Object} Object with meal_plans array
   */
  async getAll(isActive = null) {
    try {
      // Always clear cache for testing
      this.clearCache();
      
      const now = Date.now();
      logDebug(`Fetching meal plans, active filter: ${isActive}`);
      
      const params = {};
      if (isActive !== null) {
        params.is_active = isActive;
      }
      
      // Try the API first every time
      try {
        console.log("Fetching meal plans from API...");
        const response = await axios.get(`${API_BASE}/meal-plans`, { 
          params,
          timeout: 10000 // 10 second timeout
        });
        
        console.log("API response received:", response.data);
        
        // Handle different API response formats
        let apiPlans = [];
        
        // Handle array response
        if (Array.isArray(response.data)) {
          apiPlans = response.data;
          console.log("Data is an array, using directly");
        } 
        // Handle object with meal_plans property
        else if (response.data && Array.isArray(response.data.meal_plans)) {
          apiPlans = response.data.meal_plans;
          console.log("Data has meal_plans array, using it");
        }
        // Handle object with success and data properties 
        else if (response.data && response.data.success && Array.isArray(response.data.data)) {
          apiPlans = response.data.data;
          console.log("Data has success and data array, using it");
        }
        // If data is just a single plan, wrap in array
        else if (response.data && response.data.id) {
          apiPlans = [response.data];
          console.log("Data is a single plan, wrapping in array");
        }
        // Empty response with no recognizable structure
        else {
          console.warn("Unknown response format:", response.data);
          apiPlans = [];
        }
        
        // Update cache and local storage
        this.cachedPlans = apiPlans;
        this.lastFetch = now;
        
        // Store in local storage for backup
        try {
          LocalStorageHelper.saveLocalMealPlans(apiPlans);
          console.log(`Saved ${apiPlans.length} plans to local storage`);
        } catch (storageErr) {
          console.error("Error saving to local storage:", storageErr);
        }
        
        // If filtering by active status, apply filter
        if (isActive !== null) {
          console.log(`Filtering ${apiPlans.length} plans by is_active=${isActive}`);
          return { 
            meal_plans: apiPlans.filter(p => p.is_active === isActive) 
          };
        }
        
        return { meal_plans: apiPlans };
      } catch (apiErr) {
        console.error("API error:", apiErr);
        
        // Fallback to local storage
        const localPlans = this.getLocalPlansOnly();
        console.log(`API failed, using ${localPlans.length} local plans`);
        
        if (isActive !== null) {
          return { 
            meal_plans: localPlans.filter(p => p.is_active === isActive),
            fromLocalStorage: true
          };
        }
        return { meal_plans: localPlans, fromLocalStorage: true };
      }
    } catch (error) {
      console.error("General error in getAll:", error);
      return { meal_plans: [], error: error.message };
    }
  }

  /**
   * Get a single meal plan by ID
   * @param {number|string} id - Meal plan ID
   * @param {boolean} withItems - Whether to include items in the response
   * @returns {Object} Meal plan data
   */
  async getById(id, withItems = true) {
    try {
      console.log(`Fetching meal plan ${id} with items=${withItems}`);
      
      // If ID starts with "local-", it's a locally stored plan
      if (id.toString().startsWith('local-')) {
        const localPlans = LocalStorageHelper.getLocalMealPlans() || [];
        const localPlan = localPlans.find(p => p.id.toString() === id.toString());
        
        if (!localPlan) {
          throw new Error(`Local plan ${id} not found`);
        }
        return localPlan;
      }
      
      // Otherwise, try to get from API
      const response = await axios.get(`${API_BASE}/meal-plans/${id}`, {
        params: { with_items: withItems },
        timeout: 10000
      });
      
      console.log(`Plan ${id} response:`, response.data);
      
      // Extract plan from response
      let plan = null;
      
      // Single plan object
      if (response.data && response.data.id) {
        plan = response.data;
      }
      // Object with plan property
      else if (response.data && response.data.plan && response.data.plan.id) {
        plan = response.data.plan;
      }
      // Object with success and plan property
      else if (response.data && response.data.success && response.data.data && response.data.data.id) {
        plan = response.data.data;
      }
      
      if (!plan) {
        throw new Error(`Plan ${id} not found or invalid response format`);
      }
      
      // Clean up items if they're not present
      if (!plan.items) {
        plan.items = [];
      }
      
      return plan;
    } catch (error) {
      console.error(`Error fetching meal plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Create a new meal plan with improved error handling
   * @param {Object} data - Meal plan data
   * @returns {Object} Created meal plan
   */
  async create(data) {
    try {
      console.log("Creating meal plan:", data);
      
      // Prepare data for API
      const apiData = {
        plan_name: data.plan_name || data.name || "Nuevo plan",
        is_active: data.is_active !== undefined ? data.is_active : true,
        items: Array.isArray(data.items) ? data.items : [],
        description: data.description || '',
        user_id: data.user_id || '1' // Default to user 1 if not specified
      };
      
      // Send to API first
      try {
        console.log("Sending to API:", apiData);
        const response = await axios.post(`${API_BASE}/meal-plans`, apiData, {
          timeout: 10000
        });
        
        console.log("API response:", response.data);
        
        // Extract plan from response
        let createdPlan = null;
        
        if (response.data && response.data.id) {
          createdPlan = response.data;
        } else if (response.data && response.data.meal_plan && response.data.meal_plan.id) {
          createdPlan = response.data.meal_plan;
        }
        
        if (!createdPlan) {
          throw new Error("API returned success but no plan data");
        }
        
        // Clear cache
        this.clearCache();
        
        // Merge with local plans
        const localPlans = this.getLocalPlansOnly();
        localPlans.push(createdPlan);
        localStorage.setItem('local_meal_plans', JSON.stringify(localPlans));
        
        return createdPlan;
      } catch (apiErr) {
        console.error("API error:", apiErr);
        
        // Fallback to local storage
        const localPlan = {
          ...apiData,
          id: `local-${Date.now()}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          _localOnly: true
        };
        
        // Save to local storage
        const localPlans = this.getLocalPlansOnly();
        localPlans.push(localPlan);
        localStorage.setItem('local_meal_plans', JSON.stringify(localPlans));
        
        // Clear cache
        this.clearCache();
        
        return localPlan;
      }
    } catch (error) {
      console.error("General error in create:", error);
      throw error;
    }
  }

  /**
   * Update an existing meal plan
   * @param {number|string} id - Meal plan ID
   * @param {Object} data - Updated meal plan data
   * @returns {Object} Updated meal plan
   */
  async update(id, data) {
    try {
      console.log(`Updating meal plan ${id}:`, data);
      
      // If ID starts with "local-", it's a locally stored plan
      if (id.toString().startsWith('local-')) {
        console.log(`Updating local plan ${id}`);
        const localPlans = this.getLocalPlansOnly();
        const index = localPlans.findIndex(p => p.id.toString() === id.toString());
        
        if (index === -1) {
          throw new Error(`Local plan ${id} not found`);
        }
        
        // Update plan
        const updatedPlan = {
          ...localPlans[index],
          ...data,
          id: id, // Ensure ID doesn't change
          updated_at: new Date().toISOString(),
          _localOnly: true
        };
        
        localPlans[index] = updatedPlan;
        localStorage.setItem('local_meal_plans', JSON.stringify(localPlans));
        
        // Clear cache
        this.clearCache();
        
        return updatedPlan;
      }
      
      // Otherwise, try to update through API
      try {
        console.log(`Sending PUT request to API for plan ${id}`);
        const response = await axios.put(`${API_BASE}/meal-plans/${id}`, data, {
          timeout: 10000
        });
        
        console.log("API response:", response.data);
        
        // Extract plan from response
        let updatedPlan = null;
        
        if (response.data && response.data.id) {
          updatedPlan = response.data;
        } else if (response.data && response.data.meal_plan && response.data.meal_plan.id) {
          updatedPlan = response.data.meal_plan;
        }
        
        if (!updatedPlan) {
          throw new Error("API returned success but no plan data");
        }
        
        // Update in local storage if exists
        try {
          const localPlans = this.getLocalPlansOnly();
          const index = localPlans.findIndex(p => p.id.toString() === id.toString());
          
          if (index !== -1) {
            localPlans[index] = updatedPlan;
            localStorage.setItem('local_meal_plans', JSON.stringify(localPlans));
          }
        } catch (storageErr) {
          console.warn(`Could not update local storage: ${storageErr.message}`);
        }
        
        // Clear cache
        this.clearCache();
        
        return updatedPlan;
      } catch (apiErr) {
        console.error(`API error updating plan ${id}:`, apiErr);
        
        // If API fails but still needs updating locally
        try {
          const localPlans = this.getLocalPlansOnly();
          const index = localPlans.findIndex(p => p.id.toString() === id.toString());
          
          if (index !== -1) {
            const updatedPlan = {
              ...localPlans[index],
              ...data,
              id: id,
              updated_at: new Date().toISOString(),
              _localOnly: true
            };
            
            localPlans[index] = updatedPlan;
            localStorage.setItem('local_meal_plans', JSON.stringify(localPlans));
            
            this.clearCache();
            console.log(`Updated plan ${id} in local storage only due to API error`);
            
            return updatedPlan;
          }
        } catch (localErr) {
          console.error(`Local storage error:`, localErr);
        }
        
        throw apiErr; // Re-throw API error
      }
    } catch (error) {
      console.error(`General error updating plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Delete a meal plan
   * @param {number|string} id - Meal plan ID
   * @returns {boolean} Success status
   */
  async delete(id) {
    try {
      console.log(`Deleting meal plan with ID: ${id}`);
      
      // If it's a local plan (ID starts with "local-"), just remove from localStorage
      if (id.toString().startsWith('local-')) {
        console.log(`Deleting local plan ${id} from localStorage`);
        const localPlans = this.getLocalPlansOnly();
        const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
        localStorage.setItem('local_meal_plans', JSON.stringify(filteredPlans));
        this.clearCache();
        return true;
      }
      
      // Otherwise, try to delete from API
      try {
        console.log(`Sending DELETE request to API for plan ${id}`);
        await axios.delete(`${API_BASE}/meal-plans/${id}`, {
          timeout: 10000
        });
        
        // Also remove from local storage if exists
        try {
          const localPlans = this.getLocalPlansOnly();
          const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
          localStorage.setItem('local_meal_plans', JSON.stringify(filteredPlans));
        } catch (err) {
          console.warn(`Could not update local storage after API delete: ${err.message}`);
        }
        
        this.clearCache();
        return true;
      } catch (apiErr) {
        console.error(`API error deleting plan ${id}:`, apiErr);
        
        // If API fails but it's a valid plan ID (not a local one), 
        // we still try to remove it from local storage
        try {
          const localPlans = this.getLocalPlansOnly();
          const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
          localStorage.setItem('local_meal_plans', JSON.stringify(filteredPlans));
          this.clearCache();
          console.log(`Removed plan ${id} from local storage only due to API error`);
          return true;
        } catch (localErr) {
          console.error(`Local storage error:`, localErr);
          throw apiErr; // Re-throw API error
        }
      }
    } catch (error) {
      console.error(`General error deleting plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Clear cached data - useful when debugging
   */
  clearCache() {
    this.cachedPlans = null;
    this.lastFetch = 0;
    console.log("Cache cleared");
  }
}

// Create and export the singleton instance
export const MealPlanService = new MealPlanServiceClass();