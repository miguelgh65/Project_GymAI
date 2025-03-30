/**
 * Módulo de rutina del día
 * Maneja la visualización y registro de la rutina diaria
 */

const TodayRoutine = {
    // Estado compartido
    state: {
        routineData: null,
        dayName: '',
        isLoading: false
    },
    
    /**
     * Inicializa la gestión de rutina diaria
     */
    init: function() {
        // Verificar si estamos en la página de rutina de hoy
        const todayContent = document.getElementById('today-content');
        if (todayContent) {
            this.loadTodaysWorkout();
        }
    },
    
    /**
     * Carga la rutina del día de hoy
     */
    loadTodaysWorkout: async function() {
        const todayContent = document.getElementById('today-content');
        if (!todayContent) return;
        
        // Mostrar estado de carga
        this.state.isLoading = true;
        todayContent.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Cargando tu rutina de hoy...</p>
            </div>
        `;
        
        try {
            // Solicitar datos de rutina de hoy
            const response = await fetch('/rutina_hoy?format=json');
            const data = await response.json();
            
            // Actualizar estado
            this.state.routineData = data;
            this.state.dayName = data.dia_nombre || '';
            
            if (data.success && data.rutina && data.rutina.length > 0) {
                // Renderizar la rutina
                this.renderTodayRoutine(todayContent, data);
            } else {
                // Mostrar mensaje de no hay rutina
                todayContent.innerHTML = `
                    <div class="no-routine">
                        <i class="fas fa-calendar-times"></i>
                        <p>${data.message || 'No hay rutina definida para hoy.'}</p>
                        <p class="no-routine-tip">Configura tu rutina en la pestaña "Mi Rutina".</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error:', error);
            
            todayContent.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error al cargar la rutina de hoy.</p>
                </div>
            `;
        } finally {
            this.state.isLoading = false;
        }
    },
    
    /**
     * Renderiza la rutina del día
     * 
     * @param {HTMLElement} container - Contenedor donde renderizar
     * @param {Object} data - Datos de la rutina
     */
    renderTodayRoutine: function(container, data) {
        let html = `
            <div class="today-header">
                <h3>${data.dia_nombre}</h3>
                <p>Estos son los ejercicios que te tocan hoy:</p>
            </div>
            <form id="todayExerciseForm">
                <ul class="today-exercises">
        `;
        
        // Generar ítems de ejercicios
        data.rutina.forEach((item, index) => {
            const statusClass = item.realizado ? 'completed' : 'pending';
            const statusIcon = item.realizado ? 
                '<i class="fas fa-check-circle"></i>' : 
                '<i class="fas fa-circle"></i>';
            
            html += `
                <li class="${statusClass}">
                    <div class="exercise-info">
                        ${statusIcon}
                        <span>${item.ejercicio}</span>
                    </div>
                    <div class="exercise-input">
                        <input type="text" 
                               name="exercise_input_${index}" 
                               id="exercise_input_${index}" 
                               data-exercise="${item.ejercicio}"
                               placeholder="ej: 5x75, 7x70, 8x60" 
                               ${item.realizado ? 'disabled' : ''}
                               class="reps-input">
                    </div>
                </li>
            `;
        });
        
        html += `
                </ul>
                <button type="submit" class="btn primary-btn log-today-btn">
                    <i class="fas fa-save"></i> Registrar Entrenamiento
                </button>
            </form>
            <div id="today-response" class="response" style="display: none;"></div>
        `;
        
        // Actualizar contenido
        container.innerHTML = html;
        
        // Añadir evento al formulario
        const form = document.getElementById('todayExerciseForm');
        if (form) {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        }
    },
    
    /**
     * Maneja el envío del formulario de rutina del día
     * 
     * @param {Event} e - Evento de submit
     */
    handleFormSubmit: async function(e) {
        e.preventDefault();
        
        // Recopilar datos de los ejercicios
        const exerciseData = [];
        let hasData = false;
        
        document.querySelectorAll('.reps-input').forEach(input => {
            if (input.value.trim() !== '') {
                hasData = true;
                const exerciseName = input.getAttribute('data-exercise');
                exerciseData.push(`${exerciseName}: ${input.value.trim()}`);
            }
        });
        
        if (!hasData) {
            const responseDiv = document.getElementById('today-response');
            if (responseDiv) {
                responseDiv.style.display = 'block';
                responseDiv.className = 'response error';
                responseDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Debes completar al menos un ejercicio.';
                
                setTimeout(() => {
                    responseDiv.style.display = 'none';
                }, 5000);
            }
            
            return;
        }
        
        // Preparar datos para enviar
        const formData = new FormData();
        formData.append('exercise_data', exerciseData.join('\n'));
        
        const submitBtn = document.querySelector('.log-today-btn');
        if (submitBtn) {
            // Guardar estado original del botón
            const originalButtonContent = submitBtn.innerHTML;
            
            // Cambiar el botón a estado de carga
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            submitBtn.disabled = true;
            
            try {
                // Enviar datos
                const response = await fetch('/', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                // Mostrar respuesta
                const responseDiv = document.getElementById('today-response');
                if (responseDiv) {
                    responseDiv.style.display = 'block';
                    
                    if (data.success) {
                        responseDiv.className = 'response success';
                        responseDiv.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
                        
                        // Limpiar inputs y recargar
                        document.querySelectorAll('.reps-input').forEach(input => {
                            input.value = '';
                        });
                        
                        // Recargar después de un breve retraso
                        setTimeout(() => {
                            this.loadTodaysWorkout();
                        }, 2000);
                    } else {
                        responseDiv.className = 'response error';
                        responseDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + data.message;
                    }
                    
                    // Ocultar el mensaje después de 5 segundos
                    setTimeout(() => {
                        responseDiv.style.display = 'none';
                    }, 5000);
                }
            } catch (error) {
                console.error('Error:', error);
                
                // Mostrar error
                const responseDiv = document.getElementById('today-response');
                if (responseDiv) {
                    responseDiv.style.display = 'block';
                    responseDiv.className = 'response error';
                    responseDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error en la comunicación con el servidor.';
                    
                    // Ocultar el mensaje después de 5 segundos
                    setTimeout(() => {
                        responseDiv.style.display = 'none';
                    }, 5000);
                }
            } finally {
                // Restaurar el botón
                submitBtn.innerHTML = originalButtonContent;
                submitBtn.disabled = false;
            }
        }
    }
};

// Inicializar el módulo cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    TodayRoutine.init();
});

// Hacer disponible el módulo globalmente
window.TodayRoutine = TodayRoutine;