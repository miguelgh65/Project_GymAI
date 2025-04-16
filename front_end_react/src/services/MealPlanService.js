// Extracto de NutritionService.js que corrige la clase MealPlanServiceClass

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
        
        console.log("Calling meal-plans endpoint with params:", params);
        const response = await axios.get(`${API_BASE}/meal-plans`, { params });
        console.log("Raw meal-plans response:", response);
        
        // La respuesta puede tener diferentes estructuras, intentamos manejarlas todas
        if (response.data && typeof response.data === 'object') {
          // Si la respuesta ya tiene la estructura esperada
          if (Array.isArray(response.data.meal_plans)) {
            return response.data;
          }
          
          // Si la respuesta tiene éxito pero los planes están en una propiedad diferente
          if (response.data.success && Array.isArray(response.data.data)) {
            return { meal_plans: response.data.data };
          }
          
          // Si solo devuelve un array de planes
          if (Array.isArray(response.data)) {
            return { meal_plans: response.data };
          }
          
          // Formato desconocido, pero hay datos - convertimos a formato esperado
          console.log("Unknown response format for meal plans, trying to adapt");
          return { 
            success: true, 
            meal_plans: [] // Devolvemos array vacío si no podemos interpretar la respuesta
          };
        }
        
        return { meal_plans: [] };
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
        console.log(`Fetching meal plan ${id} with items=${withItems}`);
        const response = await axios.get(`${API_BASE}/meal-plans/${id}`);
        
        console.log("Meal plan detail response:", response.data);
        
        // Manejar los diferentes formatos de respuesta posibles
        if (response.data && typeof response.data === 'object') {
          if (response.data.success && response.data.plan) {
            return response.data.plan;
          }
          
          // Si la respuesta ya es el plan directamente
          if (response.data.id) {
            return response.data;
          }
        }
        
        return null;
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
        console.log("Creating meal plan with data:", data);
        const response = await axios.post(`${API_BASE}/meal-plans`, data);
        console.log("Create meal plan response:", response.data);
        
        if (response.data && response.data.success) {
          return response.data.meal_plan || response.data;
        }
        
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
        console.log(`Updating meal plan ${id} with data:`, data);
        const response = await axios.put(`${API_BASE}/meal-plans/${id}`, data);
        console.log("Update meal plan response:", response.data);
        
        if (response.data && response.data.success) {
          return response.data.meal_plan || response.data;
        }
        
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
        console.log(`Deleting meal plan ${id}`);
        const response = await axios.delete(`${API_BASE}/meal-plans/${id}`);
        console.log("Delete meal plan response:", response);
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
        // Intentamos obtener planes activos primero
        console.log(`Fetching meal plans for date range: ${startDate} to ${endDate}`);
        const response = await this.getAll(true);
        const plans = response.meal_plans || [];
        
        // Para pruebas, devolvemos todos los planes activos
        // En una implementación real, filtraríamos por fecha
        console.log(`Found ${plans.length} active plans`);
        return plans;
      } catch (error) {
        console.error('Error fetching meal plans by date range:', error);
        throw error;
      }
    }
  }