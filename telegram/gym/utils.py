# utils.py
import datetime
import os
import sys
from datetime import datetime

MAX_MESSAGE_LENGTH = 4096

# Configuración de colores para la consola si el sistema lo soporta
COLORS = {
    "RESET": "\033[0m",
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "PURPLE": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m"
}

# Asignar colores a diferentes tipos de mensajes
LOG_COLORS = {
    "ERROR": COLORS["RED"],
    "WARNING": COLORS["YELLOW"],
    "INFO": COLORS["GREEN"],
    "INPUT": COLORS["CYAN"],
    "OUTPUT": COLORS["PURPLE"],
    "API": COLORS["BLUE"],
    "PROCESS": COLORS["WHITE"],
    "SUCCESS": COLORS["GREEN"],
    "ACCESS_DENIED": COLORS["RED"]
}

def color_enabled():
    """Comprueba si los colores en la consola están disponibles y habilitados"""
    # Habilitar siempre en Unix/Linux/Mac
    if os.name == 'posix':
        return True
    # En Windows, depende de la versión y configuración
    elif os.name == 'nt':
        return 'ANSICON' in os.environ or os.environ.get('TERM') == 'xterm'
    return False

def log_to_console(message, level="INFO"):
    """
    Registra un mensaje en la consola con formato y colores si están disponibles.
    Args:
        message: El mensaje a mostrar
        level: Nivel del mensaje (ERROR, WARNING, INFO, etc.)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Aplicar colores solo si están disponibles
    if color_enabled():
        color = LOG_COLORS.get(level, COLORS["RESET"])
        formatted_message = f"{COLORS['YELLOW']}[{now}]{COLORS['RESET']} {color}[{level}]{COLORS['RESET']} {message}"
    else:
        formatted_message = f"[{now}] [{level}] {message}"
    
    print(formatted_message, flush=True)

def send_message_split(bot, chat_id, text, parse_mode=None):
    """Envía el mensaje en fragmentos si excede el límite permitido."""
    if not text:
        log_to_console(f"Intento de enviar mensaje vacío a {chat_id}", "WARNING")
        return
        
    # Registrar que estamos enviando un mensaje (resumido si es muy largo)
    log_preview = text[:100] + "..." if len(text) > 100 else text
    log_to_console(f"Enviando mensaje a {chat_id}: {log_preview}", "OUTPUT")
    
    # Dividir y enviar el mensaje en fragmentos
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        fragment = text[i : i + MAX_MESSAGE_LENGTH]
        bot.send_message(chat_id, fragment, parse_mode=parse_mode)
        log_to_console(f"Fragmento {i//MAX_MESSAGE_LENGTH + 1} enviado a {chat_id}", "INFO")

def format_logs(logs):
    """
    Formatea la lista de logs para que se muestre de forma legible.
    Cada log debe tener 'ejercicio', 'fecha' y 'data'.
    Si 'data' es una lista, se muestran los detalles (peso y repeticiones).
    """
    if not logs:
        return "No hay registros de ejercicios en el período solicitado."
        
    log_to_console(f"Formateando {len(logs)} registros de ejercicios", "PROCESS")
    
    formatted = ""
    for log in logs:
        ejercicio = log.get("ejercicio", "Sin nombre")
        fecha = log.get("fecha", "Sin fecha")
        formatted += f"Ejercicio: {ejercicio}\n"
        formatted += f"Fecha: {fecha}\n"
        data = log.get("data")
        if isinstance(data, list):
            formatted += "Series:\n"
            for serie in data:
                peso = serie.get("peso", "N/A")
                reps = serie.get("repeticiones", "N/A")
                formatted += f"  - Peso: {peso}, Reps: {reps}\n"
        else:
            formatted += f"Data: {data}\n"
        formatted += "\n"
    
    log_to_console(f"Formato completado. {len(formatted)} caracteres generados", "PROCESS")
    return formatted

def is_user_whitelisted(user_id):
    """
    Verifica si el id del usuario (user_id) está en la whitelist.
    Se asume que 'whitelist.txt' contiene un id por línea.
    """
    whitelist_path = os.path.join(os.path.dirname(__file__), "whitelist.txt")
    log_to_console(f"Verificando acceso para usuario {user_id}", "PROCESS")
    
    try:
        if not os.path.exists(whitelist_path):
            log_to_console(f"¡Archivo {whitelist_path} no encontrado!", "ERROR")
            return False
            
        with open(whitelist_path, "r") as f:
            whitelist = {line.strip() for line in f if line.strip()}
        
        is_allowed = str(user_id) in whitelist
        log_to_console(f"Usuario {user_id} {'está' if is_allowed else 'NO está'} en la lista blanca", "INFO")
        return is_allowed
        
    except Exception as e:
        # Si ocurre algún error, se niega el acceso por seguridad.
        log_to_console(f"Error al leer {whitelist_path}: {e}", "ERROR")
        return False
        
    except Exception as e:
        # Si ocurre algún error, se niega el acceso por seguridad.
        log_to_console(f"Error al leer {whitelist_path}: {e}", "ERROR")
        return False

def log_denied_access(user_id, message_text):
    """
    Registra en 'peticiones.txt' el intento de acceso denegado con la fecha, id y texto del mensaje.
    """
    try:
        with open("peticiones.txt", "a") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{now} - Acceso denegado para usuario {user_id}: {message_text}\n"
            f.write(log_entry)
            log_to_console(f"Registro guardado en peticiones.txt", "INFO")
    except Exception as e:
        log_to_console(f"Error al registrar en peticiones.txt: {e}", "ERROR")