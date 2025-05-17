# fitness_chatbot/chains/progress_chain.py
import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

def detect_exercise_in_query(query: str) -> str:
    """
    Detecta si hay algún ejercicio específico mencionado en la consulta.
    Esta función debe ser exportable para otros módulos.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Nombre del ejercicio o cadena vacía si no se detecta
    """
    query_lower = query.lower()
    
    # Detección específica para press banca
    if "press" in query_lower and ("banca" in query_lower or "banc" in query_lower):
        return "press banca"
    
    # Lista simple de ejercicios comunes
    common_exercises = [
        "sentadilla", "sentadillas", "squat", "squats",
        "peso muerto", "deadlift",
        "dominada", "dominadas", "pull up", "pullup",
        "curl biceps", "curl de bíceps", "bicep curl",
        "press militar", "military press",
        "fondos", "dips",
        "remo", "row"
    ]
    
    for exercise in common_exercises:
        if exercise in query_lower:
            return exercise
    
    return ""

async def process_query(user_id: str, query: str, user_context: Dict[str, Any] = None) -> str:
    """
    Procesa una consulta sobre progreso y genera un análisis completo.
    
    Args:
        user_id: ID del usuario
        query: Consulta en lenguaje natural
        user_context: Contexto con datos recolectados por otros nodos
        
    Returns:
        Respuesta formateada con análisis de progreso
    """
    logger.info(f"🚀 ProgressChain procesando: '{query}' para usuario {user_id}")
    
    if not user_context:
        user_context = {}
    
    try:
        # Verificar si tenemos datos suficientes para hacer análisis
        exercise_history = user_context.get("exercise_history", [])
        has_exercise_history = len(exercise_history) > 0
        
        if not has_exercise_history:
            logger.warning("⚠️ No hay datos suficientes para análisis de progreso")
            return "No tengo suficientes datos para analizar tu progreso."
        
        # Detectar si la consulta menciona press banca o similares
        query_lower = query.lower()
        specific_exercise = None
        if "press" in query_lower and ("banca" in query_lower or "banc" in query_lower):
            specific_exercise = "press banca"
        
        # Si se detectó press banca, analizar directamente
        if specific_exercise:
            logger.info(f"🏋️ Ejercicio específico detectado: {specific_exercise}")
            # Filtrar ejercicios de press banca
            press_banca_data = []
            for entry in exercise_history:
                if entry.get('ejercicio', '') == specific_exercise:
                    press_banca_data.append(entry)
            
            # Generar análisis directo sin usar LLM
            return generate_press_banca_analysis(press_banca_data)
        
        # Para otros casos, usar análisis genérico
        return "He analizado tus datos de entrenamiento y puedo ver que has estado entrenando regularmente. Para un análisis más específico, pregúntame sobre un ejercicio concreto como 'press banca'."
        
    except Exception as e:
        logger.exception(f"❌ Error en ProgressChain: {str(e)}")
        return "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."

def generate_press_banca_analysis(press_banca_data: List[Dict[str, Any]]) -> str:
    """
    Genera un análisis específico para press banca sin usar LLM.
    
    Args:
        press_banca_data: Lista de registros de press banca
        
    Returns:
        Análisis de progreso formateado
    """
    if not press_banca_data:
        return "No encontré registros de press banca en tu historial."
    
    # Ordenar por fecha (de más antiguo a más reciente)
    press_banca_data.sort(key=lambda x: x.get('fecha', ''))
    
    # Extraer datos básicos
    num_sessions = len(press_banca_data)
    first_session = press_banca_data[0]
    last_session = press_banca_data[-1]
    
    # Calcular fechas legibles
    first_date = first_session.get('fecha', '').split('T')[0] if 'T' in first_session.get('fecha', '') else first_session.get('fecha', '')
    last_date = last_session.get('fecha', '').split('T')[0] if 'T' in last_session.get('fecha', '') else last_session.get('fecha', '')
    
    # Calcular peso máximo usado
    max_weight = 0
    for session in press_banca_data:
        for serie in session.get('repeticiones', []):
            if isinstance(serie, dict):
                peso = serie.get('peso', 0)
                if peso > max_weight:
                    max_weight = peso
    
    # Calcular 1RM estimado para primera y última sesión
    first_1rm = calculate_1rm(first_session.get('repeticiones', []))
    last_1rm = calculate_1rm(last_session.get('repeticiones', []))
    
    # Calcular cambio porcentual
    if first_1rm > 0:
        change_percent = ((last_1rm - first_1rm) / first_1rm) * 100
    else:
        change_percent = 0
    
    # Crear análisis
    analysis = f"# Análisis de Progreso en Press Banca\n\n"
    analysis += f"He analizado tus {num_sessions} sesiones de press banca registradas entre {first_date} y {last_date}.\n\n"
    
    analysis += "## Resumen\n\n"
    analysis += f"* **Peso máximo utilizado:** {max_weight} kg\n"
    analysis += f"* **1RM estimado inicial:** {first_1rm:.1f} kg\n"
    analysis += f"* **1RM estimado actual:** {last_1rm:.1f} kg\n"
    
    if change_percent > 0:
        analysis += f"* **Progreso:** +{change_percent:.1f}% de mejora\n\n"
        analysis += "¡Has mostrado un progreso positivo! Tu fuerza máxima estimada ha aumentado significativamente desde tu primera sesión registrada.\n\n"
    elif change_percent < 0:
        analysis += f"* **Cambio:** {change_percent:.1f}% (reducción)\n\n"
        analysis += "Tu fuerza máxima estimada ha disminuido desde tu primera sesión registrada. Esto podría deberse a fatiga, técnica, o factores como nutrición y descanso.\n\n"
    else:
        analysis += "* **Progreso:** Estable\n\n"
        analysis += "Tu fuerza se ha mantenido estable durante el período analizado.\n\n"
    
    analysis += "## Recomendaciones\n\n"
    
    if change_percent >= 0:
        analysis += "1. **Continúa con tu progresión gradual** - Sigue aumentando el peso de manera progresiva.\n"
        analysis += "2. **Considera variaciones** - Añade press inclinado o declinado para desarrollo completo.\n"
        analysis += f"3. **Próximo objetivo:** Intenta llegar a {(last_1rm * 1.05):.1f} kg de 1RM en las próximas semanas.\n"
    else:
        analysis += "1. **Revisa tu técnica** - Asegúrate de ejecutar correctamente el movimiento.\n"
        analysis += "2. **Evalúa recuperación** - El descanso y la nutrición son clave para el progreso.\n"
        analysis += "3. **Considera un deload** - Una semana de menor intensidad podría ayudar a recuperarte.\n"
    
    return analysis

