/**
 * Módulo de autenticación
 * Maneja la autenticación con Google y vinculación de Telegram
 */

const Auth = {
    // Estado compartido
    state: {
        isProcessing: false,
        googleClientId: null,
    },
    
    /**
     * Inicializa la funcionalidad de autenticación
     */
    init: function() {
        // Verificar si estamos en la página de login
        if (document.getElementById('google-login-btn')) {
            this.setupGoogleAuth();
        }
        
        // Verificar si hay un botón de generación de código
        const linkCodeBtn = document.getElementById('generate-link-code-btn');
        if (linkCodeBtn) {
            linkCodeBtn.addEventListener('click', this.handleGenerateCode.bind(this));
        }
        
        // Verificar si hay botón de copia de código
        const copyCodeBtn = document.getElementById('copy-code-btn');
        if (copyCodeBtn) {
            copyCodeBtn.addEventListener('click', this.handleCopyCode.bind(this));
        }
    },
    
    /**
     * Configura la autenticación con Google
     */
    setupGoogleAuth: function() {
        // Si Google Sign-In API no está cargada, mostramos error
        if (typeof google === 'undefined' || !google.accounts) {
            console.error('Google Sign-In API no está cargada');
            const googleLoginBtn = document.getElementById('google-login-btn');
            if (googleLoginBtn) {
                googleLoginBtn.innerHTML = 'Error: API de Google no disponible';
                googleLoginBtn.disabled = true;
            }
            return;
        }
        
        // Obtener ID de cliente de Google
        const googleClientId = document.getElementById('google-client-id');
        if (googleClientId) {
            this.state.googleClientId = googleClientId.value;
        } else {
            // Buscar en el HTML (en el caso de que esté en el código inline)
            const scripts = document.querySelectorAll('script');
            scripts.forEach(script => {
                const match = script.textContent.match(/['"]client_id['"]:\s*['"]([^'"]+)['"]/);
                if (match && match[1]) {
                    this.state.googleClientId = match[1];
                }
            });
        }
        
        if (!this.state.googleClientId) {
            console.error('No se pudo obtener el ID de cliente de Google');
            return;
        }
        
        // Inicializar OAuth de Google
        google.accounts.id.initialize({
            client_id: this.state.googleClientId,
            callback: this.handleGoogleCredentialResponse.bind(this)
        });
        
        // Renderizar botón de Google Sign-In si existe un contenedor
        const googleLoginBtn = document.getElementById('google-login-btn');
        if (googleLoginBtn) {
            google.accounts.id.renderButton(
                googleLoginBtn,
                { theme: "outline", size: "large" }
            );
        }
    },
    
    /**
     * Maneja la respuesta de credenciales de Google
     * 
     * @param {Object} response - Respuesta con el token de ID
     */
    handleGoogleCredentialResponse: async function(response) {
        if (this.state.isProcessing) return;
        this.state.isProcessing = true;
        
        // Mostrar indicador de carga
        const loadingIndicator = document.createElement('div');
        loadingIndicator.innerHTML = '<div class="spinner"></div>Iniciando sesión...';
        loadingIndicator.className = 'text-center text-blue-600 mt-4';
        
        const googleLoginBtn = document.getElementById('google-login-btn');
        if (googleLoginBtn) {
            googleLoginBtn.style.display = 'none';
            googleLoginBtn.parentNode.appendChild(loadingIndicator);
        }
        
        try {
            // Obtener código de vinculación de Telegram si está visible
            const linkCodeDisplay = document.getElementById('link-code-display');
            const telegramCode = linkCodeDisplay && linkCodeDisplay.textContent !== 'XXXXXX' 
                ? linkCodeDisplay.textContent 
                : null;
            
            // Verificar el token de Google
            const verifyResponse = await fetch('/auth/google/verify', {
                method: 'POST',
                credentials: 'include',  // Importante para manejar cookies
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id_token: response.credential,
                    telegram_id: telegramCode
                })
            });
            
            const data = await verifyResponse.json();
            
            if (data.success) {
                // Redirigir a la página principal o la indicada en la respuesta
                window.location.href = data.redirect || '/';
            } else {
                // Mostrar error
                alert(data.message || 'Error al iniciar sesión');
                window.location.reload();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al conectar con el servidor');
            window.location.reload();
        } finally {
            this.state.isProcessing = false;
        }
    },
    
    /**
     * Maneja la generación de código de vinculación
     */
    handleGenerateCode: async function() {
        const btn = document.getElementById('generate-link-code-btn');
        if (!btn || this.state.isProcessing) return;
        
        this.state.isProcessing = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<div class="spinner"></div>Generando código...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/generate-link-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Mostrar instrucciones y código
                const linkInstructions = document.getElementById('link-instructions');
                if (linkInstructions) {
                    linkInstructions.style.display = 'block';
                }
                
                const linkCodeDisplay = document.getElementById('link-code-display');
                if (linkCodeDisplay) {
                    linkCodeDisplay.textContent = data.code;
                }
                
                btn.style.display = 'none';
            } else {
                alert(data.message || 'No se pudo generar el código');
                btn.innerHTML = originalText;
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al conectar con el servidor');
            btn.innerHTML = originalText;
        } finally {
            btn.disabled = false;
            this.state.isProcessing = false;
        }
    },
    
    /**
     * Maneja la copia del código de vinculación
     */
    handleCopyCode: function() {
        const codeDisplay = document.getElementById('link-code-display');
        if (!codeDisplay) return;
        
        const code = codeDisplay.textContent;
        
        // Copiar al portapapeles usando la API moderna
        if (navigator.clipboard) {
            navigator.clipboard.writeText(code)
                .then(() => {
                    // Indicar éxito
                    alert('Código copiado al portapapeles');
                })
                .catch(err => {
                    console.error('Error al copiar:', err);
                    // Método alternativo
                    this.fallbackCopyCode(code);
                });
        } else {
            // Navegadores que no soportan clipboard API
            this.fallbackCopyCode(code);
        }
    },
    
    /**
     * Método alternativo para copiar texto
     * 
     * @param {string} text - Texto a copiar
     */
    fallbackCopyCode: function(text) {
        // Crear elemento temporal
        const textArea = document.createElement('textarea');
        textArea.value = text;
        
        // Ocultar el elemento
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        
        // Seleccionar y copiar
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                alert('Código copiado al portapapeles');
            } else {
                console.error('Fallo al copiar el texto');
                alert('No se pudo copiar el código. Por favor, cópialo manualmente.');
            }
        } catch (err) {
            console.error('Error al intentar copiar', err);
            alert('No se pudo copiar el código. Por favor, cópialo manualmente.');
        }
        
        // Limpiar
        document.body.removeChild(textArea);
    }
};

// Inicializar el módulo cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    Auth.init();
});

// Hacer disponible el módulo globalmente
window.Auth = Auth;