# telegram/gym/__init__.py
# Este archivo permite que el directorio telegram/gym sea tratado como un paquete de Python.
# Puedes importar módulos y subpaquetes desde aquí si es necesario.

# Configuración básica de logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_bot.log')
    ]
)

# Puedes agregar aquí variables globales, funciones o importaciones comunes
__version__ = "1.0.0"