// src/services/ApiService.js
import axios from 'axios';
import AuthService from './AuthService';

// Crear una instancia de axios configurada
const API_URL = process.env.REACT_APP_API_BASE_URL || '';

// ¡IMPORTANTE! - Configurar axios para incluir automáticamente el token JWT en cada solicitud
axios.interceptors.request.use(
  (config) => {
    const token = AuthService.getToken();
    if (token) {
      // Añadir token a todas las solicitudes
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de autenticación
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Si recibimos un 401, redirigir a login
      console.log('Error 401 detectado - sesión expirada o token inválido');
      AuthService.logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

class ApiService {
  // Exercise logging
  static async logExercise(exerciseData) {
    try {
      const response = await axios.post(`${API_URL}/api/log-exercise`, {
        exercise_data: exerciseData
      });
      return response.data;
    } catch (error) {
      console.error('Error logging exercise:', error);
      throw error;
    }
  }

  // Get exercise logs
  static async getExerciseLogs(days = 7) {
    try {
      const response = await axios.get(`${API_URL}/api/logs?days=${days}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching exercise logs:', error);
      throw error;
    }
  }

  // Get today's routine
  static async getTodayRoutine() {
    try {
      const response = await axios.get(`${API_URL}/api/rutina_hoy`);
      return response.data;
    } catch (error) {
      console.error('Error fetching today\'s routine:', error);
      throw error;
    }
  }

  // Get full routine
  static async getFullRoutine() {
    try {
      const response = await axios.get(`${API_URL}/api/rutina`);
      return response.data;
    } catch (error) {
      console.error('Error fetching routine:', error);
      throw error;
    }
  }

  // Save routine
  static async saveRoutine(routineData) {
    try {
      const response = await axios.post(`${API_URL}/api/rutina`, {
        rutina: routineData
      });
      return response.data;
    } catch (error) {
      console.error('Error saving routine:', error);
      throw error;
    }
  }

  // Reset today's routine
  static async resetTodayRoutine() {
    try {
      const response = await axios.post(`${API_URL}/api/log-exercise`, {
        exercise_data: 'RESET_ROUTINE'
      });
      return response.data;
    } catch (error) {
      console.error('Error resetting today\'s routine:', error);
      throw error;
    }
  }

  // Get exercise statistics
  static async getExerciseStats(exercise = null, fromDate = null, toDate = null) {
    try {
      let url = `${API_URL}/api/ejercicios_stats`;
      const params = [];
      
      if (exercise) params.push(`ejercicio=${encodeURIComponent(exercise)}`);
      if (fromDate) params.push(`desde=${fromDate}`);
      if (toDate) params.push(`hasta=${toDate}`);
      
      if (params.length > 0) {
        url += `?${params.join('&')}`;
      }
      
      const response = await axios.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching exercise stats:', error);
      throw error;
    }
  }

  // Get calendar heatmap data
  static async getCalendarHeatmap(year = new Date().getFullYear()) {
    try {
      const response = await axios.get(`${API_URL}/api/calendar_heatmap?year=${year}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching calendar heatmap data:', error);
      throw error;
    }
  }

  // Fitbit API methods
  static async connectFitbit() {
    try {
      // Esta llamada redireccionará al usuario a Fitbit OAuth
      window.location.href = `${API_URL}/api/fitbit/connect`;
      return { success: true };
    } catch (error) {
      console.error('Error connecting to Fitbit:', error);
      throw error;
    }
  }

  static async disconnectFitbit() {
    try {
      const response = await axios.post(`${API_URL}/api/fitbit/disconnect`);
      return response.data;
    } catch (error) {
      console.error('Error disconnecting Fitbit:', error);
      throw error;
    }
  }

  static async getFitbitData(dataType, date = null, detailLevel = null) {
    try {
      let url = `${API_URL}/api/fitbit/data?data_type=${dataType}`;
      
      if (date) url += `&date=${date}`;
      if (detailLevel) url += `&detail_level=${detailLevel}`;
      
      const response = await axios.get(url);
      return response.data;
    } catch (error) {
      console.error(`Error fetching Fitbit ${dataType} data:`, error);
      throw error;
    }
  }
  
  // User methods
  static async getCurrentUser() {
    try {
      const response = await axios.get(`${API_URL}/api/current-user`);
      return response.data;
    } catch (error) {
      console.error('Error fetching current user:', error);
      throw error;
    }
  }
  
  // Telegram methods
  static async generateTelegramCode() {
    try {
      const response = await axios.post(`${API_URL}/api/generate-link-code`);
      return response.data;
    } catch (error) {
      console.error('Error generating Telegram code:', error);
      throw error;
    }
  }

  static async verifyTelegramCode(code, telegramId) {
    try {
      const response = await axios.post(`${API_URL}/api/verify-link-code`, {
        code: code,
        telegram_id: telegramId
      });
      return response.data;
    } catch (error) {
      console.error('Error verifying Telegram code:', error);
      throw error;
    }
  }
}

export default ApiService;