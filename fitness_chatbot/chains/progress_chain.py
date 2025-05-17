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
    Procesa una consulta sobre progreso y genera un análisis completo utilizando LLM.
    
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
        
        # Los datos de Fitbit son opcionales, no un requisito para el análisis
        fitbit_data = user_context.get("fitbit_data", {})
        has_fitbit_data = fitbit_data.get("available", False)
        
        if not has_exercise_history:
            logger.warning("⚠️ No hay datos suficientes para análisis de progreso")
            return "No tengo suficientes datos para analizar tu progreso. Necesito que registres más ejercicios primero."
        
        # Detectar ejercicio específico mencionado en la consulta
        specific_exercise = user_context.get("specific_exercise") or detect_exercise_in_query(query)
        
        if specific_exercise:
            logger.info(f"🏋️ Ejercicio específico detectado: {specific_exercise}")
            # Filtrar ejercicios para el específico mencionado
            filtered_exercises = [e for e in exercise_history if e.get('ejercicio', '').lower() == specific_exercise.lower()]
            if filtered_exercises:
                logger.info(f"Se encontraron {len(filtered_exercises)} registros para {specific_exercise}")
                exercise_history = filtered_exercises
                
                # Asegurarse de que hay suficientes registros para analizar
                if len(filtered_exercises) < 2:
                    logger.warning(f"⚠️ Solo se encontró {len(filtered_exercises)} registro para {specific_exercise}, se necesitan al menos 2 para analizar progreso")
                    return f"He encontrado {len(filtered_exercises)} sesión de {specific_exercise}, pero necesito al menos 2 para poder analizar tu progreso. Sigue registrando tus entrenamientos y pronto podré darte un análisis detallado."
            else:
                logger.warning(f"⚠️ No se encontraron registros para {specific_exercise}")
                return f"No encontré ningún registro de '{specific_exercise}' en tu historial. ¿Quieres que te ayude a registrar este ejercicio?"
        
        # Estructurar datos para el LLM
        progress_data = {
            "exercise_history": exercise_history,
            "fitbit_data": fitbit_data,
            "specific_exercise": specific_exercise
        }
        
        # Preparar el contexto para el LLM
        analysis_context = prepare_analysis_context(progress_data)
        logger.info(f"Preparado contexto de análisis con {len(analysis_context)} caracteres")
        
        # Usar el LLM para generar el análisis
        llm = get_llm()
        if not llm:
            logger.error("LLM no disponible para generar análisis de progreso")
            return "Lo siento, no puedo analizar tu progreso en este momento debido a un problema técnico."
        
        # Obtener prompts para análisis de progreso
        messages = PromptManager.get_prompt_messages(
            "progress",
            query=query,
            user_context=analysis_context
        )
        
        # Invocar el LLM
        logger.info("🧠 Enviando datos al LLM para análisis de progreso")
        response = await llm.ainvoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Verificar si la respuesta es válida
        if not content or len(content.strip()) < 50:
            logger.warning(f"⚠️ Respuesta del LLM demasiado corta o vacía: '{content}'")
            return "Lo siento, tuve un problema al analizar tu progreso. Los datos están disponibles pero no pude generar un análisis detallado. Por favor, intenta de nuevo más tarde."
        
        logger.info(f"✅ Análisis generado exitosamente ({len(content)} caracteres)")
        return content
    
    except Exception as e:
        logger.exception(f"❌ Error en ProgressChain: {str(e)}")
        return "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."

