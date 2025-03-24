// Variables globales para los gráficos
let weightChart = null;
let volumeChart = null;
let repsChart = null;
let calendarHeatmap = null;

// Verificar dependencias antes de inicializar
function checkDependencies() {
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
    
    return true;
}

// Verificar que los elementos necesarios existen en el DOM
function checkRequiredElements() {
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
}

// Inicializar dashboard al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    console.log("Documento listo, iniciando verificación de dependencias...");
    
    if (!checkDependencies()) {
        console.error("No se pudo iniciar el dashboard debido a dependencias faltantes");
        return;
    }
    
    if (!checkRequiredElements()) {
        console.error("No se pudo iniciar el dashboard debido a elementos faltantes");
        return;
    }
    
    console.log("Verificación completada, iniciando dashboard...");
    initDashboard();
});

// Función para inicializar el dashboard
async function initDashboard() {
    console.log("Inicializando dashboard...");
    
    try {
        // Cargar lista de ejercicios
        await loadExercises();
        
        // Configurar filtros iniciales
        setDefaultDateRange();
        
        // Configurar evento de filtros
        const applyFiltersBtn = document.getElementById('apply-filters');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', applyFilters);
        }
        
        // Cargar mapa de calor del calendario de actividad
        if (typeof d3 !== 'undefined') {
            loadActivityHeatmap();
        } else {
            console.warn("D3.js no está disponible, el mapa de calor no se cargará");
        }
        
        // Si no hay ejercicio seleccionado, mostrar un gráfico de prueba
        const ejercicioSelect = document.getElementById('ejercicio-select');
        if (ejercicioSelect && !ejercicioSelect.value) {
            createTestChart();
        }
        
        console.log("Dashboard inicializado con éxito");
    } catch (error) {
        console.error("Error al inicializar el dashboard:", error);
        alert("Hubo un error al inicializar el dashboard. Consulta la consola para más detalles.");
    }
}

