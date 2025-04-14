// src/services/AuthService.js - mejorado con mejor manejo de errores
import axios from 'axios';

class AuthService {
  constructor() {
    // Configurar interceptores al inicializar
    this.setupAxiosInterceptors();

    // Flag para evitar intentos repetidos de interceptores
    this.interceptorsSetup = false;
  }

  // Configurar interceptores para añadir el token a todas las solicitudes
  setupAxiosInterceptors() {
    if (this.interceptorsSetup) {
      console.log("Interceptores ya configurados, evitando duplicación");
      return;
    }

    console.log("Configurando interceptores de Axios");

    axios.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers["Authorization"] = `Bearer ${token}`;
          console.log(`Request a ${config.url}: Token añadido al header Authorization`);
        } else {
          console.log(`Request a ${config.url}: Sin token disponible`);
        }
        return config;
      },
      (error) => {
        console.error("Error en interceptor de petición:", error);
        return Promise.reject(error);
      }
    );

    // Interceptor para respuestas
    axios.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        // Log detallado de errores de respuesta
        if (error.response) {
          // La petición fue hecha y el servidor respondió con un código de estado
          // fuera del rango 2xx
          console.error(`Error de respuesta (${error.response.status}):`, error.response.data);
          console.log(`Headers:`, error.response.headers);
        } else if (error.request) {
          // La petición fue hecha pero no se recibió respuesta
          console.error(`Sin respuesta del servidor:`, error.request);
        } else {
          // Algo ocurrió en el setup de la petición que lanzó un error
          console.error(`Error de configuración:`, error.message);
        }
        return Promise.reject(error);
      }
    );

    this.interceptorsSetup = true;
    console.log("Interceptores de Axios configurados correctamente");
  }

  // Iniciar sesión con Google
  async loginWithGoogle(googleToken) {
    try {
      console.log("Enviando token a backend para verificación:", googleToken.substring(0, 20) + "...");
      
      // Verificar la URL base
      console.log(`URL base para login: ${window.location.origin}`);
      
      // Guardar un timestamp para comparar con cookies posteriores
      const timestamp = new Date().toISOString();
      try {
        localStorage.setItem('auth_request_time', timestamp);
      } catch (e) {
        console.error("Error al guardar timestamp en localStorage:", e);
      }

      const response = await axios.post('/api/auth/google/verify', {
        id_token: googleToken
      });
      
      console.log("Respuesta de verificación:", response.data);
      
      if (response.data.success && response.data.access_token) {
        // Intentar guardar token en localStorage con manejo mejorado de errores
        try {
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('user', JSON.stringify(response.data.user));
          console.log("Token y datos de usuario guardados en localStorage");
        } catch (storageError) {
          console.error("Error al guardar en localStorage:", storageError);
          // Intento de fallback a cookies
          try {
            document.cookie = `access_token=${response.data.access_token}; path=/;`;
            document.cookie = `user=${JSON.stringify(response.data.user)}; path=/;`;
            console.log("Token y datos de usuario guardados en cookies como fallback");
          } catch (cookieError) {
            console.error("Error al guardar en cookies:", cookieError);
            // Si también falla cookies, aún devolvemos success pero avisamos
            console.warn("No se pudo almacenar la sesión localmente. La sesión podría perderse al recargar.");
          }
        }
        return response.data;
      } else {
        const errorMsg = response.data.message || 'Token no recibido del servidor';
        console.error(`Error en respuesta del servidor: ${errorMsg}`);
        throw new Error(errorMsg);
      }
    } catch (error) {
      console.error('Error en loginWithGoogle:', error);
      
      // Diagnostico extenso
      console.log("--- Diagnóstico de Error en Login ---");
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Data:`, error.response.data);
        console.log(`Headers:`, error.response.headers);
      } else {
        console.log(`Sin respuesta HTTP. Error: ${error.message}`);
      }
      console.log("--- Fin Diagnóstico ---");
      
      throw error;
    }
  }

  // Obtener el token con verificación extensiva
  getToken() {
    let token = null;
    
    // Intento principal desde localStorage
    try {
      token = localStorage.getItem('access_token');
      if (token) {
        console.log("Token encontrado en localStorage");
        return token;
      }
    } catch (e) {
      console.warn("Error al acceder a localStorage:", e.message);
    }
    
    // Intento de fallback desde cookies
    try {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('access_token=')) {
          token = cookie.substring('access_token='.length);
          console.log("Token encontrado en cookies");
          
          // Intentar migrar de cookie a localStorage si es posible
          try {
            localStorage.setItem('access_token', token);
            console.log("Token migrado de cookie a localStorage");
          } catch (storageError) {
            console.warn("No se pudo migrar el token a localStorage:", storageError.message);
          }
          
          return token;
        }
      }
    } catch (e) {
      console.warn("Error al acceder a cookies:", e.message);
    }
    
    console.warn("No se encontró token de autenticación");
    return null;
  }

  // Obtener usuario actual desde localStorage con fallback a cookies
  getCurrentUser() {
    let userJson = null;
    
    // Intento principal desde localStorage
    try {
      userJson = localStorage.getItem('user');
      if (userJson) {
        console.log("Datos de usuario encontrados en localStorage");
        try {
          return JSON.parse(userJson);
        } catch (e) {
          console.error('Error parseando usuario desde localStorage:', e);
          // No return aquí para intentar el fallback
        }
      }
    } catch (e) {
      console.warn("Error al acceder a localStorage para usuario:", e.message);
    }
    
    // Intento de fallback desde cookies
    try {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('user=')) {
          userJson = cookie.substring('user='.length);
          console.log("Datos de usuario encontrados en cookies");
          try {
            const userData = JSON.parse(userJson);
            
            // Intentar migrar de cookie a localStorage si es posible
            try {
              localStorage.setItem('user', userJson);
              console.log("Datos de usuario migrados de cookie a localStorage");
            } catch (storageError) {
              console.warn("No se pudo migrar datos de usuario a localStorage:", storageError.message);
            }
            
            return userData;
          } catch (e) {
            console.error('Error parseando usuario desde cookie:', e);
          }
        }
      }
    } catch (e) {
      console.warn("Error al acceder a cookies para usuario:", e.message);
    }
    
    console.warn("No se encontraron datos de usuario");
    return null;
  }

  // Verificar si el usuario está autenticado
  isAuthenticated() {
    return !!this.getToken();
  }

  // Cerrar sesión con limpieza extensiva
  logout() {
    let success = true;
    
    // Limpiar localStorage
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      console.log("Token y datos de usuario eliminados de localStorage");
    } catch (e) {
      console.error('Error al limpiar localStorage:', e);
      success = false;
    }
    
    // Limpiar cookies
    try {
      document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      document.cookie = "user=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      console.log("Token y datos de usuario eliminados de cookies");
    } catch (e) {
      console.error('Error al limpiar cookies:', e);
      success = false;
    }
    
    // Opcional: llamar al endpoint de logout en el backend
    try {
      axios.get('/api/logout')
        .then(() => console.log('Notificado logout al servidor'))
        .catch(err => console.log('Error al notificar logout al servidor:', err));
    } catch (e) {
      console.log('Error al llamar a endpoint de logout:', e);
      // No afecta al éxito del logout del cliente
    }
    
    return success;
  }
}

export default new AuthService();