/**
 * Módulo de datos del Dashboard
 * Maneja la obtención y procesamiento de datos para el dashboard
 */

const DashboardData = {
    /**
     * Obtiene datos de ejercicios con filtros
     * 
     * @param {string} ejercicio - Nombre del ejercicio
     * @param {string} desde - Fecha inicial (YYYY-MM-DD)
     * @param {string} hasta - Fecha final (YYYY-MM-DD)
     * @returns {Promise<Object>} Datos del ejercicio
     */
    fetchExerciseData: async function(ejercicio, desde, hasta) {
        try {
            // Construir URL con parámetros normalizados
            const params = { ejercicio };
            
            if (desde) {
                params.desde = desde;
            }
            
            if (hasta) {
                params.hasta = hasta;
            }
            
            console.log("Solicitando datos con parámetros:", params);
            
            // Realizar petición a la API
            return await API.get('/api/ejercicios_stats', params);
        } catch (error) {
            console.error('Error al obtener datos de ejercicios:', error);
            throw error;
        }
    },
    
    /**
     * Obtiene datos para el mapa de calor de actividad
     * 
     * @param {number} year - Año para el mapa de calor
     * @returns {Promise<Object>} Datos para el mapa de calor
     */
    fetchCalendarData: async function(year = new Date().getFullYear()) {
        try {
            console.log(`Solicitando datos de calendario para el año ${year}`);
            
            // Realizar petición a la API
            return await API.get('/api/calendar_heatmap', { year });
        } catch (error) {
            console.error('Error al obtener datos de calendario:', error);
            throw error;
        }
    },
    
    /**
     * Procesa datos de sesiones para obtener series temporales
     * 
     * @param {Array} data - Datos de sesiones
     * @param {string} valueKey - Clave del valor a extraer
     * @returns {Array} Datos procesados para gráficos
     */
    processTimeSeriesData: function(data, valueKey) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            return [];
        }
        
        return data
            .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item[valueKey] === 'number')
            .map(item => ({
                x: new Date(item.fecha),
                y: item[valueKey]
            }))
            .sort((a, b) => a.x - b.x); // Ordenar cronológicamente
    },
    
    /**
     * Procesa datos para el mapa de calor
     * 
     * @param {Array} data - Datos de calendario
     * @returns {Array} Datos procesados para el mapa de calor
     */
    processHeatmapData: function(data) {
        if (!data || !Array.isArray(data)) {
            return [];
        }
        
        // Asegurarse de que cada elemento tenga fecha y conteo
        return data
            .filter(d => d && typeof d === 'object' && d.date && typeof d.count === 'number')
            .map(d => ({
                date: d.date,
                count: d.count
            }));
    }
};

// Hacer disponible el módulo globalmente
window.DashboardData = DashboardData;