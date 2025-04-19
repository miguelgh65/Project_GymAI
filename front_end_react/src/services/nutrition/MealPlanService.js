// src/services/nutrition/MealPlanService.js
// Service for managing meal plans

import axios from 'axios';
import { API_BASE } from './constants';

/**
 * Servicio para manejar planes de comida con almacenamiento local robusto
 */
class MealPlanServiceClass {
  constructor() {
    this.LOCAL_STORAGE_KEY = 'local_meal_plans';
    this.cachedPlans = null;
    this.lastFetch = 0;
  }

  /**
   * Obtener planes directamente de localStorage
   * @param {boolean|null} isActive - Filtrar por estado activo (opcional)
   * @returns {Array} Array de planes de comida
   */
  getLocalPlansOnly(isActive = null) {
    try {
      const localData = localStorage.getItem(this.LOCAL_STORAGE_KEY);
      let plans = [];
      
      if (localData) {
        try {
          plans = JSON.parse(localData);
          if (!Array.isArray(plans)) {
            console.error("Los datos de planes en localStorage no son un array:", plans);
            plans = [];
          }
        } catch (parseError) {
          console.error("Error al analizar datos de localStorage:", parseError);
          plans = [];
        }
      }
      
      // Filtrar por isActive si se proporciona
      if (isActive !== null) {
        return plans.filter(p => p.is_active === isActive);
      }
      
      return plans;
    } catch (err) {
      console.error("[MealPlanService] Error al leer planes locales:", err);
      return [];
    }
  }

