/**
 * Módulo de gestión de formularios de ejercicios
 * Maneja el envío de datos de ejercicios
 */

const ExerciseForm = {
    /**
     * Inicializa el formulario de ejercicios
     */
    init: function() {
        const exerciseForm = document.getElementById('exerciseForm');
        if (exerciseForm) {
            exerciseForm.addEventListener('submit', this.handleSubmit.bind(this));
            console.log("Formulario de ejercicios inicializado");
        }
    },
    
    /**
     * Maneja el envío del formulario
     * 
     * @param {Event} e - Evento de submit
     */
    handleSubmit: async function(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const responseDiv = document.getElementById('response');
        
        // Guardar estado original del botón
        const originalButtonContent = submitBtn.innerHTML;
        
        // Cambiar el botón a estado de carga
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            // Mostrar respuesta
            if (responseDiv) {
                responseDiv.style.display = 'block';
                
                if (data.success) {
                    responseDiv.className = 'response success';
                    responseDiv.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
                    
                    // Limpiar el formulario en caso de éxito
                    document.getElementById('exercise_data').value = '';
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
    },
    
    /**
     * Valida los datos del formulario
     * 
     * @param {FormData} formData - Datos del formulario
     * @returns {boolean} True si los datos son válidos
     */
    validateFormData: function(formData) {
        const exerciseData = formData.get('exercise_data');
        
        // Verificar que hay datos
        if (!exerciseData || exerciseData.trim() === '') {
            return false;
        }
        
        // Verificar formato básico (al menos un nombre de ejercicio seguido de números)
        const exercisePattern = /[a-zA-Z\s]+:?\s*\d+/;
        return exercisePattern.test(exerciseData);
    }
};

// Inicializar el módulo cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    ExerciseForm.init();
});

// Hacer disponible el módulo globalmente
window.ExerciseForm = ExerciseForm;