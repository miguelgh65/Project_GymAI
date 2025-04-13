// src/services/AuthService.js
import axios from 'axios';

// API base URL from environment
const API_URL = process.env.REACT_APP_API_BASE_URL || '';

class AuthService {
  // Google authentication
  static async verifyGoogleToken(token) {
    try {
      console.log(`Enviando token Google a ${API_URL}/api/auth/google/verify`);
      const response = await axios.post(`${API_URL}/api/auth/google/verify`, {
        id_token: token
      });
      
      console.log("Respuesta del servidor:", response.data);
      
      if (response.data.success && response.data.access_token) {
        // Guardar usuario y token en localStorage
        localStorage.setItem('user', JSON.stringify(response.data.user));
        localStorage.setItem('token', response.data.access_token);
        
        // Para compatibilidad con código existente que use este nombre
        localStorage.setItem('access_token', response.data.access_token);
        
        return response.data;
      } else {
        console.warn("Respuesta de verificación no exitosa:", response.data);
        return null;
      }
    } catch (error) {
      console.error('Error verificando token de Google:', error.response?.data || error.message);
      throw error;
    }
  }

  // Obtener usuario actual del localStorage
  static getCurrentUser() {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch (error) {
      console.error('Error al parsear usuario de localStorage:', error);
      return null;
    }
  }

  // Obtener token del localStorage
  static getToken() {
    // Primero intentar con 'token' (nuevo nombre), luego 'access_token' (nombre antiguo)
    return localStorage.getItem('token') || localStorage.getItem('access_token');
  }

  // Verificar si el usuario está logueado
  static isLoggedIn() {
    return !!this.getToken() && !!this.getCurrentUser();
  }

  // Logout (eliminar datos de localStorage)
  static async logout() {
    // Primero intentar el logout en el servidor
    try {
      // Añadimos el token de autorización
      const token = this.getToken();
      if (token) {
        await axios.get(`${API_URL}/api/logout`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      } else {
        await axios.get(`${API_URL}/api/logout`);
      }
    } catch (error) {
      console.warn('Error en logout del servidor:', error);
      // Continuar con logout local incluso si falla el servidor
    }
    
    // Limpiar localStorage (ambos nombres de token)
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    
    return true;
  }

  // Obtener datos de usuario desde el servidor (verifica validez del token)
  static async fetchCurrentUser() {
    try {
      const token = this.getToken();
      if (!token) return null;
      
      const response = await axios.get(`${API_URL}/api/current-user`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.data.success && response.data.user) {
        // Actualizar localStorage con los datos más recientes
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return response.data.user;
      }
      
      return null;
    } catch (error) {
      // Si es 401 Unauthorized, limpiar localStorage
      if (error.response && error.response.status === 401) {
        this.logout();
      }
      console.error('Error al obtener usuario actual:', error);
      return null;
    }
  }
}

export default AuthService;