  /**
   * Obtener todos los planes de comida
   * @param {boolean|null} isActive - Filtrar por estado activo
   * @returns {Object} Objeto con array meal_plans
   */
  async getAll(isActive = null) {
    try {
      // Limpiar caché para pruebas
      this.clearCache();
      
      console.log(`Obteniendo planes de comida, filtro activo: ${isActive}`);
      
      const params = {};
      if (isActive !== null) {
        params.is_active = isActive;
      }
      
      // Intentar primero la API
      try {
        console.log("Obteniendo planes de comida desde la API...");
        const response = await axios.get(`${API_BASE}/meal-plans`, { 
          params,
          timeout: 10000 // 10 segundos de timeout
        });
        
        console.log("Respuesta de API recibida:", response.data);
        
        // Procesar diferentes formatos de respuesta
        let apiPlans = [];
        
        if (Array.isArray(response.data)) {
          apiPlans = response.data;
        } 
        else if (response.data && Array.isArray(response.data.meal_plans)) {
          apiPlans = response.data.meal_plans;
        }
        else if (response.data && response.data.success && Array.isArray(response.data.data)) {
          apiPlans = response.data.data;
        }
        else if (response.data && response.data.id) {
          apiPlans = [response.data];
        }
        else {
          console.warn("Formato de respuesta desconocido:", response.data);
          apiPlans = [];
        }
        
        // Actualizar caché y localStorage
        this.cachedPlans = apiPlans;
        this.lastFetch = Date.now();
        
        // Guardar en localStorage como respaldo
        try {
          // Combinar con planes locales para no perder datos
          const localPlans = this.getLocalPlansOnly();
          const localOnlyPlans = localPlans.filter(localPlan => 
            !apiPlans.some(apiPlan => apiPlan.id === localPlan.id)
          );
          
          const combinedPlans = [...apiPlans, ...localOnlyPlans];
          localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(combinedPlans));
          console.log(`Guardados ${combinedPlans.length} planes en localStorage`);
        } catch (storageErr) {
          console.error("Error al guardar en localStorage:", storageErr);
        }
        
        // Filtrar por estado activo si se solicita
        if (isActive !== null) {
          return { 
            meal_plans: apiPlans.filter(p => p.is_active === isActive) 
          };
        }
        
        return { meal_plans: apiPlans };
      } catch (apiErr) {
        console.error("Error de API:", apiErr);
        
        // Usar localStorage como fallback
        const localPlans = this.getLocalPlansOnly();
        console.log(`Error de API, usando ${localPlans.length} planes locales`);
        
        if (isActive !== null) {
          return { 
            meal_plans: localPlans.filter(p => p.is_active === isActive),
            fromLocalStorage: true
          };
        }
        
        return { meal_plans: localPlans, fromLocalStorage: true };
      }
    } catch (error) {
      console.error("Error general en getAll:", error);
      return { meal_plans: [], error: error.message };
    }
  }

  /**
   * Obtener un plan de comida por ID
   * @param {number|string} id - ID del plan
   * @param {boolean} withItems - Incluir elementos en la respuesta
   * @returns {Object} Datos del plan
   */
  async getById(id, withItems = true) {
    try {
      if (!id) {
        throw new Error("ID de plan no proporcionado");
      }
      
      console.log(`Obteniendo plan ${id} con items=${withItems}`);
      
      // Si el ID comienza con "local-", es un plan guardado localmente
      if (id.toString().startsWith('local-')) {
        const localPlans = this.getLocalPlansOnly();
        const localPlan = localPlans.find(p => p.id.toString() === id.toString());
        
        if (!localPlan) {
          throw new Error(`Plan local ${id} no encontrado`);
        }
        
        return localPlan;
      }
      
      // Intentar obtener desde la API
      try {
        const response = await axios.get(`${API_BASE}/meal-plans/${id}`, {
          params: { with_items: withItems },
          timeout: 10000
        });
        
        console.log(`Respuesta para plan ${id}:`, response.data);
        
        // Extraer plan de la respuesta
        let plan = null;
        
        if (response.data && response.data.id) {
          plan = response.data;
        }
        else if (response.data && response.data.plan && response.data.plan.id) {
          plan = response.data.plan;
        }
        else if (response.data && response.data.success && response.data.data && response.data.data.id) {
          plan = response.data.data;
        }
        
        if (!plan) {
          throw new Error(`Plan ${id} no encontrado o formato de respuesta inválido`);
        }
        
        // Asegurar que haya items si no están presentes
        if (!plan.items) {
          plan.items = [];
        }
        
        return plan;
      } catch (apiErr) {
        console.error(`Error de API al obtener plan ${id}:`, apiErr);
        
        // Intentar obtener del localStorage como fallback
        const localPlans = this.getLocalPlansOnly();
        const localPlan = localPlans.find(p => p.id.toString() === id.toString());
        
        if (localPlan) {
          console.log(`Usando plan ${id} desde localStorage`);
          return localPlan;
        } 
        
        throw apiErr; // No se encontró el plan localmente, reenviar error de API
      }
    } catch (error) {
      console.error(`Error al obtener plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Crear un nuevo plan de comida
   * @param {Object} data - Datos del plan
   * @returns {Object} Plan creado
   */
  async create(data) {
    try {
      if (!data) {
        throw new Error("No se proporcionaron datos para crear el plan");
      }
      
      console.log("Creando plan de comida:", data);
      
      // Preparar datos para API
      const planData = {
        plan_name: data.plan_name || data.name || "Nuevo plan",
        name: data.plan_name || data.name || "Nuevo plan",
        is_active: data.is_active !== undefined ? data.is_active : true,
        items: Array.isArray(data.items) ? data.items : [],
        description: data.description || '',
        user_id: data.user_id || '1', // Default a usuario 1 si no se especifica
        // Incluir objetivos nutricionales si existen
        target_calories: data.target_calories,
        target_protein_g: data.target_protein_g,
        target_carbs_g: data.target_carbs_g,
        target_fat_g: data.target_fat_g
      };
      
      // Intentar enviar a la API primero
      try {
        console.log("Enviando a API:", planData);
        const response = await axios.post(`${API_BASE}/meal-plans`, planData, {
          timeout: 10000
        });
        
        console.log("Respuesta de API:", response.data);
        
        // Extraer plan de la respuesta
        let createdPlan = null;
        
        if (response.data && response.data.id) {
          createdPlan = response.data;
        } else if (response.data && response.data.meal_plan && response.data.meal_plan.id) {
          createdPlan = response.data.meal_plan;
        } else if (response.data && response.data.success && response.data.data && response.data.data.id) {
          createdPlan = response.data.data;
        }
        
        if (!createdPlan) {
          throw new Error("API devolvió éxito pero sin datos del plan");
        }
        
        // Limpiar caché
        this.clearCache();
        
        // Fusionar con planes locales
        const localPlans = this.getLocalPlansOnly();
        localPlans.push(createdPlan);
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
        
        return createdPlan;
      } catch (apiErr) {
        console.error("Error de API:", apiErr);
        
        // Usar localStorage como fallback
        const timestamp = Date.now();
        const localPlan = {
          ...planData,
          id: `local-${timestamp}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          _localOnly: true
        };
        
        // Guardar en localStorage
        const localPlans = this.getLocalPlansOnly();
        localPlans.push(localPlan);
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
        
        // Limpiar caché
        this.clearCache();
        
        console.log("Plan guardado localmente:", localPlan);
        return localPlan;
      }
    } catch (error) {
      console.error("Error general al crear:", error);
      throw error;
    }
  }

  /**
   * Actualizar un plan existente
   * @param {number|string} id - ID del plan
   * @param {Object} data - Datos actualizados
   * @returns {Object} Plan actualizado
   */
  async update(id, data) {
    try {
      if (!id) {
        throw new Error("ID de plan no proporcionado para actualizar");
      }
      
      console.log(`Actualizando plan ${id}:`, data);
      
      // Si el ID comienza con "local-", es un plan local
      if (id.toString().startsWith('local-')) {
        console.log(`Actualizando plan local ${id}`);
        const localPlans = this.getLocalPlansOnly();
        const index = localPlans.findIndex(p => p.id.toString() === id.toString());
        
        if (index === -1) {
          throw new Error(`Plan local ${id} no encontrado`);
        }
        
        // Actualizar plan
        const updatedPlan = {
          ...localPlans[index],
          ...data,
          id: id, // Asegurar que ID no cambie
          updated_at: new Date().toISOString(),
          _localOnly: true
        };
        
        localPlans[index] = updatedPlan;
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
        
        // Limpiar caché
        this.clearCache();
        
        console.log(`Plan local ${id} actualizado:`, updatedPlan);
        return updatedPlan;
      }
      
      // Intentar actualizar en API
      try {
        // Preparar datos para enviar a la API
        const planData = { ...data };
        
        // Asegurar que items es un array
        if (planData.items && !Array.isArray(planData.items)) {
          planData.items = [];
        }
        
        console.log(`Enviando petición PUT a API para plan ${id}`);
        const response = await axios.put(`${API_BASE}/meal-plans/${id}`, planData, {
          timeout: 10000
        });
        
        console.log("Respuesta de API:", response.data);
        
        // Extraer plan de la respuesta
        let updatedPlan = null;
        
        if (response.data && response.data.id) {
          updatedPlan = response.data;
        } else if (response.data && response.data.meal_plan && response.data.meal_plan.id) {
          updatedPlan = response.data.meal_plan;
        } else if (response.data && response.data.success && response.data.data && response.data.data.id) {
          updatedPlan = response.data.data;
        }
        
        if (!updatedPlan) {
          throw new Error("API devolvió éxito pero sin datos del plan");
        }
        
        // Actualizar en localStorage si existe
        try {
          const localPlans = this.getLocalPlansOnly();
          const index = localPlans.findIndex(p => p.id.toString() === id.toString());
          
          if (index !== -1) {
            localPlans[index] = updatedPlan;
            localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
          }
        } catch (storageErr) {
          console.warn(`No se pudo actualizar localStorage: ${storageErr.message}`);
        }
        
        // Limpiar caché
        this.clearCache();
        
        return updatedPlan;
      } catch (apiErr) {
        console.error(`Error de API al actualizar plan ${id}:`, apiErr);
        
        // Si falla API pero aún necesitamos actualizar localmente
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
            localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
            
            this.clearCache();
            console.log(`Plan ${id} actualizado en localStorage debido a error de API`);
            
            return updatedPlan;
          }
        } catch (localErr) {
          console.error(`Error de localStorage:`, localErr);
        }
        
        throw apiErr; // Reenviar error de API
      }
    } catch (error) {
      console.error(`Error general al actualizar plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Eliminar un plan de comida
   * @param {number|string} id - ID del plan
   * @returns {boolean} Estado de éxito
   */
  async delete(id) {
    try {
      if (!id) {
        throw new Error("ID de plan no proporcionado para eliminar");
      }
      
      console.log(`Eliminando plan con ID: ${id}`);
      
      // Si es un plan local (ID comienza con "local-"), solo eliminar de localStorage
      if (id.toString().startsWith('local-')) {
        console.log(`Eliminando plan local ${id} de localStorage`);
        const localPlans = this.getLocalPlansOnly();
        const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
        this.clearCache();
        return true;
      }
      
      // Intentar eliminar desde API
      try {
        console.log(`Enviando petición DELETE a API para plan ${id}`);
        await axios.delete(`${API_BASE}/meal-plans/${id}`, {
          timeout: 15000 // Timeout más largo para eliminación
        });
        
        // También eliminar de localStorage si existe
        try {
          const localPlans = this.getLocalPlansOnly();
          const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
          localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
        } catch (err) {
          console.warn(`No se pudo actualizar localStorage después de eliminación: ${err.message}`);
        }
        
        this.clearCache();
        return true;
      } catch (apiErr) {
        console.error(`Error de API al eliminar plan ${id}:`, apiErr);
        
        // Si falla API pero es un ID de plan válido (no uno local),
        // intentar eliminar de localStorage
        try {
          const localPlans = this.getLocalPlansOnly();
          const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
          localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
          this.clearCache();
          console.log(`Plan ${id} eliminado de localStorage debido a error de API`);
          return true;
        } catch (localErr) {
          console.error(`Error de localStorage:`, localErr);
          throw apiErr; // Reenviar error de API
        }
      }
    } catch (error) {
      console.error(`Error general al eliminar plan ${id}:`, error);
      throw error;
    }
  }

  /**
   * Limpiar caché - útil para depuración
   */
  clearCache() {
    this.cachedPlans = null;
    this.lastFetch = 0;
    console.log("Caché limpiada");
  }
}

// Crear y exportar la instancia singleton
export const MealPlanService = new MealPlanServiceClass();