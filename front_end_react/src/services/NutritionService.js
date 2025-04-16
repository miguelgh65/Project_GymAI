// src/services/NutritionService.js - Versión con almacenamiento local para planes de comida
import axios from 'axios';

// Base API URL prefix
const API_BASE = '/api/nutrition';

// Clave para LocalStorage
const LOCAL_STORAGE_MEAL_PLANS_KEY = 'local_meal_plans';

/**
 * Funciones auxiliares para almacenamiento local de planes de comida
 */
const LocalStorageHelper = {
  /**
   * Obtiene todos los planes de comida del almacenamiento local
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
   * Guarda planes de comida en el almacenamiento local
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
   * Añade un nuevo plan al almacenamiento local
   */
  addLocalMealPlan(plan) {
    try {
      const plans = this.getLocalMealPlans();
      // Si el plan ya tiene ID, asegúrate de que sea string para consistencia
      if (plan.id) {
        plan.id = plan.id.toString();
      } else {
        // Genera un ID local temporal
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
   * Actualiza un plan existente en el almacenamiento local
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
   * Elimina un plan del almacenamiento local
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
      return response.data?.ingredients || [];
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
      return response.data?.meals || [];
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
 * Service for managing meal plans - VERSIÓN MEJORADA CON SOPORTE LOCAL
 */
class MealPlanServiceClass {
  /**
   * Get all meal plans
   * @param {boolean|null} isActive - Filter by active status, or null for all
   */
  async getAll(isActive = null) {
    try {
      console.log('MealPlanService.getAll - fetching plans, isActive:', isActive);
      
      const params = {};
      if (isActive !== null) {
        params.is_active = isActive;
      }
      
      const response = await axios.get(`${API_BASE}/meal-plans`, { params });
      console.log('MealPlanService.getAll - response:', response.data);
      
      // Intentar extraer planes de diferentes formatos de respuesta
      let plans = [];
      if (response.data && typeof response.data === 'object') {
        if (Array.isArray(response.data.meal_plans)) {
          plans = response.data.meal_plans;
        } else if (response.data.success && Array.isArray(response.data.data)) {
          plans = response.data.data;
        } else if (Array.isArray(response.data)) {
          plans = response.data;
        }
      }
      
      // Si no se encontraron planes en la API, usar los locales
      if (plans.length === 0) {
        console.log('No plans from API, using local storage');
        plans = LocalStorageHelper.getLocalMealPlans();
        if (isActive !== null) {
          plans = plans.filter(p => p.is_active === isActive);
        }
      } else {
        // Sincronizar con almacenamiento local si hay planes
        console.log('Syncing plans to local storage');
        LocalStorageHelper.saveLocalMealPlans(plans);
      }
      
      return { meal_plans: plans };
    } catch (error) {
      console.error('Error fetching meal plans:', error);
      // En caso de error, intentar usar planes locales
      const localPlans = LocalStorageHelper.getLocalMealPlans();
      const filteredPlans = isActive !== null 
        ? localPlans.filter(p => p.is_active === isActive)
        : localPlans;
      
      return { meal_plans: filteredPlans };
    }
  }

  /**
   * Get a single meal plan by ID
   * @param {number} id - The meal plan ID
   * @param {boolean} withItems - Whether to include items in the response
   */
  async getById(id, withItems = true) {
    try {
      console.log(`MealPlanService.getById - fetching plan ${id}, withItems:`, withItems);
      const response = await axios.get(`${API_BASE}/meal-plans/${id}`);
      console.log(`MealPlanService.getById - response:`, response.data);
      
      let plan = null;
      
      // Intentar extraer el plan de diferentes formatos de respuesta
      if (response.data && typeof response.data === 'object') {
        if (response.data.success && response.data.plan) {
          plan = response.data.plan;
        } else if (response.data.id) {
          plan = response.data;
        }
      }
      
      // Si no se encontró en la API, intentar local
      if (!plan) {
        const localPlans = LocalStorageHelper.getLocalMealPlans();
        plan = localPlans.find(p => p.id.toString() === id.toString());
      }
      
      if (!plan) {
        throw new Error(`Plan ${id} not found`);
      }
      
      return plan;
    } catch (error) {
      console.error(`Error fetching meal plan ${id}:`, error);
      
      // Intentar obtener del almacenamiento local
      const localPlans = LocalStorageHelper.getLocalMealPlans();
      const plan = localPlans.find(p => p.id.toString() === id.toString());
      
      if (plan) return plan;
      throw error;
    }
  }

  /**
   * Create a new meal plan
   */
  async create(data) {
    try {
      console.log('MealPlanService.create - creating plan with data:', data);
      const response = await axios.post(`${API_BASE}/meal-plans`, data);
      console.log('MealPlanService.create - response:', response.data);
      
      let createdPlan = null;
      
      // Intentar extraer el plan creado de diferentes formatos de respuesta
      if (response.data) {
        if (response.data.success && response.data.meal_plan) {
          createdPlan = response.data.meal_plan;
        } else if (response.data.id) {
          createdPlan = response.data;
        }
      }
      
      // Si se obtuvo un plan de la API, guardarlo también localmente
      if (createdPlan) {
        LocalStorageHelper.addLocalMealPlan(createdPlan);
      } else {
        // Si no se obtuvo un plan válido de la API, crear uno local
        createdPlan = {
          id: `local-${Date.now()}`,
          plan_name: data.plan_name,
          is_active: data.is_active !== undefined ? data.is_active : true,
          items: data.items || [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        LocalStorageHelper.addLocalMealPlan(createdPlan);
      }
      
      return createdPlan;
    } catch (error) {
      console.error('Error creating meal plan:', error);
      
      // Si falla la API, crear un plan local
      const localPlan = {
        id: `local-${Date.now()}`,
        plan_name: data.plan_name,
        is_active: data.is_active !== undefined ? data.is_active : true,
        items: data.items || [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      const savedPlan = LocalStorageHelper.addLocalMealPlan(localPlan);
      if (savedPlan) return savedPlan;
      
      throw error;
    }
  }

  /**
   * Update an existing meal plan
   */
  async update(id, data) {
    try {
      console.log(`MealPlanService.update - updating plan ${id} with data:`, data);
      const isLocalId = id.toString().startsWith('local-');
      
      // Si es un ID local, actualizar solo localmente
      if (isLocalId) {
        const updatedPlan = LocalStorageHelper.updateLocalMealPlan(id, data);
        if (!updatedPlan) throw new Error(`Local plan ${id} not found`);
        return updatedPlan;
      }
      
      // Si no es local, intentar actualizar en la API
      const response = await axios.put(`${API_BASE}/meal-plans/${id}`, data);
      console.log(`MealPlanService.update - response:`, response.data);
      
      let updatedPlan = null;
      
      // Extraer el plan actualizado
      if (response.data) {
        if (response.data.success && response.data.meal_plan) {
          updatedPlan = response.data.meal_plan;
        } else if (response.data.id) {
          updatedPlan = response.data;
        }
      }
      
      // Actualizar también en almacenamiento local
      if (updatedPlan) {
        LocalStorageHelper.updateLocalMealPlan(id, updatedPlan);
      } else {
        // Si no hay respuesta válida, actualizar solo localmente
        updatedPlan = LocalStorageHelper.updateLocalMealPlan(id, data);
      }
      
      return updatedPlan;
    } catch (error) {
      console.error(`Error updating meal plan ${id}:`, error);
      
      // Si falla la API, intentar actualizar localmente
      const updatedPlan = LocalStorageHelper.updateLocalMealPlan(id, data);
      if (updatedPlan) return updatedPlan;
      
      throw error;
    }
  }

  /**
   * Delete a meal plan
   */
  async delete(id) {
    try {
      console.log(`MealPlanService.delete - deleting plan ${id}`);
      const isLocalId = id.toString().startsWith('local-');
      
      // Si es un ID local, eliminar solo localmente
      if (isLocalId) {
        const deleted = LocalStorageHelper.deleteLocalMealPlan(id);
        if (!deleted) throw new Error(`Local plan ${id} not found`);
        return true;
      }
      
      // Si no es local, intentar eliminar en la API
      await axios.delete(`${API_BASE}/meal-plans/${id}`);
      
      // También eliminar del almacenamiento local
      LocalStorageHelper.deleteLocalMealPlan(id);
      
      return true;
    } catch (error) {
      console.error(`Error deleting meal plan ${id}:`, error);
      
      // Si falla la API, intentar eliminar localmente
      const deleted = LocalStorageHelper.deleteLocalMealPlan(id);
      if (deleted) return true;
      
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
      console.log(`MealPlanService.getMealPlansByDateRange - fetching plans from ${startDate} to ${endDate}`);
      
      // Intenta obtener todos los planes activos
      const response = await this.getAll(true);
      const plans = response.meal_plans || [];
      
      // Implementa la filtración por fecha en el cliente
      // Esta es una implementación temporal
      console.log(`Found ${plans.length} active plans`);
      
      // Aquí deberías filtrar por fecha si los planes tuvieran fechas
      // Por ahora devolvemos todos los planes activos
      return plans;
    } catch (error) {
      console.error('Error fetching meal plans by date range:', error);
      
      // En caso de error, devolver planes locales
      const localPlans = LocalStorageHelper.getLocalMealPlans();
      return localPlans.filter(p => p.is_active);
    }
  }
}

/**
 * Service for calculating nutritional values
 */
class NutritionCalculatorService {
  /**
   * Calculate macros based on user inputs
   */
  async calculateMacros(data) {
    try {
      const response = await axios.post(`${API_BASE}/calculate-macros`, data);
      return response.data;
    } catch (error) {
      console.error('Error calculating macros:', error);
      throw error;
    }
  }

  /**
   * Get user's nutrition profile
   */
  async getProfile() {
    try {
      const response = await axios.get(`${API_BASE}/profile`);
      return response.data?.profile || null;
    } catch (error) {
      console.error('Error fetching nutrition profile:', error);
      return null;
    }
  }
}

// Create singleton instances
export const IngredientService = new IngredientServiceClass();
export const MealService = new MealServiceClass();
export const MealPlanService = new MealPlanServiceClass();
export const NutritionCalculator = new NutritionCalculatorService();

// Legacy export for backward compatibility
export default {
  IngredientService,
  MealService,
  MealPlanService,
  NutritionCalculator
};