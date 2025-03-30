/**
 * Módulo del chatbot
 * Maneja la interacción con el chatbot de IA
 */

const Chatbot = {
    // Referencias a elementos del DOM
    elements: {
        chatForm: null,
        messageInput: null,
        chatMessages: null,
        suggestionBtns: null
    },
    
    // Datos del usuario
    userData: {
        userId: null
    },
    
    /**
     * Inicializa el chatbot
     */
    init: function() {
        // Obtener referencias a elementos del DOM
        this.elements.chatForm = document.getElementById('chat-form');
        this.elements.messageInput = document.getElementById('message-input');
        this.elements.chatMessages = document.getElementById('chat-messages');
        this.elements.suggestionBtns = document.querySelectorAll('.suggestion-btn');
        
        // Obtener ID de usuario
        const userIdElement = document.getElementById('user_id');
        if (userIdElement) {
            this.userData.userId = userIdElement.value;
        }
        
        // Configurar eventos
        if (this.elements.chatForm) {
            this.elements.chatForm.addEventListener('submit', this.handleSubmit.bind(this));
        }
        
        if (this.elements.suggestionBtns.length > 0) {
            this.elements.suggestionBtns.forEach(btn => {
                btn.addEventListener('click', this.handleSuggestion.bind(this));
            });
        }
        
        console.log("Chatbot inicializado");
    },
    
    /**
     * Maneja el envío del formulario de chat
     * 
     * @param {Event} e - Evento de submit
     */
    handleSubmit: function(e) {
        e.preventDefault();
        
        const messageText = this.elements.messageInput.value;
        this.sendMessage(messageText);
    },
    
    /**
     * Maneja el clic en un botón de sugerencia
     * 
     * @param {Event} e - Evento de click
     */
    handleSuggestion: function(e) {
        const messageText = e.target.textContent.trim();
        this.sendMessage(messageText);
    },
    
    /**
     * Envía un mensaje al chatbot
     * 
     * @param {string} messageText - Texto del mensaje
     */
    sendMessage: async function(messageText) {
        if (!messageText.trim()) return;
        
        // Mostrar mensaje del usuario
        this.appendMessage(messageText, 'user');
        this.elements.messageInput.value = '';
        this.scrollToBottom();
        
        // Mostrar indicador de escritura
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message bot-message typing-indicator';
        typingIndicator.innerHTML = '<div class="message-content"><p>Escribiendo...</p></div>';
        this.elements.chatMessages.appendChild(typingIndicator);
        this.scrollToBottom();
        
        try {
            const response = await fetch('/api/chatbot/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userData.userId,
                    message: messageText
                }),
            });
            
            const data = await response.json();
            
            // Eliminar indicador de escritura
            if (typingIndicator && typingIndicator.parentNode) {
                typingIndicator.parentNode.removeChild(typingIndicator);
            }
            
            if (data.success && data.responses) {
                data.responses.forEach(msg => {
                    let content = msg.content;
                    let role = msg.role === 'tool' ? 'system' : 'bot';
                    
                    this.appendMessage(content, role);
                });
            } else {
                this.appendMessage("Lo siento, ocurrió un error al procesar tu mensaje.", 'bot');
            }
            
            this.scrollToBottom();
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Eliminar indicador de escritura en caso de error
            if (typingIndicator && typingIndicator.parentNode) {
                typingIndicator.parentNode.removeChild(typingIndicator);
            }
            
            this.appendMessage("Lo siento, no pude conectarme con el servidor. Por favor, intenta de nuevo más tarde.", 'bot');
            this.scrollToBottom();
        }
    },
    
    /**
     * Agrega un mensaje al chat
     * 
     * @param {string} content - Contenido del mensaje
     * @param {string} type - Tipo de mensaje ('user', 'bot', 'system')
     */
    appendMessage: function(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        // Formatear contenido para detectar posibles JSON
        let formattedContent = content;
        if (typeof content === 'string' && content.trim().startsWith('{') && content.trim().endsWith('}')) {
            try {
                const jsonData = JSON.parse(content);
                formattedContent = `<pre>${JSON.stringify(jsonData, null, 2)}</pre>`;
            } catch (e) {
                // No es JSON válido, mantener el contenido original
            }
        }
        
        // Formatear listas y negritas
        if (typeof formattedContent === 'string') {
            // Convertir * texto * a <strong>texto</strong>
            formattedContent = formattedContent.replace(/\*(.*?)\*/g, '<strong>$1</strong>');
            
            // Convertir listas con guiones
            formattedContent = formattedContent.replace(/- (.*?)(?=\n|$)/g, '• $1<br>');
        }
        
        messageDiv.innerHTML = `<div class="message-content"><p>${formattedContent}</p></div>`;
        this.elements.chatMessages.appendChild(messageDiv);
    },
    
    /**
     * Desplaza el chat hacia abajo
     */
    scrollToBottom: function() {
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
};

// Inicializar el chatbot cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    Chatbot.init();
});

// Hacer disponible el módulo globalmente
window.Chatbot = Chatbot;