// Función de prueba para verificar que Chart.js funciona correctamente
function createTestChart() {
    console.log("Creando gráfico de prueba para verificar Chart.js");
    
    try {
        // Gráfico de peso
        const weightChartElement = document.getElementById('weight-progression-chart');
        if (weightChartElement) {
            const ctxWeight = weightChartElement.getContext('2d');
            if (weightChart) {
                weightChart.destroy();
            }
            weightChart = new Chart(ctxWeight, {
                type: 'line',
                data: {
                    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May'],
                    datasets: [{
                        label: 'Peso de prueba',
                        data: [65, 70, 75, 80, 85],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            console.log("Gráfico de peso de prueba creado con éxito");
        } else {
            console.error("No se pudo crear el gráfico de peso: elemento no encontrado");
        }
        
        // Gráfico de volumen
        const volumeChartElement = document.getElementById('volume-chart');
        if (volumeChartElement) {
            const ctxVolume = volumeChartElement.getContext('2d');
            if (volumeChart) {
                volumeChart.destroy();
            }
            volumeChart = new Chart(ctxVolume, {
                type: 'bar',
                data: {
                    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May'],
                    datasets: [{
                        label: 'Volumen de prueba',
                        data: [500, 600, 550, 700, 750],
                        backgroundColor: 'rgba(46, 204, 113, 0.7)',
                        borderColor: 'rgba(46, 204, 113, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            console.log("Gráfico de volumen de prueba creado con éxito");
        } else {
            console.error("No se pudo crear el gráfico de volumen: elemento no encontrado");
        }
        
        // Gráfico de repeticiones
        const repsChartElement = document.getElementById('reps-chart');
        if (repsChartElement) {
            const ctxReps = repsChartElement.getContext('2d');
            if (repsChart) {
                repsChart.destroy();
            }
            repsChart = new Chart(ctxReps, {
                type: 'line',
                data: {
                    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May'],
                    datasets: [{
                        label: 'Repeticiones de prueba',
                        data: [15, 18, 20, 22, 25],
                        borderColor: '#e67e22',
                        backgroundColor: 'rgba(230, 126, 34, 0.1)',
                        borderWidth: 2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            console.log("Gráfico de repeticiones de prueba creado con éxito");
        } else {
            console.error("No se pudo crear el gráfico de repeticiones: elemento no encontrado");
        }
    } catch (error) {
        console.error("Error al crear gráficos de prueba:", error);
    }
}

// Cargar lista de ejercicios al selector
async function loadExercises() {
    try {
        console.log("Solicitando lista de ejercicios...");
        const response = await fetch('/api/ejercicios_stats');
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("Datos de ejercicios recibidos:", data);
        
        const selectElement = document.getElementById('ejercicio-select');
        if (!selectElement) {
            console.error("No se encontró el elemento selector de ejercicios");
            return;
        }
        
        if (data.success && Array.isArray(data.ejercicios)) {
            selectElement.innerHTML = '<option value="">Selecciona un ejercicio</option>';
            
            data.ejercicios.forEach(ejercicio => {
                const option = document.createElement('option');
                option.value = ejercicio;
                option.textContent = ejercicio;
                selectElement.appendChild(option);
            });
            
            // Añadir evento de cambio al selector
            selectElement.addEventListener('change', function() {
                if (this.value) {
                    applyFilters();
                } else {
                    clearCharts();
                }
            });
            
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
}

// Establecer fechas predeterminadas (último mes)
function setDefaultDateRange() {
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
        
        console.log("Rango de fechas establecido:", {
            desde: dateFrom.value,
            hasta: dateTo.value
        });
    } catch (error) {
        console.error("Error al establecer fechas predeterminadas:", error);
    }
}

// Aplicar filtros y cargar datos
async function applyFilters() {
    try {
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
        
        const dateFrom = document.getElementById('date-from');
        const dateTo = document.getElementById('date-to');
        
        if (!dateFrom || !dateTo) {
            console.error("No se encontraron los elementos de fecha");
            return;
        }
        
        console.log("Aplicando filtros:", {
            ejercicio,
            desde: dateFrom.value,
            hasta: dateTo.value
        });
        
        let url = `/api/ejercicios_stats?ejercicio=${encodeURIComponent(ejercicio)}`;
        if (dateFrom.value) url += `&desde=${dateFrom.value}`;
        if (dateTo.value) url += `&hasta=${dateTo.value}`;
        
        console.log("Solicitando datos con URL:", url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("Datos recibidos:", data);
        
        if (data.success) {
            if (data.resumen) {
                updateMetricCards(data.resumen);
            } else {
                console.warn("No se recibieron datos de resumen");
            }
            
            updateSessionsTable(data.datos || []);
            
            if (Array.isArray(data.datos) && data.datos.length > 0) {
                createWeightProgressionChart(data.datos);
                createVolumeChart(data.datos);
                createRepsChart(data.datos);
            } else {
                console.warn("No se recibieron datos para los gráficos");
                clearCharts();
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

// Actualizar tarjetas de métricas
function updateMetricCards(resumen) {
    try {
        console.log("Actualizando tarjetas de métricas con:", resumen);
        
        const sessionElement = document.querySelector('#card-sessions .metric-value');
        const maxWeightElement = document.querySelector('#card-max-weight .metric-value');
        const progressElement = document.querySelector('#card-progress .metric-value');
        const volumeElement = document.querySelector('#card-volume .metric-value');
        
        if (sessionElement) {
            sessionElement.textContent = resumen.total_sesiones || 0;
        }
        
        if (maxWeightElement) {
            maxWeightElement.textContent = `${resumen.max_weight_ever || 0} kg`;
        }
        
        if (progressElement) {
            const progress = resumen.progress_percent || 0;
            progressElement.textContent = `${progress}%`;
            progressElement.className = 'metric-value';
            
            // Añadir clase según si el progreso es positivo o negativo
            if (progress > 0) {
                progressElement.classList.add('positive');
            } else if (progress < 0) {
                progressElement.classList.add('negative');
            }
        }
        
        if (volumeElement) {
            volumeElement.textContent = `${resumen.max_volume_session || 0} kg`;
        }
    } catch (error) {
        console.error("Error al actualizar tarjetas de métricas:", error);
    }
}

// Actualizar tabla de sesiones
function updateSessionsTable(datos) {
    try {
        console.log("Actualizando tabla de sesiones con:", datos);
        
        const tableBody = document.querySelector('#sessions-table tbody');
        if (!tableBody) {
            console.error("No se encontró el elemento de la tabla de sesiones");
            return;
        }
        
        tableBody.innerHTML = '';
        
        if (!datos || !Array.isArray(datos) || datos.length === 0) {
            const row = document.createElement('tr');
            row.className = 'empty-state';
            row.innerHTML = '<td colspan="5">No hay datos para el ejercicio y periodo seleccionados</td>';
            tableBody.appendChild(row);
            return;
        }
        
        // Ordenar datos por fecha descendente para mostrar los más recientes primero
        const sortedData = [...datos].sort((a, b) => {
            const dateA = new Date(a.fecha || 0);
            const dateB = new Date(b.fecha || 0);
            return dateB - dateA;
        });
        
        // Limitar a las 10 sesiones más recientes
        const recentSessions = sortedData.slice(0, 10);
        
        recentSessions.forEach(session => {
            const row = document.createElement('tr');
            
            // Formatear fecha
            let fechaFormateada = 'Sin fecha';
            try {
                if (session.fecha) {
                    const fecha = new Date(session.fecha);
                    if (!isNaN(fecha.getTime())) {
                        fechaFormateada = fecha.toLocaleDateString('es-ES');
                    }
                }
            } catch (e) {
                console.error("Error al formatear fecha:", e);
            }
            
            // Formatear series
            let seriesText = '';
            if (session.series && Array.isArray(session.series)) {
                session.series.forEach(serie => {
                    if (serie && typeof serie === 'object') {
                        const reps = serie.repeticiones || 0;
                        const peso = serie.peso || 0;
                        seriesText += `${reps}x${peso}kg `;
                    }
                });
            }
            
            row.innerHTML = `
                <td>${fechaFormateada}</td>
                <td>${seriesText.trim() || 'N/A'}</td>
                <td>${session.max_peso || 0} kg</td>
                <td>${session.total_reps || 0}</td>
                <td>${session.volumen || 0} kg</td>
            `;
            
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error("Error al actualizar tabla de sesiones:", error);
    }
}

// Crear gráfico de progresión de peso
function createWeightProgressionChart(datos) {
    try {
        console.log("Creando gráfico de progresión de peso con:", datos);
        
        // Verificar que el elemento existe
        const chartElement = document.getElementById('weight-progression-chart');
        if (!chartElement) {
            console.error("No se encontró el elemento para el gráfico de peso");
            return;
        }
        
        // Verificar que Chart está definido
        if (typeof Chart === 'undefined') {
            console.error("Chart.js no está disponible");
            return;
        }
        
        // Verificar que haya datos
        if (!datos || !Array.isArray(datos) || datos.length === 0) {
            console.warn("No hay datos para crear el gráfico de peso");
            
            // Limpiar gráfico anterior si existe
            if (weightChart) {
                weightChart.destroy();
                weightChart = null;
            }
            
            // Mostrar mensaje de "sin datos"
            const ctx = chartElement.getContext('2d');
            ctx.clearRect(0, 0, chartElement.width, chartElement.height);
            ctx.fillStyle = '#757575';
            ctx.textAlign = 'center';
            ctx.font = '14px Arial';
            ctx.fillText('No hay datos disponibles', chartElement.width / 2, chartElement.height / 2);
            
            return;
        }
        
        // Destruir gráfico anterior si existe
        if (weightChart) {
            weightChart.destroy();
        }
        
        // Preparar datos para el gráfico - convertir fechas a objetos Date
        const chartData = datos
            .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item.max_peso === 'number')
            .map(item => ({
                x: new Date(item.fecha),
                y: item.max_peso
            }));
        
        const avgData = datos
            .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item.avg_peso === 'number')
            .map(item => ({
                x: new Date(item.fecha),
                y: item.avg_peso
            }));
        
        console.log("Datos procesados para gráfico:", { chartData, avgData });
        
        if (chartData.length === 0) {
            console.warn("No hay datos válidos para el gráfico de peso después del filtrado");
            return;
        }
        
        const ctx = chartElement.getContext('2d');
        weightChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Peso Máximo',
                        data: chartData,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.2
                    },
                    {
                        label: 'Peso Promedio',
                        data: avgData,
                        borderColor: '#9b59b6',
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y + ' kg';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'dd/MM/yy'
                            },
                            tooltipFormat: 'dd/MM/yyyy'
                        },
                        title: {
                            display: true,
                            text: 'Fecha'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Peso (kg)'
                        }
                    }
                }
            }
        });
        
        console.log("Gráfico de peso creado exitosamente");
    } catch (error) {
        console.error("Error al crear el gráfico de peso:", error);
    }
}

// Crear gráfico de volumen de entrenamiento
function createVolumeChart(datos) {
    try {
        console.log("Creando gráfico de volumen con:", datos);
        
        // Verificar que el elemento existe
        const chartElement = document.getElementById('volume-chart');
        if (!chartElement) {
            console.error("No se encontró el elemento para el gráfico de volumen");
            return;
        }
        
        // Verificar que Chart está definido
        if (typeof Chart === 'undefined') {
            console.error("Chart.js no está disponible");
            return;
        }
        
        // Verificar que haya datos
        if (!datos || !Array.isArray(datos) || datos.length === 0) {
            console.warn("No hay datos para crear el gráfico de volumen");
            
            // Limpiar gráfico anterior si existe
            if (volumeChart) {
                volumeChart.destroy();
                volumeChart = null;
            }
            
            // Mostrar mensaje de "sin datos"
            const ctx = chartElement.getContext('2d');
            ctx.clearRect(0, 0, chartElement.width, chartElement.height);
            ctx.fillStyle = '#757575';
            ctx.textAlign = 'center';
            ctx.font = '14px Arial';
            ctx.fillText('No hay datos disponibles', chartElement.width / 2, chartElement.height / 2);
            
            return;
        }
        
        // Destruir gráfico anterior si existe
        if (volumeChart) {
            volumeChart.destroy();
        }
        
        // Preparar datos para el gráfico - convertir fechas a objetos Date
        const chartData = datos
            .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item.volumen === 'number')
            .map(item => ({
                x: new Date(item.fecha),
                y: item.volumen
            }));
        
        console.log("Datos procesados para gráfico de volumen:", chartData);
        
        if (chartData.length === 0) {
            console.warn("No hay datos válidos para el gráfico de volumen después del filtrado");
            return;
        }
        
        const ctx = chartElement.getContext('2d');
        volumeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                datasets: [
                    {
                        label: 'Volumen Total',
                        data: chartData,
                        backgroundColor: 'rgba(46, 204, 113, 0.7)',
                        borderColor: 'rgba(46, 204, 113, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Volumen: ' + context.parsed.y + ' kg';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'dd/MM/yy'
                            },
                            tooltipFormat: 'dd/MM/yyyy'
                        },
                        title: {
                            display: true,
                            text: 'Fecha'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Volumen (kg)'
                        }
                    }
                }
            }
        });
        
        console.log("Gráfico de volumen creado exitosamente");
    } catch (error) {
        console.error("Error al crear el gráfico de volumen:", error);
    }
}

// Crear gráfico de repeticiones por serie
function createRepsChart(datos) {
    try {
        console.log("Creando gráfico de repeticiones con:", datos);
        
        // Verificar que el elemento existe
        const chartElement = document.getElementById('reps-chart');
        if (!chartElement) {
            console.error("No se encontró el elemento para el gráfico de repeticiones");
            return;
        }
        
        // Verificar que Chart está definido
        if (typeof Chart === 'undefined') {
            console.error("Chart.js no está disponible");
            return;
        }
        
        // Verificar que haya datos
        if (!datos || !Array.isArray(datos) || datos.length === 0) {
            console.warn("No hay datos para crear el gráfico de repeticiones");
            
            // Limpiar gráfico anterior si existe
            if (repsChart) {
                repsChart.destroy();
                repsChart = null;
            }
            
            // Mostrar mensaje de "sin datos"
            const ctx = chartElement.getContext('2d');
            ctx.clearRect(0, 0, chartElement.width, chartElement.height);
            ctx.fillStyle = '#757575';
            ctx.textAlign = 'center';
            ctx.font = '14px Arial';
            ctx.fillText('No hay datos disponibles', chartElement.width / 2, chartElement.height / 2);
            
            return;
        }
        
        // Destruir gráfico anterior si existe
        if (repsChart) {
            repsChart.destroy();
        }
        
        // Preparar datos para el gráfico - convertir fechas a objetos Date
        const chartData = datos
            .filter(item => item && item.fecha && !isNaN(new Date(item.fecha).getTime()) && typeof item.total_reps === 'number')
            .map(item => ({
                x: new Date(item.fecha),
                y: item.total_reps
            }));
        
        console.log("Datos procesados para gráfico de repeticiones:", chartData);
        
        if (chartData.length === 0) {
            console.warn("No hay datos válidos para el gráfico de repeticiones después del filtrado");
            return;
        }
        
        const ctx = chartElement.getContext('2d');
        repsChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Repeticiones Totales',
                        data: chartData,
                        borderColor: '#e67e22',
                        backgroundColor: 'rgba(230, 126, 34, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'dd/MM/yy'
                            },
                            tooltipFormat: 'dd/MM/yyyy'
                        },
                        title: {
                            display: true,
                            text: 'Fecha'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Repeticiones'
                        }
                    }
                }
            }
        });
        
        console.log("Gráfico de repeticiones creado exitosamente");
    } catch (error) {
        console.error("Error al crear el gráfico de repeticiones:", error);
    }
}

// Cargar y crear mapa de calor de actividad
async function loadActivityHeatmap() {
    try {
        // Verificar que D3.js está cargado
        if (typeof d3 === 'undefined') {
            console.error("D3.js no está disponible para el mapa de calor");
            return;
        }
        
        const container = document.getElementById('activity-heatmap');
        if (!container) {
            console.error("No se encontró el contenedor del mapa de calor");
            return;
        }
        
        const year = new Date().getFullYear();
        console.log("Solicitando datos para el mapa de calor del año:", year);
        
        const response = await fetch(`/api/calendar_heatmap?year=${year}`);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("Datos recibidos para el mapa de calor:", data);
        
        if (data.success && Array.isArray(data.data) && data.data.length > 0) {
            createCalendarHeatmap(data.data);
        } else {
            console.warn("No hay datos para el mapa de calor de actividad");
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: #757575;">No hay datos de actividad para mostrar</div>';
        }
    } catch (error) {
        console.error('Error al cargar datos de actividad:', error);
        
        const container = document.getElementById('activity-heatmap');
        if (container) {
            container.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #757575;">
                    Error al cargar datos de actividad: ${error.message || 'Error desconocido'}
                </div>
            `;
        }
    }
}

// Crear mapa de calor del calendario con D3.js
function createCalendarHeatmap(data) {
    try {
        console.log("Creando mapa de calor con:", data);
        
        // Verificar que D3.js está cargado
        if (typeof d3 === 'undefined') {
            console.error("D3.js no está disponible para crear el mapa de calor");
            return;
        }
        
        const container = document.getElementById('activity-heatmap');
        if (!container) {
            console.error("No se encontró el contenedor del mapa de calor");
            return;
        }
        
        container.innerHTML = '';
        
        // Verificar que haya datos
        if (!data || !Array.isArray(data) || data.length === 0) {
            console.warn("No hay datos para crear el mapa de calor");
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: #757575;">No hay datos de actividad para mostrar</div>';
            return;
        }
        
        // Verificar formato de datos
        if (!data.every(d => d && typeof d === 'object' && d.date && (typeof d.count === 'number'))) {
            console.error("Formato de datos inválido para el mapa de calor");
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: #757575;">Formato de datos inválido</div>';
            return;
        }
        
        // Configurar dimensiones
        const width = container.clientWidth || 800;
        const height = 150;
        const cellSize = 15;
        const cellMargin = 2;
        
        console.log("Dimensiones del contenedor:", width, height);
        
        // Crear escala de color
        const maxCount = Math.max(...data.map(d => d.count), 1);
        const colorScale = d3.scaleSequential()
            .domain([0, maxCount])
            .interpolator(d3.interpolateBlues);
        
        // Crear el SVG
        const svg = d3.select('#activity-heatmap')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Configurar fecha y formato
        const today = new Date();
        const year = today.getFullYear();
        const parseDate = d3.timeParse('%Y-%m-%d');
        
        // Procesar datos
        const countByDate = {};
        data.forEach(d => {
            countByDate[d.date] = d.count;
        });
        
        // Crear el calendario
        const yearDates = d3.timeDays(
            new Date(year, 0, 1),
            new Date(year + 1, 0, 1)
        );
        
        // Calcular la posición de los días
        const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        
        // Añadir nombres de los meses
        svg.selectAll('.month-label')
            .data(d3.range(12))
            .join('text')
            .attr('class', 'month-label')
            .attr('x', d => (d * cellSize * 31) / 12 + 20)
            .attr('y', 20)
            .style('font-size', '10px')
            .style('fill', '#666')
            .text(d => monthNames[d]);
        
        // Crear los cuadrados para cada día
        svg.selectAll('.day')
            .data(yearDates)
            .join('rect')
            .attr('class', 'day')
            .attr('width', cellSize - cellMargin)
            .attr('height', cellSize - cellMargin)
            .attr('x', d => {
                // Ajustar la posición x basada en el día del año
                const dayOfYear = d3.timeDay.count(d3.timeYear(d), d);
                return dayOfYear * (cellSize / 3) + 10;
            })
            .attr('y', d => {
                // Ajustar la posición y basada en el día de la semana
                return d.getDay() * cellSize + 30;
            })
            .attr('fill', d => {
                const dateStr = d3.timeFormat('%Y-%m-%d')(d);
                return countByDate[dateStr] ? colorScale(countByDate[dateStr]) : '#eee';
            })
            .append('title')
            .text(d => {
                const dateStr = d3.timeFormat('%Y-%m-%d')(d);
                const formattedDate = d3.timeFormat('%d/%m/%Y')(d);
                return `${formattedDate}: ${countByDate[dateStr] || 0} ejercicios`;
            });
        
        // Leyenda para el mapa de calor
        const legendWidth = 150;
        const legendHeight = 20;
        
        const legendScale = d3.scaleLinear()
            .domain([0, maxCount])
            .range([0, legendWidth]);
            
        const legend = svg.append('g')
            .attr('transform', `translate(${width - legendWidth - 20}, ${height - 30})`);
            
        legend.append('text')
            .attr('x', 0)
            .attr('y', -5)
            .style('font-size', '10px')
            .style('fill', '#666')
            .text('Intensidad de Entrenamiento:');
            
        const defs = svg.append('defs');
        const gradient = defs.append('linearGradient')
            .attr('id', 'gradient')
            .attr('x1', '0%')
            .attr('x2', '100%')
            .attr('y1', '0%')
            .attr('y2', '0%');
            
        gradient.selectAll('stop')
            .data([0, 0.2, 0.4, 0.6, 0.8, 1])
            .join('stop')
            .attr('offset', d => (d * 100) + '%')
            .attr('stop-color', d => colorScale(d * maxCount));
            
        legend.append('rect')
            .attr('width', legendWidth)
            .attr('height', legendHeight)
            .style('fill', 'url(#gradient)');
            
        const legendAxis = d3.axisBottom(legendScale)
            .ticks(5)
            .tickSize(legendHeight);
            
        legend.append('g')
            .call(legendAxis)
            .select('.domain')
            .remove();
            
        console.log("Mapa de calor creado exitosamente");
    } catch (error) {
        console.error("Error al crear el mapa de calor:", error);
        
        const container = document.getElementById('activity-heatmap');
        if (container) {
            container.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #757575;">
                    Error al crear el mapa de calor: ${error.message || 'Error desconocido'}
                </div>
            `;
        }
    }
}

// Función para limpiar los gráficos
function clearCharts() {
    try {
        console.log("Limpiando gráficos...");
        
        // Limpiar gráficos
        if (weightChart) {
            weightChart.destroy();
            weightChart = null;
        }
        
        if (volumeChart) {
            volumeChart.destroy();
            volumeChart = null;
        }
        
        if (repsChart) {
            repsChart.destroy();
            repsChart = null;
        }
        
        // Limpiar tarjetas de métricas
        const sessionElement = document.querySelector('#card-sessions .metric-value');
        const maxWeightElement = document.querySelector('#card-max-weight .metric-value');
        const progressElement = document.querySelector('#card-progress .metric-value');
        const volumeElement = document.querySelector('#card-volume .metric-value');
        
        if (sessionElement) sessionElement.textContent = '0';
        if (maxWeightElement) maxWeightElement.textContent = '0 kg';
        if (progressElement) {
            progressElement.textContent = '0%';
            progressElement.className = 'metric-value';
        }
        if (volumeElement) volumeElement.textContent = '0 kg';
        
        // Limpiar tabla
        const tableBody = document.querySelector('#sessions-table tbody');
        if (tableBody) {
            tableBody.innerHTML = '<tr class="empty-state"><td colspan="5">Selecciona un ejercicio para ver sus datos</td></tr>';
        }
        
        console.log("Gráficos limpiados exitosamente");
    } catch (error) {
        console.error("Error al limpiar gráficos:", error);
    }
}