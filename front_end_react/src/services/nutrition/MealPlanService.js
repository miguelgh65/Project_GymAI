// src/services/nutrition/MealPlanService.js
// Service for managing meal plans

import axios from 'axios';
// Asegúrate que API_BASE se importa o define correctamente. 
// Si viene de './constants', verifica que el archivo exista y exporte API_BASE.
// Ejemplo: const API_BASE = 'http://localhost:5050/api/nutrition'; 
import { API_BASE } from './constants'; // O define la constante aquí si no existe

/**
 * Servicio para manejar planes de comida con almacenamiento local robusto
 */
class MealPlanServiceClass {
  constructor() {
    this.LOCAL_STORAGE_KEY = 'local_meal_plans';
    this.cachedPlans = null;
    this.lastFetch = 0;
    // Configurar instancia de axios si necesitas interceptores o headers por defecto
    // this.apiClient = axios.create({ baseURL: API_BASE, timeout: 10000 });
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
      // Limpiar caché para pruebas (puedes comentar esto en producción si prefieres caché persistente)
       this.clearCache(); 

      console.log(`[MealPlanService] Obteniendo planes, filtro activo: ${isActive}`);

      const params = {};
      if (isActive !== null) {
        params.is_active = isActive;
      }

      // Intentar primero la API
      try {
        console.log("[MealPlanService] Intentando obtener planes desde API...");
        const response = await axios.get(`${API_BASE}/meal-plans`, {
          params,
          timeout: 10000 // 10 segundos de timeout
        });

        console.log("[MealPlanService] Respuesta de API recibida:", response.status, response.data);

        // Procesar diferentes formatos de respuesta
        let apiPlans = [];

        if (Array.isArray(response.data)) {
          apiPlans = response.data;
        }
        else if (response.data && Array.isArray(response.data.meal_plans)) {
          apiPlans = response.data.meal_plans;
        }
        // Añade más casos si tu API tiene otros formatos
        else {
          console.warn("[MealPlanService] Formato de respuesta de API no reconocido:", response.data);
          apiPlans = [];
        }

        // Actualizar caché y localStorage
        this.cachedPlans = apiPlans;
        this.lastFetch = Date.now();

        // Guardar en localStorage como respaldo
        try {
          // Opcional: Considera si realmente quieres combinar o solo sobrescribir con los de la API
          const combinedPlans = [...apiPlans]; // Sobrescribe local con API por simplicidad ahora
          localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(combinedPlans));
          console.log(`[MealPlanService] Guardados ${combinedPlans.length} planes de API en localStorage`);
        } catch (storageErr) {
          console.error("[MealPlanService] Error al guardar en localStorage:", storageErr);
        }

        // Filtrar por estado activo si se solicita
        if (isActive !== null) {
          return {
            meal_plans: apiPlans.filter(p => p.is_active === isActive)
          };
        }

        return { meal_plans: apiPlans };
      } catch (apiErr) {
        // Manejo de error de API: Log detallado y fallback a local
        if (axios.isAxiosError(apiErr)) {
            console.error(`[MealPlanService] Error de API (Axios): ${apiErr.message}`, apiErr.response?.status, apiErr.response?.data);
        } else {
            console.error(`[MealPlanService] Error inesperado al llamar a la API:`, apiErr);
        }

        // Usar localStorage como fallback
        const localPlans = this.getLocalPlansOnly();
        console.warn(`[MealPlanService] Error de API, usando ${localPlans.length} planes locales como fallback.`);

        if (isActive !== null) {
          return {
            meal_plans: localPlans.filter(p => p.is_active === isActive),
            fromLocalStorage: true
          };
        }

        return { meal_plans: localPlans, fromLocalStorage: true };
      }
    } catch (error) {
      console.error("[MealPlanService] Error general en getAll:", error);
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

      console.log(`[MealPlanService] Obteniendo plan ${id} con items=${withItems}`);

      // Si el ID comienza con "local-", es un plan guardado localmente
      if (id.toString().startsWith('local-')) {
        const localPlans = this.getLocalPlansOnly();
        const localPlan = localPlans.find(p => p.id.toString() === id.toString());

        if (!localPlan) {
          throw new Error(`Plan local ${id} no encontrado en localStorage`);
        }
        console.log(`[MealPlanService] Devolviendo plan local ${id} desde localStorage`);
        return localPlan;
      }

      // Intentar obtener desde la API
      try {
        const response = await axios.get(`${API_BASE}/meal-plans/${id}`, {
          params: { with_items: withItems },
          timeout: 10000
        });

        console.log(`[MealPlanService] Respuesta de API para plan ${id}:`, response.status, response.data);

        let plan = response.data; // Asumir formato directo, ajustar si es necesario

        if (!plan || !plan.id) {
             console.warn(`[MealPlanService] Plan ${id} no encontrado en API o formato inválido. Respuesta:`, response.data);
             // Intentar buscar en localStorage como fallback ANTES de lanzar error
             const localPlans = this.getLocalPlansOnly();
             const localPlan = localPlans.find(p => p.id.toString() === id.toString());
             if (localPlan) {
                 console.warn(`[MealPlanService] Plan ${id} no encontrado en API, usando versión de localStorage.`);
                 return localPlan;
             }
            throw new Error(`Plan ${id} no encontrado en API ni en localStorage.`);
        }

        // Asegurar que haya items si no están presentes
        if (!plan.items) {
          plan.items = [];
        }

        return plan;
      } catch (apiErr) {
         if (axios.isAxiosError(apiErr)) {
            console.error(`[MealPlanService] Error de API (Axios) al obtener plan ${id}: ${apiErr.message}`, apiErr.response?.status, apiErr.response?.data);
        } else {
            console.error(`[MealPlanService] Error inesperado al obtener plan ${id} de API:`, apiErr);
        }

        // Intentar obtener del localStorage como fallback
        const localPlans = this.getLocalPlansOnly();
        const localPlan = localPlans.find(p => p.id.toString() === id.toString());

        if (localPlan) {
          console.warn(`[MealPlanService] Usando plan ${id} desde localStorage debido a error de API.`);
          return localPlan;
        }

        throw apiErr; // No se encontró el plan localmente, reenviar error de API original
      }
    } catch (error) {
      console.error(`[MealPlanService] Error general al obtener plan ${id}:`, error);
      throw error; // Re-lanzar para que el componente pueda manejarlo
    }
  }

  /**
   * Crear un nuevo plan de comida
   * @param {Object} data - Datos del plan desde el formulario
   * @returns {Object} Plan creado (desde API o local)
   */
  async create(data) {
    try {
      if (!data) {
        throw new Error("No se proporcionaron datos para crear el plan");
      }

      console.log("[MealPlanService] Intentando crear plan con datos:", data);

      // Preparar datos para API (ajusta según necesite tu backend)
      const planDataForApi = {
        plan_name: data.plan_name || "Nuevo plan", // Asegurar que plan_name existe
        description: data.description || '',
        is_active: data.is_active !== undefined ? data.is_active : true,
        // Convertir a números si son strings, o null si están vacíos/inválidos
        target_calories: data.target_calories ? parseFloat(data.target_calories) || null : null,
        target_protein_g: data.target_protein_g ? parseFloat(data.target_protein_g) || null : null,
        target_carbs_g: data.target_carbs_g ? parseFloat(data.target_carbs_g) || null : null,
        target_fat_g: data.target_fat_g ? parseFloat(data.target_fat_g) || null : null,
        // Asegurarse de que 'items' es un array válido
        items: Array.isArray(data.items) ? data.items.map(item => ({
            meal_id: item.meal_id,
            plan_date: item.plan_date, // Asegúrate que está en formato YYYY-MM-DD
            meal_type: item.meal_type || 'Comida', // Valor por defecto si falta
            quantity: parseFloat(item.quantity) || 100, // Valor por defecto
            unit: item.unit || 'g'
        })) : [],
        // Quita user_id si el backend lo obtiene del token de autenticación
        // user_id: data.user_id || '1',
      };

      // +++ AÑADIDO: Log del payload final antes de enviar +++
      console.log("[MealPlanService] Payload final a enviar a API (POST /meal-plans):", JSON.stringify(planDataForApi, null, 2));

      // Intentar enviar a la API primero
      try {
        const response = await axios.post(`${API_BASE}/meal-plans`, planDataForApi, {
          timeout: 15000 // Timeout un poco más largo para creación
          // Aquí deberías añadir headers de autenticación si son necesarios
          // headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log("[MealPlanService] Respuesta de API (create):", response.status, response.data);

        let createdPlan = response.data; // Asumir formato directo

        if (!createdPlan || !createdPlan.id) {
           console.warn("[MealPlanService] API devolvió éxito pero sin datos válidos del plan creado:", response.data);
           // Considerar si lanzar un error o devolver los datos originales con un ID temporal
           throw new Error("La respuesta de la API no contiene un plan válido con ID.");
        }

        // Limpiar caché local del servicio para forzar recarga
        this.clearCache();

        // Opcional: Actualizar localStorage con el plan creado
        try {
            const localPlans = this.getLocalPlansOnly();
            // Evitar duplicados si ya existía localmente por algún motivo
            const filteredPlans = localPlans.filter(p => p.id !== createdPlan.id);
            filteredPlans.push(createdPlan);
            localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
        } catch (storageErr) {
            console.warn("[MealPlanService] No se pudo actualizar localStorage tras crear plan:", storageErr);
        }

        return createdPlan; // Devolver el plan confirmado por la API

      } catch (apiErr) {
        // Manejo de error de API en creación
        if (axios.isAxiosError(apiErr)) {
            console.error(`[MealPlanService] Error de API (Axios) al crear plan: ${apiErr.message}`, apiErr.response?.status, apiErr.response?.data);
        } else {
            console.error(`[MealPlanService] Error inesperado al crear plan vía API:`, apiErr);
        }

        // --- Fallback a localStorage DESACTIVADO por defecto ---
        // Si quieres guardarlo localmente cuando falla la API, descomenta esto:
        /*
        console.warn("[MealPlanService] Falló la creación en API, guardando plan localmente como fallback.");
        const timestamp = Date.now();
        const localPlan = {
          ...planDataForApi, // Usar los datos preparados para la API
          id: `local-${timestamp}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          _localOnly: true // Marcar como solo local
        };

        // Guardar en localStorage
        const localPlans = this.getLocalPlansOnly();
        localPlans.push(localPlan);
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));

        this.clearCache(); // Limpiar caché de planes
        console.log("[MealPlanService] Plan guardado localmente:", localPlan);
        // Podrías lanzar un error aquí para notificar al usuario que se guardó localmente
        // throw new Error("No se pudo guardar en el servidor, el plan se guardó localmente.");
        return localPlan; // O devolver el plan local
        */

         // Por defecto, si falla la API, simplemente relanzamos el error
         throw apiErr;
      }
    } catch (error) {
      console.error("[MealPlanService] Error general al crear plan:", error);
      throw error; // Re-lanzar para que el componente maneje la UI
    }
  }

  /**
   * Actualizar un plan existente
   * @param {number|string} id - ID del plan
   * @param {Object} data - Datos actualizados desde el formulario
   * @returns {Object} Plan actualizado
   */
  async update(id, data) {
    try {
      if (!id) {
        throw new Error("ID de plan no proporcionado para actualizar");
      }

      console.log(`[MealPlanService] Intentando actualizar plan ${id} con datos:`, data);

      // Preparar datos para API (similar a create, pero sin user_id y con ID implícito en URL)
       const planDataForApi = {
        plan_name: data.plan_name,
        description: data.description,
        is_active: data.is_active,
        target_calories: data.target_calories ? parseFloat(data.target_calories) || null : null,
        target_protein_g: data.target_protein_g ? parseFloat(data.target_protein_g) || null : null,
        target_carbs_g: data.target_carbs_g ? parseFloat(data.target_carbs_g) || null : null,
        target_fat_g: data.target_fat_g ? parseFloat(data.target_fat_g) || null : null,
        // 'items' podría necesitar una lógica más compleja si la API requiere diferenciar
        // entre items nuevos, modificados y eliminados. Aquí asumimos que envía la lista completa.
        items: Array.isArray(data.items) ? data.items.map(item => ({
            // Si el item tiene un ID de BD (meal_plan_item_id), incluirlo para la actualización
            id: item.meal_plan_item_id || undefined, // Enviar `id` solo si existe
            meal_id: item.meal_id,
            plan_date: item.plan_date,
            meal_type: item.meal_type || 'Comida',
            quantity: parseFloat(item.quantity) || 100,
            unit: item.unit || 'g'
        })) : [],
      };

      // +++ AÑADIDO: Log del payload final antes de enviar +++
       console.log(`[MealPlanService] Payload final a enviar a API (PUT /meal-plans/${id}):`, JSON.stringify(planDataForApi, null, 2));


      // Si el ID comienza con "local-", actualizar solo en localStorage
      if (id.toString().startsWith('local-')) {
        console.log(`[MealPlanService] Actualizando plan local ${id} en localStorage`);
        const localPlans = this.getLocalPlansOnly();
        const index = localPlans.findIndex(p => p.id.toString() === id.toString());

        if (index === -1) {
          throw new Error(`Plan local ${id} no encontrado para actualizar.`);
        }

        // Actualizar plan local
        const updatedLocalPlan = {
          ...localPlans[index], // Mantener datos originales como created_at
          ...planDataForApi, // Sobrescribir con nuevos datos (ya formateados)
          id: id, // Asegurar que ID no cambie
          updated_at: new Date().toISOString(),
          _localOnly: true
        };

        localPlans[index] = updatedLocalPlan;
        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
        this.clearCache();
        console.log(`[MealPlanService] Plan local ${id} actualizado.`);
        return updatedLocalPlan;
      }

      // Intentar actualizar en API
      try {
        const response = await axios.put(`${API_BASE}/meal-plans/${id}`, planDataForApi, {
          timeout: 15000
           // headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log(`[MealPlanService] Respuesta de API (update ${id}):`, response.status, response.data);

        let updatedPlan = response.data; // Asumir formato directo

        if (!updatedPlan || !updatedPlan.id) {
             console.warn(`[MealPlanService] API devolvió éxito pero sin datos válidos del plan actualizado ${id}:`, response.data);
             throw new Error("La respuesta de la API no contiene un plan actualizado válido con ID.");
        }

        // Actualizar en localStorage si existe
        try {
          const localPlans = this.getLocalPlansOnly();
          const index = localPlans.findIndex(p => p.id.toString() === id.toString());
          if (index !== -1) {
            localPlans[index] = updatedPlan; // Reemplazar con la versión de la API
            localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
          }
        } catch (storageErr) {
          console.warn(`[MealPlanService] No se pudo actualizar localStorage tras actualizar plan ${id}:`, storageErr);
        }

        this.clearCache();
        return updatedPlan;

      } catch (apiErr) {
        // Manejo de error de API en actualización
        if (axios.isAxiosError(apiErr)) {
            console.error(`[MealPlanService] Error de API (Axios) al actualizar plan ${id}: ${apiErr.message}`, apiErr.response?.status, apiErr.response?.data);
        } else {
            console.error(`[MealPlanService] Error inesperado al actualizar plan ${id} vía API:`, apiErr);
        }

        // --- Fallback a localStorage DESACTIVADO por defecto ---
        // Si falla la API, podríamos intentar actualizar localmente como fallback,
        // pero esto puede llevar a inconsistencias. Por defecto, relanzamos el error.
        /*
        console.warn(`[MealPlanService] Falló la actualización en API para ${id}, intentando actualizar localmente.`);
         try {
           const localPlans = this.getLocalPlansOnly();
           const index = localPlans.findIndex(p => p.id.toString() === id.toString());
           if (index !== -1) {
             const updatedLocalPlan = { ...localPlans[index], ...planDataForApi, id: id, updated_at: new Date().toISOString(), _localOnly: true };
             localPlans[index] = updatedLocalPlan;
             localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(localPlans));
             this.clearCache();
             console.log(`[MealPlanService] Plan ${id} actualizado en localStorage debido a error de API.`);
             // throw new Error("No se pudo actualizar en el servidor, los cambios se guardaron localmente.");
             return updatedLocalPlan;
           }
         } catch (localErr) {
           console.error(`[MealPlanService] Error al intentar actualizar localStorage como fallback:`, localErr);
         }
        */
        throw apiErr; // Reenviar error de API original
      }
    } catch (error) {
      console.error(`[MealPlanService] Error general al actualizar plan ${id}:`, error);
      throw error; // Re-lanzar para que el componente maneje la UI
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

      console.log(`[MealPlanService] Intentando eliminar plan con ID: ${id}`);

      // Si es un plan local (ID comienza con "local-"), solo eliminar de localStorage
      if (id.toString().startsWith('local-')) {
        console.log(`[MealPlanService] Eliminando plan local ${id} de localStorage`);
        const localPlans = this.getLocalPlansOnly();
        const initialLength = localPlans.length;
        const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
        if (filteredPlans.length < initialLength) {
            localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
            this.clearCache();
            console.log(`[MealPlanService] Plan local ${id} eliminado.`);
            return true;
        } else {
            console.warn(`[MealPlanService] Plan local ${id} no encontrado en localStorage para eliminar.`);
            return false; // O lanzar error si se prefiere
        }
      }

      // Intentar eliminar desde API
      try {
        console.log(`[MealPlanService] Enviando petición DELETE a API para plan ${id}`);
        const response = await axios.delete(`${API_BASE}/meal-plans/${id}`, {
          timeout: 15000 // Timeout más largo para eliminación
           // headers: { 'Authorization': `Bearer ${token}` }
        });

         console.log(`[MealPlanService] Respuesta de API (delete ${id}):`, response.status);

        // También eliminar de localStorage si existe
        try {
          const localPlans = this.getLocalPlansOnly();
          const initialLength = localPlans.length;
          const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
           if (filteredPlans.length < initialLength) {
                localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
                 console.log(`[MealPlanService] Plan ${id} también eliminado de localStorage.`);
           }
        } catch (storageErr) {
          console.warn(`[MealPlanService] No se pudo actualizar localStorage después de eliminar plan ${id}:`, storageErr);
        }

        this.clearCache();
        return true; // Éxito en API

      } catch (apiErr) {
         // Manejo de error de API en eliminación
        if (axios.isAxiosError(apiErr)) {
            console.error(`[MealPlanService] Error de API (Axios) al eliminar plan ${id}: ${apiErr.message}`, apiErr.response?.status, apiErr.response?.data);
             // Si la API devuelve 404 (Not Found), podríamos considerarlo un "éxito" si el objetivo era que no existiera.
             if (apiErr.response?.status === 404) {
                 console.warn(`[MealPlanService] La API devolvió 404 al intentar eliminar plan ${id}. Asumiendo que ya no existe.`);
                 // Intentar eliminar de localStorage de todas formas
                 try {
                    const localPlans = this.getLocalPlansOnly();
                    const initialLength = localPlans.length;
                    const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
                    if (filteredPlans.length < initialLength) {
                        localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
                         console.log(`[MealPlanService] Plan ${id} eliminado de localStorage tras 404 de API.`);
                    }
                    this.clearCache();
                    return true; // Considerar 404 como éxito de eliminación
                 } catch(storageErr) {
                     console.error("[MealPlanService] Error limpiando localStorage tras 404 de API:", storageErr);
                     // Continuar para relanzar el error original de API
                 }
             }
        } else {
            console.error(`[MealPlanService] Error inesperado al eliminar plan ${id} vía API:`, apiErr);
        }


        // --- Fallback a localStorage DESACTIVADO por defecto ---
        // Podríamos eliminar localmente si falla la API, pero es arriesgado.
        /*
         console.warn(`[MealPlanService] Falló la eliminación en API para ${id}, intentando eliminar localmente.`);
         try {
           const localPlans = this.getLocalPlansOnly();
           const initialLength = localPlans.length;
           const filteredPlans = localPlans.filter(p => p.id.toString() !== id.toString());
           if (filteredPlans.length < initialLength) {
             localStorage.setItem(this.LOCAL_STORAGE_KEY, JSON.stringify(filteredPlans));
             this.clearCache();
             console.log(`[MealPlanService] Plan ${id} eliminado de localStorage debido a error de API.`);
             // throw new Error("No se pudo eliminar en el servidor, se eliminó localmente.");
             return true;
           }
         } catch (localErr) {
           console.error(`[MealPlanService] Error al intentar eliminar de localStorage como fallback:`, localErr);
         }
        */

        throw apiErr; // Reenviar error de API original si no fue 404 manejado
      }
    } catch (error) {
      console.error(`[MealPlanService] Error general al eliminar plan ${id}:`, error);
      throw error; // Re-lanzar
    }
  }

  /**
   * Limpiar caché local del servicio
   */
  clearCache() {
    this.cachedPlans = null;
    this.lastFetch = 0;
    console.log("[MealPlanService] Caché de planes limpiada.");
  }
}

// Crear y exportar la instancia singleton
export const MealPlanService = new MealPlanServiceClass();