def prepare_analysis_context(progress_data: Dict[str, Any]) -> str:
    """
    Prepara un contexto detallado para el LLM basado en los datos recopilados.
    
    Args:
        progress_data: Datos de progreso recopilados
        
    Returns:
        Contexto formateado para el LLM
    """
    exercise_history = progress_data.get("exercise_history", [])
    fitbit_data = progress_data.get("fitbit_data", {})
    specific_exercise = progress_data.get("specific_exercise", "")
    
    context = "=== HISTORIAL DE EJERCICIOS ===\n\n"
    
    # Si hay un ejercicio específico, enfocarse en él
    if specific_exercise and any(e.get('ejercicio') == specific_exercise for e in exercise_history):
        specific_exercises = [e for e in exercise_history if e.get('ejercicio') == specific_exercise]
        context += f"EJERCICIO ESPECÍFICO: {specific_exercise}\n"
        context += f"Total de sesiones: {len(specific_exercises)}\n\n"
        
        # Mostrar detalles de cada sesión (limitado a las últimas 10)
        for i, session in enumerate(specific_exercises[:10]):
            # Formato de fecha mejorado
            date_str = ""
            if 'fecha' in session:
                date_raw = session.get('fecha', '')
                if isinstance(date_raw, str):
                    if 'T' in date_raw:
                        date_str = date_raw.split('T')[0]
                    else:
                        date_str = date_raw
                else:
                    # Si es un objeto datetime
                    try:
                        date_str = date_raw.strftime("%Y-%m-%d")
                    except:
                        date_str = str(date_raw)
            
            context += f"  Sesión {i+1} - Fecha: {date_str}\n"
            
            # Intentar extraer detalles de series con manejo mejorado de errores
            try:
                # Primero intentar con series_json (formato nuevo)
                if 'series_json' in session and session['series_json']:
                    series_data = []
                    
                    # Manejar diferentes formatos de series_json
                    if isinstance(session['series_json'], str):
                        try:
                            series_data = json.loads(session['series_json'])
                        except json.JSONDecodeError:
                            logger.warning(f"❌ Error decodificando series_json: {session['series_json'][:100]}")
                            series_data = []
                    else:
                        series_data = session['series_json']
                    
                    # Procesar series
                    if isinstance(series_data, list):
                        for j, serie in enumerate(series_data):
                            if isinstance(serie, dict):
                                reps = serie.get('repeticiones', 0)
                                peso = serie.get('peso', 0)
                                rir = serie.get('rir', None)
                                
                                serie_txt = f"    Serie {j+1}: {reps} repeticiones × {peso} kg"
                                if rir is not None:
                                    serie_txt += f" (RIR: {rir})"
                                context += serie_txt + "\n"
                            else:
                                context += f"    Serie {j+1}: {str(serie)}\n"
                
                # Si no hay series_json, intentar con repeticiones (formato antiguo)
                elif 'repeticiones' in session:
                    repetitions_data = session['repeticiones']
                    
                    # Manejar diferentes formatos de repeticiones
                    if isinstance(repetitions_data, int) or (isinstance(repetitions_data, str) and repetitions_data.isdigit()):
                        context += f"    Total repeticiones: {repetitions_data}\n"
                    elif repetitions_data:
                        rep_data = []
                        
                        # Intentar decodificar JSON si es string
                        if isinstance(repetitions_data, str):
                            try:
                                rep_data = json.loads(repetitions_data)
                            except json.JSONDecodeError:
                                logger.warning(f"❌ Error decodificando repeticiones: {repetitions_data[:100]}")
                                rep_data = []
                        else:
                            rep_data = repetitions_data
                        
                        # Procesar repeticiones como series
                        if isinstance(rep_data, list):
                            for j, rep in enumerate(rep_data):
                                if isinstance(rep, dict):
                                    reps = rep.get('repeticiones', 0)
                                    peso = rep.get('peso', 0)
                                    rir = rep.get('rir', None)
                                    
                                    rep_txt = f"    Serie {j+1}: {reps} repeticiones × {peso} kg"
                                    if rir is not None:
                                        rep_txt += f" (RIR: {rir})"
                                    context += rep_txt + "\n"
                                else:
                                    context += f"    Serie {j+1}: {str(rep)}\n"
            except Exception as e:
                logger.warning(f"❌ Error procesando series para sesión {i+1}: {str(e)}")
                context += f"    [Error procesando detalles de series]\n"
            
            # Añadir comentarios si están disponibles
            if 'comentarios' in session and session['comentarios']:
                context += f"    Comentarios: {session['comentarios']}\n"
            
            # Separador entre sesiones
            context += "\n"
    
    # Siempre incluir un resumen general
    context += "RESUMEN DE EJERCICIOS:\n"
    exercise_counts = {}
    for e in exercise_history:
        name = e.get('ejercicio', 'desconocido')
        exercise_counts[name] = exercise_counts.get(name, 0) + 1
    
    for name, count in exercise_counts.items():
        context += f"• {name}: {count} sesiones\n"
    
    # Incluir datos de Fitbit si están disponibles
    if fitbit_data.get("available", False):
        context += "\n=== DATOS DE FITBIT ===\n\n"
        
        # Datos de perfil
        if 'profile' in fitbit_data and 'user' in fitbit_data['profile']:
            user = fitbit_data['profile']['user']
            if 'weight' in user:
                context += "REGISTRO DE PESO:\n"
                context += f"  {datetime.now().strftime('%Y-%m-%d')}: {user.get('weight')} kg\n"
        
        # Datos de actividad
        if 'activity_summary' in fitbit_data:
            summary = fitbit_data['activity_summary'].get('summary', {})
            context += "\nACTIVIDAD RECIENTE:\n"
            context += f"  Pasos: {summary.get('steps', 0)}\n"
            context += f"  Calorías: {summary.get('caloriesOut', 0)}\n"
        
        # Datos de sueño
        if 'sleep_log' in fitbit_data and 'sleep' in fitbit_data['sleep_log'] and fitbit_data['sleep_log']['sleep']:
            sleep = fitbit_data['sleep_log']['sleep'][0]
            minutes = sleep.get('minutesAsleep', 0)
            hours = minutes // 60
            mins = minutes % 60
            context += f"\nSUEÑO: {hours}h {mins}m\n"
    else:
        context += "\n=== DATOS DE FITBIT ===\n"
        context += "No hay datos de Fitbit disponibles.\n"
    
    # Añadir instrucciones para el análisis
    context += "\n=== INSTRUCCIONES PARA ANÁLISIS ===\n"
    context += "1. Analiza la tendencia de progreso basada en:\n"
    context += "   - Aumento de peso utilizado\n"
    context += "   - Aumento de repeticiones totales\n"
    context += "   - Aumento de volumen total (peso × repeticiones)\n"
    context += "2. Si hay un ejercicio específico mencionado, enfócate en él\n"
    context += "3. Proporciona recomendaciones específicas para mejorar\n"
    
    return context