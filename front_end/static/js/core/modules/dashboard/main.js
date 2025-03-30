/**
 * Módulo principal del Dashboard
 * Inicializa y coordina la funcionalidad del dashboard
 */

const Dashboard = {
    // Estado compartido del dashboard
    state: {
        selectedExercise: null,
        dateFrom: null,
        dateTo: null,
        exerciseList: [],
        metricsData: {},
        sessionData: []
    },
    
    /**
     * Inicializa el dashboard
     */
    init: async function() {
        console.log("Inicializando dashboard...");
        
        // Verificar dependencias
        if (!this.checkDependencies()) {
            console.error("No se pudo iniciar el dashboard debido a dependencias faltantes");
            return;
        }
        
        try {
            // Configurar fechas predeterminadas
            this.setDefaultDateRange();
            
            // Cargar lista de ejercicios
            await this.loadExercises();
            
            // Configurar evento de filtros
            const applyFiltersBtn = document.getElementById('apply-filters');
            if (applyFiltersBtn) {
                applyFiltersBtn.addEventListener('click', this.applyFilters.bind(this));
            }
            
            // Cargar mapa de calor del calendario de actividad
            if (typeof d3 !== 'undefined') {
                DashboardHeatmap.loadActivityHeatmap();
            } else {
                console.warn("D3.js no está disponible, el mapa de calor no se cargará");
            }
            
            // Si no hay ejercicio seleccionado, mostrar un gráfico de prueba
            const ejercicioSelect = document.getElementById('ejercicio-select');
            if (ejercicioSelect && !ejercicioSelect.value) {
                DashboardCharts.createTestCharts();
            }
            
            console.log("Dashboard inicializado con éxito");
        } catch (error) {
            console.error("Error al inicializar el dashboard:", error);
            alert("Hubo un error al inicializar el dashboard. Consulta la consola para más detalles.");
        }
    },
    
    /**
     * Verificar que las dependencias necesarias están cargadas
     */
    checkDependencies: function() {
        if (typeof Chart === 'undefined') {
            console.error("ERROR: Chart.js no está cargado. Asegúrate de incluir la biblioteca Chart.js antes de dashboard.js");
            
            // Añadir mensaje de error visible para el usuario
            document.body.innerHTML = `
                <div style="color: red; padding: 20px; text-align: center; margin-top: 50px; font-family: Arial, sans-serif;">
                    <h2>Error: Chart.js no está cargado</h2>
                    <p>Por favor, asegúrate de incluir la biblioteca Chart.js en tu HTML:</p>
                    <pre style="background: #f8f8f8; padding: 10px; border-radius: 5px; text-align: left; display: inline-block;">
    &lt;script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"&gt;&lt;/script&gt;
                    </pre>
                </div>
            ` + document.body.innerHTML;
            return false;
        }
        
        if (typeof d3 === 'undefined' && document.getElementById('activity-heatmap')) {
            console.error("ERROR: D3.js no está cargado y es necesario para el mapa de calor. Asegúrate de incluir la biblioteca D3.js antes de dashboard.js");
            
            // Añadir mensaje de error solo en el contenedor del mapa de calor
            const heatmapContainer = document.getElementById('activity-heatmap');
            if (heatmapContainer) {
                heatmapContainer.innerHTML = `
                    <div style="color: red; padding: 10px; text-align: center; font-family: Arial, sans-serif;">
                        <h3>Error: D3.js no está cargado</h3>
                        <p>El mapa de calor requiere D3.js. Añade la siguiente línea a tu HTML:</p>
                        <pre style="background: #f8f8f8; padding: 5px; border-radius: 5px; text-align: left; font-size: 12px; display: inline-block;">
    &lt;script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"&gt;&lt;/script&gt;
                        </pre>
                    </div>
                `;
            }
            // Continuamos para el resto de funcionalidades
        }
        
        return this.checkRequiredElements();
    },
    
    /**
     * Verificar que los elementos necesarios existen en el DOM
     */
    checkRequiredElements: function() {
        const requiredElements = [
            { id: 'weight-progression-chart', name: 'Gráfico de Progresión de Peso' },
            { id: 'volume-chart', name: 'Gráfico de Volumen' },
            { id: 'reps-chart', name: 'Gráfico de Repeticiones' },
            { id: 'ejercicio-select', name: 'Selector de Ejercicios' },
            { id: 'date-from', name: 'Fecha Desde' },
            { id: 'date-to', name: 'Fecha Hasta' },
            { id: 'apply-filters', name: 'Botón de Aplicar Filtros' },
            { id: 'activity-heatmap', name: 'Mapa de Calor de Actividad' }
        ];
        
        const missingElements = [];
        
        requiredElements.forEach(element => {
            if (!document.getElementById(element.id)) {
                missingElements.push(element.name);
                console.error(`ERROR: No se encontró el elemento con ID '${element.id}' (${element.name})`);
            }
        });
        
        if (missingElements.length > 0) {
            console.error(`Faltan ${missingElements.length} elementos necesarios:`, missingElements);
            alert(`Error: Faltan elementos HTML necesarios: ${missingElements.join(', ')}`);
            return false;
        }
        
        return true;
    },
    
    /**
     * Establecer fechas predeterminadas (último mes)
     */
    setDefaultDateRange: function() {
        try {
            const today = new Date();
            const monthAgo = new Date();
            monthAgo.setMonth(monthAgo.getMonth() - 1);
            
            const dateFrom = document.getElementById('date-from');
            const dateTo = document.getElementById('date-to');
            
            if (!dateFrom || !dateTo) {
                console.error("No se encontraron los elementos de fecha");
                return;
            }
            
            dateFrom.valueAsDate = monthAgo;
            dateTo.valueAsDate = today;
            
            // Actualizar estado
            this.state.dateFrom = dateFrom.value;
            this.state.dateTo = dateTo.value;
            
            console.log("Rango de fechas establecido:", {
                desde: dateFrom.value,
                hasta: dateTo.value
            });
        } catch (error) {
            console.error("Error al establecer fechas predeterminadas:", error);
        }
    },
    
    /**
     * Cargar lista de ejercicios al selector
     */
    loadExercises: async function() {
        try {
            console.log("Solicitando lista de ejercicios...");
            
            const data = await API.get('/api/ejercicios_stats');
            console.log("Datos de ejercicios recibidos:", data);
            
            const selectElement = document.getElementById('ejercicio-select');
            if (!selectElement) {
                console.error("No se encontró el elemento selector de ejercicios");
                return;
            }
            
            // Guardar el valor seleccionado actualmente para restaurarlo después
            const currentSelection = selectElement.value;
            
            if (data.success && Array.isArray(data.ejercicios)) {
                selectElement.innerHTML = '<option value="">Selecciona un ejercicio</option>';
                
                // Actualizar estado
                this.state.exerciseList = data.ejercicios;
                
                data.ejercicios.forEach(ejercicio => {
                    const option = document.createElement('option');
                    option.value = ejercicio;
                    option.textContent = ejercicio;
                    selectElement.appendChild(option);
                });
                
                // Restaurar la selección previa si existía y sigue siendo válida
                if (currentSelection) {
                    const exists = Array.from(selectElement.options).some(option => option.value === currentSelection);
                    if (exists) {
                        selectElement.value = currentSelection;
                        this.state.selectedExercise = currentSelection;
                    }
                }
                
                // Añadir evento de cambio al selector si no se ha añadido antes
                const hasChangeEvent = selectElement.getAttribute('data-has-change-event');
                if (!hasChangeEvent) {
                    selectElement.addEventListener('change', () => {
                        this.state.selectedExercise = selectElement.value;
                        if (selectElement.value) {
                            this.applyFilters();
                        } else {
                            DashboardCharts.clearCharts();
                        }
                    });
                    selectElement.setAttribute('data-has-change-event', 'true');
                }
                
                console.log(`${data.ejercicios.length} ejercicios cargados con éxito`);
            } else {
                console.warn("La respuesta no contiene una lista de ejercicios válida");
                selectElement.innerHTML = '<option value="">No hay ejercicios disponibles</option>';
            }
        } catch (error) {
            console.error('Error al cargar ejercicios:', error);
            
            // Mostrar mensaje de error en el selector
            const selectElement = document.getElementById('ejercicio-select');
            if (selectElement) {
                selectElement.innerHTML = '<option value="">Error al cargar ejercicios</option>';
            }
        }
    },
    
    /**
     * Validar el rango de fechas
     */
    validateDateRange: function() {
        const dateFrom = document.getElementById('date-from');
        const dateTo = document.getElementById('date-to');
        
        if (dateFrom && dateTo && dateFrom.value && dateTo.value) {
            const fromDate = new Date(dateFrom.value);
            const toDate = new Date(dateTo.value);
            
            if (fromDate > toDate) {
                alert("La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'");
                dateTo.value = dateFrom.value;
                this.state.dateTo = dateFrom.value;
                return false;
            }
            
            // Actualizar estado
            this.state.dateFrom = dateFrom.value;
            this.state.dateTo = dateTo.value;
        }
        
        return true;
    },
    
    /**
     * Aplicar filtros y cargar datos
     */
    applyFilters: async function() {
        try {
            // Validar el rango de fechas
            if (!this.validateDateRange()) {
                return;
            }
            
            const ejercicioSelect = document.getElementById('ejercicio-select');
            if (!ejercicioSelect) {
                console.error("No se encontró el elemento selector de ejercicios");
                return;
            }
            
            const ejercicio = ejercicioSelect.value;
            if (!ejercicio) {
                console.warn("No hay ejercicio seleccionado");
                return;
            }
            
            // Actualizar estado
            this.state.selectedExercise = ejercicio;
            
            console.log("Aplicando filtros:", {
                ejercicio,
                desde: this.state.dateFrom,
                hasta: this.state.dateTo
            });
            
            // Solicitar datos
            const data = await DashboardData.fetchExerciseData(
                ejercicio, 
                this.state.dateFrom, 
                this.state.dateTo
            );
            
            // Procesar respuesta
            if (data.success) {
                // Actualizar estado
                if (data.resumen) {
                    this.state.metricsData = data.resumen;
                    DashboardUI.updateMetricCards(data.resumen);
                } else {
                    console.warn("No se recibieron datos de resumen");
                }
                
                this.state.sessionData = data.datos || [];
                DashboardUI.updateSessionsTable(this.state.sessionData);
                
                if (Array.isArray(this.state.sessionData) && this.state.sessionData.length > 0) {
                    DashboardCharts.createWeightProgressionChart(this.state.sessionData);
                    DashboardCharts.createVolumeChart(this.state.sessionData);
                    DashboardCharts.createRepsChart(this.state.sessionData);
                } else {
                    console.warn("No se recibieron datos para los gráficos");
                    DashboardCharts.clearCharts();
                }
            } else {
                console.error("Error en respuesta:", data.message || "Respuesta no exitosa");
                alert(`Error: ${data.message || "No se pudieron cargar los datos"}`);
            }
        } catch (error) {
            console.error('Error al aplicar filtros:', error);
            alert("Error al cargar datos. Consulta la consola para más detalles.");
        }
    }
};

// Iniciar el dashboard cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    Dashboard.init();
});