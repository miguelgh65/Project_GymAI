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
    // Cache timeout in milliseconds (5 minutes)
    this.CACHE_TIMEOUT = 5 * 60 * 1000;
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
      const now = Date.now();
      const useCache = this.cachedPlans && (now - this.lastFetch < this.CACHE_TIMEOUT);
      
      if (useCache) {
        logDebug("Using cached meal plans");
        // Filter cached plans if isActive is specified
        if (isActive !== null) {
          return {
            meal_plans: this.cachedPlans.filter(plan => plan.is_active === isActive)
          };
        }
        return { meal_plans: this.cachedPlans };
      }
      
      // Get local plans first before we try the API
      const localPlans = this.getLocalPlansOnly();
      logDebug(`Fetching meal plans, active filter: ${isActive}, found ${localPlans.length} local plans`);
      
      const params = {};
      if (isActive !== null) {
        params.is_active = isActive;
      }
      
      // Try the API
      try {
        const response = await axios.get(`${API_BASE}/meal-plans`, { 
          params,
          timeout: 5000 // 5 second timeout
        });
        
        logDebug("API response received", response.data);
        
        // Handle different API response formats
        let apiPlans = [];
        if (response.data && typeof response.data === 'object') {
          if (Array.isArray(response.data.meal_plans)) {
            apiPlans = response.data.meal_plans;
          } else if (response.data.success && Array.isArray(response.data.data)) {
            apiPlans = response.data.data;
          } else if (Array.isArray(response.data)) {
            apiPlans = response.data;
          }
        }
        
        // If API returned nothing, use local plans
        if (apiPlans.length === 0) {
          logDebug("No plans from API, using local plans");
          this.cachedPlans = localPlans;
          this.lastFetch = now;
          
          // Apply filter if needed
          if (isActive !== null) {
            return { 
              meal_plans: localPlans.filter(p => p.is_active === isActive),
              fromLocalOnly: true
            };
          }
          return { meal_plans: localPlans, fromLocalOnly: true };
        }
        
        // Normalize plan data from API
        const normalizedPlans = apiPlans.map(plan => ({
          id: plan.id,
          plan_name: plan.plan_name || plan.name || `Plan ${plan.id}`,
          name: plan.name || plan.plan_name || `Plan ${plan.id}`,
          description: plan.description || '',
          is_active: typeof plan.is_active === 'boolean' ? plan.is_active : true,
          items: Array.isArray(plan.items) ? plan.items : [],
          created_at: plan.created_at || new Date().toISOString(),
          updated_at: plan.updated_at || new Date().toISOString()
        }));
        
        // Merge with local plans
        const remoteIds = normalizedPlans.map(p => p.id.toString());
        const filteredLocalPlans = localPlans.filter(p => 
          p.id && p.id.toString().startsWith('local-') && !remoteIds.includes(p.id.toString())
        );
        
        // Final merged plans list
        const mergedPlans = [...normalizedPlans, ...filteredLocalPlans];
        
        // Update cache and local storage
        this.cachedPlans = mergedPlans;
        this.lastFetch = now;
        
        // Update local storage
        try {
          LocalStorageHelper.saveLocalMealPlans(mergedPlans);
        } catch (storageErr) {
          console.error("Error saving to local storage:", storageErr);
        }
        
        // If filtering by active status, apply filter
        if (isActive !== null) {
          return { 
            meal_plans: mergedPlans.filter(p => p.is_active === isActive) 
          };
        }
        return { meal_plans: mergedPlans };
      } catch (apiErr) {
        logDebug(`API error: ${apiErr.message}`);
        
        // If API fails, use local plans
        this.cachedPlans = localPlans;
        this.lastFetch = now;
        
        if (isActive !== null) {
          return { 
            meal_plans: localPlans.filter(p => p.is_active === isActive),
            fromCache: true
          };
        }
        return { meal_plans: localPlans, fromCache: true };
      }
    } catch (error) {
      logDebug(`Error fetching meal plans: ${error.message}`);
      console.error("Full error:", error);
      
      // As a last resort, try direct localStorage access
      try {
        const localPlans = this.getLocalPlansOnly();
        if (isActive !== null) {
          return { 
            meal_plans: localPlans.filter(p => p.is_active === isActive),
            fromCache: true,
            error: error.message
          };
        }
        return { 
          meal_plans: localPlans,
          fromCache: true,
          error: error.message
        };
      } catch (storageErr) {
        console.error("Error accessing local storage:", storageErr);
        // If everything fails, return empty array
        return { 
          meal_plans: [],
          error: `API error: ${error.message}, Storage error: ${storageErr.message}`
        };
      }
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
      logDebug(`Fetching meal plan ${id} with items=${withItems}`);
      
      // First check local storage
      const localPlans = LocalStorageHelper.getLocalMealPlans() || [];
      const localPlan = localPlans.find(p => p.id.toString() === id.toString());
      
      // If ID starts with "local-", it's a locally stored plan
      if (id.toString().startsWith('local-')) {
        if (!localPlan) {
          throw new Error(`Local plan ${id} not found`);
        }
        return localPlan;
      }
      
      // If not a local ID, try to get from API
      const response = await axios.get(`${API_BASE}/meal-plans/${id}`, {
        params: { with_items: withItems },
        timeout: 5000 // 5 second timeout
      });
      
      logDebug(`Meal plan ${id} response received`, response.data);
      
      // Extract plan from response
      let plan = null;
      if (response.data && typeof response.data === 'object') {
        if (response.data.success && response.data.plan) {
          plan = response.data.plan;
        } else if (response.data.id) {
          plan = response.data;
        }
      }
      
      if (!plan) {
        // If not found in API, try to use local version
        if (localPlan) {
          return localPlan;
        }
        throw new Error(`Plan ${id} not found`);
      }
      
      // Normalize plan data
      return {
        id: plan.id,
        plan_name: plan.plan_name || plan.name || `Plan ${plan.id}`,
        name: plan.name || plan.plan_name || `Plan ${plan.id}`,
        description: plan.description || '',
        is_active: typeof plan.is_active === 'boolean' ? plan.is_active : true,
        items: Array.isArray(plan.items) ? plan.items : [],
        created_at: plan.created_at || new Date().toISOString(),
        updated_at: plan.updated_at || new Date().toISOString()
      };
    } catch (error) {
      logDebug(`Error fetching meal plan ${id}: ${error.message}`);
      console.error("Full error:", error);
      
      // Try local storage as fallback
      try {
        const localPlans = LocalStorageHelper.getLocalMealPlans() || [];
        const plan = localPlans.find(p => p.id.toString() === id.toString());
        
        if (plan) {
          return plan;
        }
        
        throw error; // Re-throw if not found locally
      } catch (storageErr) {
        console.error("Error accessing local storage:", storageErr);
        throw error; // Re-throw original error
      }
    }
  }

  /**
   * Create a new meal plan with improved error handling
   * @param {Object} data - Meal plan data
   * @returns {Object} Created meal plan
   */
  async create(data) {
    try {
      logDebug("Creating meal plan", data);
      
      // Always create a local version first
      const localPlan = {
        ...data,
        id: `local-${Date.now()}`,
        plan_name: data.plan_name || data.name || "Nuevo plan",
        name: data.name || data.plan_name || "Nuevo plan",
        is_active: data.is_active !== undefined ? data.is_active : true,
        items: Array.isArray(data.items) ? data.items : [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      // Save to local storage immediately
      const localPlans = this.getLocalPlansOnly();
      localPlans.push(localPlan);
      LocalStorageHelper.saveLocalMealPlans(localPlans);
      
      // Clear cache to ensure we get fresh data next time
      this.clearCache();
      
      // Normalize data before sending to API
      const normalizedData = {
        plan_name: data.plan_name || data.name || "Nuevo plan",
        name: data.name || data.plan_name || "Nuevo plan",
        is_active: data.is_active !== undefined ? data.is_active : true,
        items: Array.isArray(data.items) ? data.items : [],
        description: data.description || ''
      };
      
      // Try to send to the API
      try {
        const response = await axios.post(`${API_BASE}/meal-plans`, normalizedData, {
          timeout: 8000 // Longer timeout for creation
        });
        
        logDebug("Create meal plan response", response.data);
        
        // Try to extract created plan from response
        let createdPlan = null;
        if (response.data) {
          if (response.data.success && response.data.meal_plan) {
            createdPlan = response.data.meal_plan;
          } else if (response.data.id) {
            createdPlan = response.data;
          } else if (response.data.plan) {
            createdPlan = response.data.plan;
          }
        }
        
        // If API creation was successful, update local storage
        if (createdPlan) {
          // Find the local plan we just created
          const updatedLocalPlans = this.getLocalPlansOnly();
          const localPlanIndex = updatedLocalPlans.findIndex(p => p.id === localPlan.id);
          
          if (localPlanIndex >= 0) {
            // Replace with API version
            updatedLocalPlans.splice(localPlanIndex, 1);
          }
          
          // Add the API plan
          updatedLocalPlans.push(createdPlan);
          LocalStorageHelper.saveLocalMealPlans(updatedLocalPlans);
          
          return createdPlan;
        }
        
        // If API didn't return a plan but request succeeded, use our local plan
        return localPlan;
      } catch (apiErr) {
        logDebug(`API error creating plan: ${apiErr.message}`);
        // Return the local plan we already created
        return {
          ...localPlan,
          _local: true,
          _error: apiErr.message
        };
      }
    } catch (error) {
      logDebug(`Error in create: ${error.message}`);
      console.error("Full error:", error);
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
      logDebug(`Updating meal plan ${id}`, data);
      
      // Check if this is a local-only plan
      const isLocalId = id.toString().startsWith('local-');
      
      if (isLocalId) {
        logDebug(`Updating local-only plan ${id}`);
        // For local plans, just update local storage
        const updatedPlan = LocalStorageHelper.updateLocalMealPlan(id, {
          ...data,
          updated_at: new Date().toISOString()
        });
        
        if (!updatedPlan) {
          throw new Error(`Local plan ${id} not found`);
        }
        
        // Refresh cached plans
        this.cachedPlans = null;
        this.lastFetch = 0;
        
        return updatedPlan;
      }
      
      // For remote plans, update local version first
      const localPlans = LocalStorageHelper.getLocalMealPlans() || [];
      const existingLocalPlan = localPlans.find(p => p.id.toString() === id.toString());
      
      if (existingLocalPlan) {
        // Update local version first
        const updatedLocalPlan = {
          ...existingLocalPlan,
          ...data,
          updated_at: new Date().toISOString()
        };
        
        LocalStorageHelper.updateLocalMealPlan(id, updatedLocalPlan);
      }
      
      // Now try API
      const normalizedData = {
        ...data,
        plan_name: data.plan_name || data.name,
        name: data.name || data.plan_name
      };
      
      const response = await axios.put(`${API_BASE}/meal-plans/${id}`, normalizedData, {
        timeout: 8000
      });
      
      logDebug(`Update meal plan ${id} response`, response.data);
      
      // Extract updated plan
      let updatedPlan = null;
      if (response.data) {
        if (response.data.success && response.data.meal_plan) {
          updatedPlan = response.data.meal_plan;
        } else if (response.data.id) {
          updatedPlan = response.data;
        } else if (response.data.plan) {
          updatedPlan = response.data.plan;
        }
      }
      
      if (!updatedPlan) {
        // If API succeeded but we couldn't extract the updated plan,
        // create a local version of the update
        const localPlans = LocalStorageHelper.getLocalMealPlans() || [];
        const existingPlan = localPlans.find(p => p.id.toString() === id.toString());
        
        if (existingPlan) {
          updatedPlan = {
            ...existingPlan,
            ...normalizedData,
            updated_at: new Date().toISOString()
          };
          
          // Update in local storage
          LocalStorageHelper.updateLocalMealPlan(id, updatedPlan);
        } else {
          // Create a new local plan if not found
          updatedPlan = {
            ...normalizedData,
            id: `local-${Date.now()}`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          };
          
          LocalStorageHelper.addLocalMealPlan(updatedPlan);
        }
      } else {
        // If we got a valid response, update local storage
        try {
          const localPlans = LocalStorageHelper.getLocalMealPlans() || [];
          const existingIndex = localPlans.findIndex(p => p.id.toString() === id.toString());
          
          if (existingIndex >= 0) {
            localPlans[existingIndex] = updatedPlan;
          } else {
            localPlans.push(updatedPlan);
          }
          
          LocalStorageHelper.saveLocalMealPlans(localPlans);
          
          // Refresh cached plans
          this.cachedPlans = null;
          this.lastFetch = 0;
        } catch (storageErr) {
          console.error("Error updating local storage:", storageErr);
        }
      }
      
      return updatedPlan;
      
    } catch (error) {
      logDebug(`Error updating meal plan ${id}: ${error.message}`);
      console.error("Full error:", error);
      
      // Try to update locally if API fails
      try {
        const localPlans = LocalStorageHelper.getLocalMealPlans() || [];
        const existingPlan = localPlans.find(p => p.id.toString() === id.toString());
        
        if (existingPlan) {
          const updatedPlan = {
            ...existingPlan,
            ...data,
            updated_at: new Date().toISOString(),
            _localOnly: true,
            _error: error.message
          };
          
          const savedPlan = LocalStorageHelper.updateLocalMealPlan(id, updatedPlan);
          if (savedPlan) {
            return savedPlan;
          }
        } else {
          // Create a new local plan
          const newPlan = {
            ...data,
            id: `local-${Date.now()}`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            _localOnly: true,
            _error: error.message
          };
          
          const savedPlan = LocalStorageHelper.addLocalMealPlan(newPlan);
          if (savedPlan) {
            return savedPlan;
          }
        }
        
        throw error;
      } catch (storageErr) {
        console.error("Error updating local storage:", storageErr);
        throw error; // Re-throw original error
      }
    }
  }

  /**
   * Delete a meal plan
   * @param {number|string} id - Meal plan ID
   * @returns {boolean} Success status
   */
  async delete(id) {
    try {
      logDebug(`Deleting meal plan ${id}`);
      
      // Check if local ID
      if (id.toString().startsWith('local-')) {
        const success = LocalStorageHelper.deleteLocalMealPlan(id);
        if (!success) {
          throw new Error(`Local plan ${id} not found`);
        }
        
        // Refresh cached plans
        this.cachedPlans = null;
        this.lastFetch = 0;
        
        return true;
      }
      
      // Delete from local storage first
      try {
        LocalStorageHelper.deleteLocalMealPlan(id);
        
        // Refresh cached plans
        this.cachedPlans = null;
        this.lastFetch = 0;
      } catch (storageErr) {
        console.error("Error deleting from local storage:", storageErr);
      }
      
      // Try API delete second
      const response = await axios.delete(`${API_BASE}/meal-plans/${id}`, {
        timeout: 5000
      });
      
      logDebug(`Delete meal plan ${id} response:`, response.data);
      
      return true;
    } catch (error) {
      logDebug(`Error deleting meal plan ${id}: ${error.message}`);
      console.error("Full error:", error);
      
      // Try to delete from local storage even if API fails
      try {
        const deleted = LocalStorageHelper.deleteLocalMealPlan(id);
        
        // Refresh cached plans
        this.cachedPlans = null;
        this.lastFetch = 0;
        
        if (deleted) {
          return true;
        }
        
        throw error;
      } catch (storageErr) {
        console.error("Error accessing local storage:", storageErr);
        throw error; // Re-throw original error
      }
    }
  }
  
  /**
   * Get meal plans by date range
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   * @returns {Array} Array of meal plan items for the date range
   */
  async getMealPlansByDateRange(startDate, endDate) {
    logDebug(`Getting meal plans for date range: ${startDate} to ${endDate}`);
    
    try {
      // We only want active plans
      const response = await this.getAll(true);
      
      // Log once to avoid spamming
      logDebug(`Found ${response.meal_plans.length} active plans`);
      
      if (response.meal_plans.length === 0) {
        return [];
      }
      
      // Process plans to create daily schedule
      const result = [];
      const plans = response.meal_plans || [];
      
      // For now, we'll just return all active plan items
      // In a real implementation, you would filter by date
      plans.forEach(plan => {
        if (Array.isArray(plan.items)) {
          plan.items.forEach(item => {
            const formattedItem = {
              ...item,
              plan_id: plan.id,
              plan_name: plan.name || plan.plan_name,
              meal_name: item.meal_name || `Comida ${item.meal_id}`
            };
            result.push(formattedItem);
          });
        }
      });
      
      return result;
    } catch (error) {
      logDebug(`Error getting meal plans by date range: ${error.message}`);
      console.error("Full error:", error);
      return []; // Return empty array on error
    }
  }

  /**
   * Clear cached data - useful when debugging
   */
  clearCache() {
    this.cachedPlans = null;
    this.lastFetch = 0;
    logDebug("Cache cleared");
  }
}

// Create and export the singleton instance
export const MealPlanService = new MealPlanServiceClass();