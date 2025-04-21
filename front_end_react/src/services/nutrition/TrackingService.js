// src/services/nutrition/TrackingService.js
import axios from 'axios';
import { API_BASE } from './constants';

/**
 * Service for managing nutrition tracking data
 */
class TrackingServiceClass {
  /**
   * Save or update daily tracking information
   * @param {Object} trackingData - The tracking data object
   * @param {string} trackingData.tracking_date - Date in YYYY-MM-DD format
   * @param {Object} trackingData.completed_meals - Map of meal types to boolean completion status
   * @param {string} [trackingData.calorie_note] - Optional note about calories
   * @param {number} [trackingData.actual_calories] - Optional actual calories consumed
   * @param {number} [trackingData.excess_deficit] - Optional excess/deficit value
   * @returns {Promise<Object>} The saved tracking data
   */
  async saveTracking(trackingData) {
    try {
      console.log("TrackingService: Guardando datos de seguimiento:", trackingData);
      const response = await axios.post(`${API_BASE}/tracking`, trackingData);
      console.log("TrackingService: Respuesta de guardado:", response.data);
      return response.data;
    } catch (error) {
      console.error('Error al guardar datos de seguimiento:', error);
      throw error;
    }
  }

  /**
   * Get tracking data for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<Object|null>} The tracking data for the date or null if not found
   */
  async getTrackingForDay(date) {
    try {
      console.log(`TrackingService: Obteniendo seguimiento para ${date}`);
      const response = await axios.get(`${API_BASE}/tracking/day/${date}`);
      console.log("TrackingService: Datos de seguimiento recibidos:", response.data);
      
      // Handle different response formats
      if (response.data?.tracking) {
        return response.data.tracking;
      } else if (response.data && typeof response.data === 'object') {
        return response.data;
      }
      
      return null;
    } catch (error) {
      // Si es error 404, simplemente devolvemos null (no hay datos todavía)
      if (error.response && error.response.status === 404) {
        console.log(`TrackingService: No hay datos para ${date} (404)`);
        return null;
      }
      
      console.error(`Error al obtener seguimiento para ${date}:`, error);
      throw error;
    }
  }

  /**
   * Get tracking data for a week
   * @param {string} [startDate] - Start date in YYYY-MM-DD format (defaults to current week)
   * @returns {Promise<Array>} Array of tracking data for the week
   */
  async getTrackingForWeek(startDate = null) {
    try {
      let url = `${API_BASE}/tracking/week`;
      if (startDate) {
        url += `?start_date=${startDate}`;
      }
      
      console.log(`TrackingService: Obteniendo seguimiento semanal desde ${startDate || 'esta semana'}`);
      const response = await axios.get(url);
      console.log("TrackingService: Datos semanales recibidos:", response.data);
      
      // Handle different response formats
      if (response.data?.tracking) {
        return response.data.tracking;
      } else if (Array.isArray(response.data)) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      if (error.response && error.response.status === 404) {
        console.log("TrackingService: No hay datos semanales (404)");
        return [];
      }
      
      console.error('Error al obtener seguimiento semanal:', error);
      throw error;
    }
  }

  /**
   * Get summary statistics for a week
   * @param {string} [startDate] - Start date in YYYY-MM-DD format
   * @returns {Promise<Object>} Weekly summary statistics
   */
  async getWeeklySummary(startDate = null) {
    try {
      let url = `${API_BASE}/tracking/summary`;
      if (startDate) {
        url += `?start_date=${startDate}`;
      }
      
      console.log(`TrackingService: Obteniendo resumen semanal desde ${startDate || 'esta semana'}`);
      const response = await axios.get(url);
      console.log("TrackingService: Resumen semanal recibido:", response.data);
      
      return response.data;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        console.log("TrackingService: No hay resumen semanal (404)");
        // Devolver objeto de resumen por defecto
        return {
          total_days_tracked: 0,
          average_calories: 0,
          total_excess_deficit: 0,
          meals_completion: {
            Desayuno: 0,
            Almuerzo: 0,
            Comida: 0,
            Merienda: 0,
            Cena: 0
          }
        };
      }
      
      console.error('Error al obtener resumen semanal:', error);
      throw error;
    }
  }

  /**
   * Delete tracking data for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<boolean>} True if successful
   */
  async deleteTracking(date) {
    try {
      console.log(`TrackingService: Eliminando seguimiento de ${date}`);
      await axios.delete(`${API_BASE}/tracking/${date}`);
      console.log(`TrackingService: Seguimiento de ${date} eliminado con éxito`);
      return true;
    } catch (error) {
      console.error(`Error al eliminar seguimiento de ${date}:`, error);
      throw error;
    }
  }
  
  /**
   * Calculate calorie excess/deficit based on target and actual calories
   * @param {number} targetCalories - Target daily calories
   * @param {number} actualCalories - Actual calories consumed
   * @returns {number} Excess (positive) or deficit (negative) amount
   */
  calculateExcessDeficit(targetCalories, actualCalories) {
    if (typeof targetCalories !== 'number' || typeof actualCalories !== 'number') {
      return 0;
    }
    return actualCalories - targetCalories;
  }
}

// Crear y exportar la instancia singleton
export const TrackingService = new TrackingServiceClass();

// Exportación por defecto para compatibilidad
export default TrackingService;