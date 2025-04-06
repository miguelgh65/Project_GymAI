import axios from 'axios';

/**
 * Servicio centralizado para el manejo de autenticación
 */
const AuthService = {
  /**
   * Obtiene el usuario actualmente autenticado
   * @returns {Promise<Object|null>} Datos del usuario o null si no está autenticado o hay error
   */
  getCurrentUser: async () => {
    try {
      // *** CAMBIO AQUÍ: Añadir /api/ ***
      const response = await axios.get('/api/current-user');
      // Asume que la cookie HttpOnly se envía automáticamente por el navegador
      // si axios está configurado con withCredentials=true (hecho en App.js o index.js)

      if (response.data.success && response.data.user) {
        console.log("Usuario actual obtenido:", response.data.user);
        return response.data.user;
      }
      console.log("Respuesta de /api/current-user no exitosa o sin usuario:", response.data);
      return null;
    } catch (error) {
      // Es normal recibir 401 si no hay sesión, no loggear como error grave en ese caso
      if (error.response && error.response.status === 401) {
         console.log('No hay sesión de usuario activa (401)');
      } else {
         console.error('Error al obtener usuario actual:', error.response?.data || error.message);
      }
      return null; // Devuelve null en caso de error o no autenticado
    }
  },

  /**
   * Cierra la sesión del usuario
   * @returns {Promise<boolean>} Éxito del cierre de sesión
   */
  logout: async () => {
    try {
      console.log("Iniciando proceso de logout...");
      const cacheBuster = new Date().getTime();

      // *** CAMBIO AQUÍ: Añadir /api/ ***
      // Usar la ruta correcta del backend para logout
      const logoutUrl = `/api/logout?_=${cacheBuster}`;

      // Hacer la petición GET para logout. Axios seguirá redirecciones por defecto.
      // No necesitamos manejar la redirección manualmente aquí si el backend la hace.
      await axios.get(logoutUrl, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
        // No necesitamos maxRedirects: 0 aquí, dejamos que axios siga la redirección del backend
      });

      // Si la llamada a axios no lanza error, asumimos que el proceso va bien
      // y la redirección ocurrirá o ya ocurrió.
      console.log("Petición de logout enviada. El backend debería redirigir.");

      // Forzar recarga a la página de login como fallback o para asegurar limpieza de estado en React
      // Podrías querer esperar un poco o confiar en la redirección del backend.
      // Comentado por ahora para confiar en la redirección del backend primero.
      // window.location.href = '/login?logout=frontend';

      return true;

    } catch (error) {
      // Incluso si la petición GET /api/logout falla (ej. 500), intentamos forzar
      // la redirección al login en el cliente.
      console.error('Error durante la petición de logout:', error.response?.data || error.message);

      try {
        const cacheBuster = new Date().getTime();
        // Forzar redirección al login desde el frontend como último recurso
        window.location.href = '/login?logout=error&t=' + cacheBuster;
      } catch (e) {
        console.error('Error en redirección forzada después de fallo de logout:', e);
      }

      return false; // Indicar que hubo un error en el proceso
    }
  }
};

export default AuthService;