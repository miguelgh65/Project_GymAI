// src/services/AuthService.js
import axios from 'axios';

class AuthService {
  constructor() {
    // Configurar interceptores al inicializar
    this.setupAxiosInterceptors();
  }

  // Configurar interceptores para añadir el token a todas las solicitudes
  setupAxiosInterceptors() {
    axios.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers["Authorization"] = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
  }

  // Iniciar sesión con Google
  async loginWithGoogle(googleToken) {
    try {
      console.log("Enviando token a backend para verificación:", googleToken.substring(0, 20) + "...");
      const response = await axios.post('/api/auth/google/verify', {
        id_token: googleToken
      });
      
      console.log("Respuesta de verificación:", response.data);
      
      if (response.data.success && response.data.access_token) {
        // Guardar token en localStorage
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return response.data;
      } else {
        throw new Error(response.data.message || 'Token no recibido del servidor');
      }
    } catch (error) {
      console.error('Error en loginWithGoogle:', error);
      throw error;
    }
  }

  // Obtener el token almacenado
  getToken() {
    return localStorage.getItem('access_token');
  }

  // Obtener usuario actual desde localStorage
  getCurrentUser() {
    const userJson = localStorage.getItem('user');
    if (userJson) {
      try {
        return JSON.parse(userJson);
      } catch (e) {
        console.error('Error parseando usuario:', e);
        return null;
      }
    }
    return null;
  }

  // Verificar si el usuario está autenticado
  isAuthenticated() {
    return !!this.getToken();
  }

  // Cerrar sesión
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    
    // Opcional: llamar al endpoint de logout en el backend
    try {
      axios.get('/api/logout').catch(err => console.log('Error al notificar logout al servidor:', err));
    } catch (e) {
      console.log('Error al cerrar sesión:', e);
    }
    
    return true;
  }
}

export default new AuthService();