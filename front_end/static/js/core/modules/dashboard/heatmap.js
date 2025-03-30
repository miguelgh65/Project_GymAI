/**
 * Módulo de gráficos del Dashboard
 * Maneja la creación y actualización de gráficos
 */

const DashboardCharts = {
    // Referencias a instancias de gráficos
    weightChart: null,
    volumeChart: null,
    repsChart: null,
    
    /**
     * Crea gráficos de prueba para verificar Chart.js
     */
    createTestCharts: function() {
        console.log("Creando gráficos de prueba para verificar Chart.js");
        
        try {
            // Gráfico de peso
            this.createTestWeightChart();
            
            // Gráfico de volumen
            this.createTestVolumeChart();
            
            // Gráfico de repeticiones
            this.createTestRepsChart();
        } catch (error) {
            console.error("Error al crear gráficos de prueba:", error);
        }
    },
    
    /**
     * Crea un gráfico de peso de prueba
     */
    createTestWeightChart: function() {
        const chartElement = document.getElementById('weight-progression-chart');
        if (chartElement) {
            const ctxWeight = chartElement.getContext('2d');
            if (this.weightChart) {
                this.weightChart.destroy();
            }
            this.weightChart = new Chart(ctxWeight, {
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
    },
    
    /**
     * Crea un gráfico de volumen de prueba
     */
    createTestVolumeChart: function() {
        const volumeChartElement = document.getElementById('volume-chart');
        if (volumeChartElement) {
            const ctxVolume = volumeChartElement.getContext('2d');
            if (this.volumeChart) {
                this.volumeChart.destroy();
            }
            this.volumeChart = new Chart(ctxVolume, {
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
    },
    
    /**
     * Crea un gráfico de repeticiones de prueba
     */
    createTestRepsChart: function() {
        const repsChartElement = document.getElementById('reps-chart');
        if (repsChartElement) {
            const ctxReps = repsChartElement.getContext('2d');
            if (this.repsChart) {
                this.repsChart.destroy();
            }
            this.repsChart = new Chart(ctxReps, {
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
    },
    
    /**
     * Crea gráfico de progresión de peso
     * 
     * @param {Array} datos - Datos para el gráfico
     */
    createWeightProgressionChart: function(datos) {
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
                this.showNoDataMessage(chartElement);
                return;
            }
            
            // Preparar datos para el gráfico - convertir fechas a objetos Date
            const chartData = DashboardData.processTimeSeriesData(datos, 'max_peso');
            const avgData = DashboardData.processTimeSeriesData(datos, 'avg_peso');
            
            console.log("Datos procesados para gráfico:", { chartData, avgData });
            
            if (chartData.length === 0) {
                console.warn("No hay datos válidos para el gráfico de peso después del filtrado");
                this.showNoDataMessage(chartElement);
                return;
            }
            
            // Destruir gráfico anterior si existe
            if (this.weightChart) {
                this.weightChart.destroy();
            }
            
            const ctx = chartElement.getContext('2d');
            this.weightChart = new Chart(ctx, {
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
    },
    
    /**
     * Crea gráfico de volumen de entrenamiento
     * 
     * @param {Array} datos - Datos para el gráfico
     */
    createVolumeChart: function(datos) {
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
                this.showNoDataMessage(chartElement);
                return;
            }
            
            // Preparar datos para el gráfico
            const chartData = DashboardData.processTimeSeriesData(datos, 'volumen');
            
            console.log("Datos procesados para gráfico de volumen:", chartData);
            
            if (chartData.length === 0) {
                console.warn("No hay datos válidos para el gráfico de volumen después del filtrado");
                this.showNoDataMessage(chartElement);
                return;
            }
            
            // Destruir gráfico anterior si existe
            if (this.volumeChart) {
                this.volumeChart.destroy();
            }
            
            const ctx = chartElement.getContext('2d');
            this.volumeChart = new Chart(ctx, {
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
    },
    
    /**
     * Crea gráfico de repeticiones por serie
     * 
     * @param {Array} datos - Datos para el gráfico
     */
    createRepsChart: function(datos) {
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
                this.showNoDataMessage(chartElement);
                return;
            }
            
            // Preparar datos para el gráfico
            const chartData = DashboardData.processTimeSeriesData(datos, 'total_reps');
            
            console.log("Datos procesados para gráfico de repeticiones:", chartData);
            
            if (chartData.length === 0) {
                console.warn("No hay datos válidos para el gráfico de repeticiones después del filtrado");
                this.showNoDataMessage(chartElement);
                return;
            }
            
            // Destruir gráfico anterior si existe
            if (this.repsChart) {
                this.repsChart.destroy();
            }
            
            const ctx = chartElement.getContext('2d');
            this.repsChart = new Chart(ctx, {
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
    },
    
    /**
     * Limpia los gráficos
     */
    clearCharts: function() {
        try {
            console.log("Limpiando gráficos...");
            
            // Limpiar gráficos
            if (this.weightChart) {
                this.weightChart.destroy();
                this.weightChart = null;
            }
            
            if (this.volumeChart) {
                this.volumeChart.destroy();
                this.volumeChart = null;
            }
            
            if (this.repsChart) {
                this.repsChart.destroy();
                this.repsChart = null;
            }
            
            console.log("Gráficos limpiados exitosamente");
        } catch (error) {
            console.error("Error al limpiar gráficos:", error);
        }
    },
    
    /**
     * Muestra un mensaje de "sin datos" en el elemento del gráfico
     * 
     * @param {HTMLElement} element - Elemento donde mostrar el mensaje
     */
    showNoDataMessage: function(element) {
        if (!element) return;
        
        // Limpiar canvas
        const ctx = element.getContext('2d');
        ctx.clearRect(0, 0, element.width, element.height);
        
        // Mostrar mensaje
        ctx.fillStyle = '#757575';
        ctx.textAlign = 'center';
        ctx.font = '14px Arial';
        ctx.fillText('No hay datos disponibles', element.width / 2, element.height / 2);
    }
};

// Hacer disponible el módulo globalmente
window.DashboardCharts = DashboardCharts;