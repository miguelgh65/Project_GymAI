// front_end_react/src/services/nutrition/TrackingService.js
import ApiService from '../ApiService';

/**
 * Service for handling nutrition tracking data
 */
class TrackingService {
  /**
   * Save or update daily tracking information
   * @param {Object} trackingData - The tracking data object
   * @param {string} trackingData.tracking_date - Date in YYYY-MM-DD format
   * @param {Object} trackingData.completed_meals - Map of meal types to boolean completion status
   * @param {string} [trackingData.calorie_note] - Optional note about calories
   * @param {number} [trackingData.actual_calories] - Optional actual calories consumed
   * @param {number} [trackingData.excess_deficit] - Optional calculated excess/deficit
   * @returns {Promise<Object>} The saved tracking data
   */
  static async saveTracking(trackingData) {
    try {
      const response = await ApiService.post('/api/nutrition/tracking', trackingData);
      return response.data;
    } catch (error) {
      console.error('Error saving tracking data:', error);
      throw error;
    }
  }

  /**
   * Get tracking data for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<Object>} The tracking data for the date
   */
  static async getTrackingForDay(date) {
    try {
      const response = await ApiService.get(`/api/nutrition/tracking/day/${date}`);
      return response.data.tracking;
    } catch (error) {
      console.error(`Error fetching tracking for ${date}:`, error);
      
      // Return null instead of throwing if tracking doesn't exist yet
      if (error.response && error.response.status === 404) {
        return null;
      }
      
      throw error;
    }
  }

  /**
   * Get tracking data for a week
   * @param {string} [startDate] - Start date in YYYY-MM-DD format (Monday). If omitted, current week is used.
   * @returns {Promise<Array>} Array of tracking data for the week
   */
  static async getTrackingForWeek(startDate) {
    try {
      const url = startDate 
        ? `/api/nutrition/tracking/week?start_date=${startDate}`
        : '/api/nutrition/tracking/week';
        
      const response = await ApiService.get(url);
      return response.data.tracking || [];
    } catch (error) {
      console.error('Error fetching weekly tracking:', error);
      
      // Return empty array if no tracking exists yet
      if (error.response && error.response.status === 404) {
        return [];
      }
      
      throw error;
    }
  }

  /**
   * Get summary statistics for a week
   * @param {string} [startDate] - Start date in YYYY-MM-DD format (Monday). If omitted, current week is used.
   * @returns {Promise<Object>} Weekly summary statistics
   */
  static async getWeeklySummary(startDate) {
    try {
      const url = startDate 
        ? `/api/nutrition/tracking/summary?start_date=${startDate}`
        : '/api/nutrition/tracking/summary';
        
      const response = await ApiService.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching weekly summary:', error);
      
      // Return default summary if no data exists yet
      if (error.response && error.response.status === 404) {
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
      
      throw error;
    }
  }

  /**
   * Delete tracking data for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<boolean>} True if successful
   */
  static async deleteTracking(date) {
    try {
      await ApiService.delete(`/api/nutrition/tracking/${date}`);
      return true;
    } catch (error) {
      console.error(`Error deleting tracking for ${date}:`, error);
      throw error;
    }
  }
  
  /**
   * Calculate calorie excess/deficit based on target and actual calories
   * @param {number} targetCalories - Target daily calories
   * @param {number} actualCalories - Actual calories consumed
   * @returns {number} Excess (positive) or deficit (negative) amount
   */
  static calculateExcessDeficit(targetCalories, actualCalories) {
    if (typeof targetCalories !== 'number' || typeof actualCalories !== 'number') {
      return 0;
    }
    return actualCalories - targetCalories;
  }
}

export default TrackingService;