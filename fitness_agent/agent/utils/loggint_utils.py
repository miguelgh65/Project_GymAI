# fitness_agent/agent/utils/logging_utils.py
import logging
import sys
from typing import Optional

def configure_logger(
    name: str = "fitness_agent", 
    level: int = logging.INFO, 
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura y devuelve un logger para la aplicación.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging
        log_file: Ruta del archivo de log (opcional)
    
    Returns:
        Objeto logger configurado
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Formatear los mensajes
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Configurar handler de archivo si se proporciona
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_error(logger: logging.Logger, message: str, exc_info: bool = False):
    """
    Registra un mensaje de error.
    
    Args:
        logger: Objeto logger
        message: Mensaje de error
        exc_info: Si se debe incluir información de excepción
    """
    logger.error(message, exc_info=exc_info)

def log_info(logger: logging.Logger, message: str):
    """
    Registra un mensaje de información.
    
    Args:
        logger: Objeto logger
        message: Mensaje de información
    """
    logger.info(message)