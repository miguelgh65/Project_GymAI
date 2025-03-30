/**
 * Módulo de utilidades - Funciones auxiliares reutilizables
 */

const Utils = {
    /**
     * Formatea una fecha para mostrarla
     * 
     * @param {string|Date} date - Fecha a formatear
     * @param {boolean} includeTime - Incluir hora en el formato
     * @returns {string} Fecha formateada
     */
    formatDate: function(date, includeTime = false) {
        if (!date) return 'Sin fecha';
        
        const dateObj = date instanceof Date ? date : new Date(date);
        
        // Verificar si la fecha es válida
        if (isNaN(dateObj.getTime())) {
            return 'Fecha inválida';
        }
        
        // Opciones de formato
        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        };
        
        // Añadir opciones de hora si se solicita
        if (includeTime) {
            options.hour = '2-digit';
            options.minute = '2-digit';
        }
        
        return dateObj.toLocaleDateString('es-ES', options);
    },
    
    /**
     * Crea un elemento de respuesta para el usuario
     * 
     * @param {string} type - Tipo de respuesta ('success' o 'error')
     * @param {string} message - Mensaje a mostrar
     * @param {HTMLElement} container - Contenedor donde mostrar la respuesta
     * @param {number} timeout - Tiempo en ms para ocultar automáticamente (0 para no ocultar)
     */
    showResponse: function(type, message, container, timeout = 5000) {
        if (!container) return;
        
        // Configurar clase y contenido
        container.className = `response ${type}`;
        
        // Añadir icono apropiado
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
        container.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
        
        // Mostrar el contenedor
        container.style.display = 'block';
        
        // Ocultar automáticamente después del tiempo especificado
        if (timeout > 0) {
            setTimeout(() => {
                container.style.display = 'none';
            }, timeout);
        }
    },
    
    /**
     * Deshabilita un botón y muestra un indicador de carga
     * 
     * @param {HTMLElement} button - Botón a deshabilitar
     * @param {string} loadingText - Texto a mostrar durante la carga (opcional)
     * @returns {string} Contenido original del botón para restaurarlo después
     */
    setButtonLoading: function(button, loadingText = 'Procesando...') {
        if (!button) return '';
        
        // Guardar contenido original
        const originalContent = button.innerHTML;
        
        // Cambiar a estado de carga
        button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${loadingText}`;
        button.disabled = true;
        
        return originalContent;
    },
    
    /**
     * Restaura un botón a su estado original
     * 
     * @param {HTMLElement} button - Botón a restaurar
     * @param {string} originalContent - Contenido original del botón
     */
    restoreButton: function(button, originalContent) {
        if (!button) return;
        
        button.innerHTML = originalContent;
        button.disabled = false;
    },
    
    /**
     * Divide un texto largo en fragmentos más pequeños
     * 
     * @param {string} text - Texto a dividir
     * @param {number} maxLength - Longitud máxima de cada fragmento
     * @returns {string[]} Array de fragmentos
     */
    splitText: function(text, maxLength = 4000) {
        if (!text) return [];
        if (text.length <= maxLength) return [text];
        
        const chunks = [];
        for (let i = 0; i < text.length; i += maxLength) {
            chunks.push(text.substring(i, i + maxLength));
        }
        
        return chunks;
    },
    
    /**
     * Valida un campo de formulario
     * 
     * @param {HTMLElement} field - Campo a validar
     * @param {Function} validationFn - Función de validación que devuelve true si es válido
     * @param {string} errorMessage - Mensaje de error si la validación falla
     * @returns {boolean} Resultado de la validación
     */
    validateField: function(field, validationFn, errorMessage) {
        if (!field) return false;
        
        const isValid = validationFn(field.value);
        
        if (!isValid) {
            // Añadir clase de error
            field.classList.add('error');
            
            // Crear mensaje de error si no existe
            let errorElement = field.nextElementSibling;
            if (!errorElement || !errorElement.classList.contains('error-message')) {
                errorElement = document.createElement('div');
                errorElement.className = 'error-message';
                field.parentNode.insertBefore(errorElement, field.nextSibling);
            }
            
            errorElement.textContent = errorMessage;
        } else {
            // Eliminar clase de error
            field.classList.remove('error');
            
            // Eliminar mensaje de error si existe
            const errorElement = field.nextElementSibling;
            if (errorElement && errorElement.classList.contains('error-message')) {
                errorElement.remove();
            }
        }
        
        return isValid;
    }
};

// Exportar módulo Utils
window.Utils = Utils;