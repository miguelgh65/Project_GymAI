/**
 * Módulo de API - Funciones para interactuar con la API del backend
 */

const API = {
    /**
     * Realiza una solicitud GET a la API
     * 
     * @param {string} endpoint - Punto final de la API
     * @param {Object} params - Parámetros de la consulta (opcional)
     * @returns {Promise} Promesa que resuelve a los datos de la respuesta JSON
     */
    get: async function(endpoint, params = {}) {
        try {
            // Construir la URL con parámetros
            const url = new URL(endpoint, window.location.origin);
            
            // Añadir parámetros a la URL si existen
            if (Object.keys(params).length > 0) {
                Object.keys(params).forEach(key => {
                    if (params[key] !== null && params[key] !== undefined) {
                        url.searchParams.append(key, params[key]);
                    }
                });
            }
            
            // Realizar la petición
            const response = await fetch(url.toString());
            
            // Verificar si la respuesta fue exitosa
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            // Convertir respuesta a JSON
            return await response.json();
        } catch (error) {
            console.error(`Error en API.get(${endpoint}):`, error);
            throw error;
        }
    },
    
    /**
     * Realiza una solicitud POST a la API con datos de formulario
     * 
     * @param {string} endpoint - Punto final de la API
     * @param {FormData|Object} data - Datos a enviar (FormData u objeto)
     * @param {boolean} isFormData - Indica si los datos son FormData (true) o un objeto JSON (false)
     * @returns {Promise} Promesa que resuelve a los datos de la respuesta JSON
     */
    post: async function(endpoint, data, isFormData = false) {
        try {
            // Configurar opciones de la petición
            const options = {
                method: 'POST',
                headers: {},
                body: data
            };
            
            // Si los datos no son FormData, convertirlos a JSON
            if (!isFormData) {
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify(data);
            }
            
            // Realizar la petición
            const response = await fetch(endpoint, options);
            
            // Verificar si la respuesta fue exitosa
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            // Convertir respuesta a JSON
            return await response.json();
        } catch (error) {
            console.error(`Error en API.post(${endpoint}):`, error);
            throw error;
        }
    },
    
    /**
     * Realiza una solicitud POST a la API con datos de formulario
     * 
     * @param {string} endpoint - Punto final de la API
     * @param {FormData} formData - Datos del formulario
     * @returns {Promise} Promesa que resuelve a los datos de la respuesta JSON
     */
    postForm: async function(endpoint, formData) {
        return this.post(endpoint, formData, true);
    },
    
    /**
     * Realiza una solicitud POST a la API con datos JSON
     * 
     * @param {string} endpoint - Punto final de la API
     * @param {Object} data - Datos a enviar como JSON
     * @returns {Promise} Promesa que resuelve a los datos de la respuesta JSON
     */
    postJSON: async function(endpoint, data) {
        return this.post(endpoint, data, false);
    }
};

// Exportar módulo API
window.API = API;