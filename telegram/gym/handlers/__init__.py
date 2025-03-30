# telegram/gym/handlers/__init__.py
from .base_handlers import register_middleware
from .auth_handlers import register_auth_handlers
from .exercise_handlers import register_exercise_handlers
from .routine_handlers import register_routine_handlers
from .chatbot_handlers import register_chatbot_handlers

def register_all_handlers(bot):
    """
    Registra todos los handlers del bot en el orden correcto.
    
    Args:
        bot: Instancia del bot de Telegram
    """
    # Primero registramos el middleware (logging, autenticación, etc)
    register_middleware(bot)
    
    # Luego registramos los manejadores específicos
    register_auth_handlers(bot)
    register_exercise_handlers(bot)
    register_routine_handlers(bot)
    register_chatbot_handlers(bot)
    
    print("✅ Todos los handlers registrados correctamente")