# fitness_chatbot/chains/progress_chain.py (sección modificada)

def calculate_1rm(repeticiones: List[Dict[str, Any]]) -> float:
    """
    Calcula el 1RM estimado usando la fórmula de Brzycki.
    
    Args:
        repeticiones: Lista de series con repeticiones y pesos
        
    Returns:
        1RM estimado
    """
    max_1rm = 0
    
    # Verificar si es el formato nuevo (series_json) o antiguo (repeticiones)
    if isinstance(repeticiones, list):
        for serie in repeticiones:
            if isinstance(serie, dict):
                # Buscar los campos correspondientes según el formato
                if "repeticiones" in serie and "peso" in serie:
                    # Formato nuevo (series_json)
                    reps = serie.get('repeticiones', 0)
                    peso = serie.get('peso', 0)
                elif "reps" in serie and "weight" in serie:
                    # Formato antiguo 
                    reps = serie.get('reps', 0)
                    peso = serie.get('weight', 0)
                else:
                    # Formato desconocido
                    continue
                
                if reps > 0 and reps < 37 and peso > 0:
                    # Fórmula de Brzycki: 1RM = peso × (36 / (37 - repeticiones))
                    current_1rm = peso * (36 / (37 - reps))
                    max_1rm = max(max_1rm, current_1rm)
    
    return max_1rm

def generate_press_banca_analysis(press_banca_data: List[Dict[str, Any]]) -> str:
    """
    Genera un análisis específico para press banca sin usar LLM.
    
    Args:
        press_banca_data: Lista de registros de press banca
        
    Returns:
        Análisis de progreso formateado
    """
    if not press_banca_data:
        return "No encontré registros de press banca en tu historial."
    
    # Ordenar por fecha (de más antiguo a más reciente)
    press_banca_data.sort(key=lambda x: x.get('fecha', ''))
    
    # Extraer datos básicos
    num_sessions = len(press_banca_data)
    first_session = press_banca_data[0]
    last_session = press_banca_data[-1]
    
    # Calcular fechas legibles
    first_date = first_session.get('fecha', '').split('T')[0] if 'T' in first_session.get('fecha', '') else first_session.get('fecha', '')
    last_date = last_session.get('fecha', '').split('T')[0] if 'T' in last_session.get('fecha', '') else last_session.get('fecha', '')
    
    # Calcular peso máximo usado
    max_weight = 0
    
    # MODIFICADO: Verificar si estamos usando series_json o repeticiones
    for session in press_banca_data:
        # Verificar primero el formato nuevo (series_json)
        if 'series_json' in session and session['series_json']:
            series_data = session['series_json']
            # Convertir a JSON si es string
            if isinstance(series_data, str):
                try:
                    series_data = json.loads(series_data)
                except:
                    series_data = []
                    
            # Extraer peso máximo
            for serie in series_data:
                if isinstance(serie, dict):
                    peso = serie.get('peso', 0)
                    if peso > max_weight:
                        max_weight = peso
        
        # Verificar el formato antiguo (repeticiones)
        elif 'repeticiones' in session and session['repeticiones']:
            series = session.get('repeticiones', [])
            # Convertir a JSON si es string
            if isinstance(series, str):
                try:
                    series = json.loads(series)
                except:
                    series = []
            
            # Extraer peso máximo
            for serie in series:
                if isinstance(serie, dict):
                    peso = serie.get('peso', 0)
                    if peso > max_weight:
                        max_weight = peso
    
    # Calcular 1RM estimado para primera y última sesión
    # MODIFICADO: Extraer series de series_json si existe, o de repeticiones si no
    first_series = None
    last_series = None
    
    if 'series_json' in first_session and first_session['series_json']:
        if isinstance(first_session['series_json'], str):
            try:
                first_series = json.loads(first_session['series_json'])
            except:
                pass
        else:
            first_series = first_session['series_json']
    elif 'repeticiones' in first_session:
        if isinstance(first_session['repeticiones'], str):
            try:
                first_series = json.loads(first_session['repeticiones'])
            except:
                pass
        else:
            first_series = first_session['repeticiones']
    
    if 'series_json' in last_session and last_session['series_json']:
        if isinstance(last_session['series_json'], str):
            try:
                last_series = json.loads(last_session['series_json'])
            except:
                pass
        else:
            last_series = last_session['series_json']
    elif 'repeticiones' in last_session:
        if isinstance(last_session['repeticiones'], str):
            try:
                last_series = json.loads(last_session['repeticiones'])
            except:
                pass
        else:
            last_series = last_session['repeticiones']
    
    first_1rm = calculate_1rm(first_series) if first_series else 0
    last_1rm = calculate_1rm(last_series) if last_series else 0
    
    # Calcular cambio porcentual
    if first_1rm > 0:
        change_percent = ((last_1rm - first_1rm) / first_1rm) * 100
    else:
        change_percent = 0