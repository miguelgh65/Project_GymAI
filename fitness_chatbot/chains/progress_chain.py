# fitness_chatbot/chains/progress_chain.py
import logging
from typing import Dict, Any, Optional, List
import json

from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

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
    logger.info(f"ProgressChain procesando: '{query}' para usuario {user_id}")
    
    if not user_context:
        user_context = {}
    
    try:
        # Verificar si tenemos datos suficientes para hacer análisis
        has_exercise_history = "exercise_history" in user_context and user_context["exercise_history"]
        has_fitbit_data = "fitbit_data" in user_context and user_context["fitbit_data"].get("available", False)
        
        if not has_exercise_history and not has_fitbit_data:
            logger.warning("No hay datos suficientes para análisis de progreso")
            return "No tengo suficientes datos para analizar tu progreso. Necesito tu historial de ejercicios o datos de Fitbit, pero parece que no pude obtenerlos. Por favor, intenta más tarde o asegúrate de tener datos registrados."
        
        # Detectar ejercicio específico en la consulta
        specific_exercise = detect_exercise_in_query(query)
        if specific_exercise:
            user_context["specific_exercise"] = specific_exercise
            logger.info(f"Ejercicio específico detectado: {specific_exercise}")
        
        # Formatear contexto para la IA
        context_text = format_context_for_llm(user_context)
        
        # Obtener LLM para análisis
        llm = get_llm()
        if not llm:
            logger.error("LLM no disponible para análisis de progreso")
            return "Lo siento, no puedo analizar tu progreso en este momento debido a un problema técnico. Por favor, intenta más tarde."
        
        # Preparar mensajes usando PromptManager
        messages = PromptManager.get_prompt_messages(
            "progress", 
            query=query,
            user_context=context_text
        )
        
        # Configurar el LLM para respuestas más detalladas
        if hasattr(llm, 'with_temperature'):
            llm = llm.with_temperature(0.2)
            
        if hasattr(llm, 'with_max_tokens'):
            llm = llm.with_max_tokens(2048)
        
        # Invocar LLM para análisis
        logger.info("Analizando progreso con IA")
        response = await llm.ainvoke(messages)
        analysis = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"Análisis generado: {len(analysis)} caracteres")
        return analysis
        
    except Exception as e:
        logger.exception(f"Error en ProgressChain: {str(e)}")
        return "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."

def detect_exercise_in_query(query: str) -> str:
    """
    Detecta si hay algún ejercicio específico mencionado en la consulta.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Nombre del ejercicio o cadena vacía si no se detecta
    """
    # Lista de ejercicios comunes para detectar
    common_exercises = [
        "press banca", "press de banca", "bench press",
        "sentadilla", "sentadillas", "squat", "squats",
        "peso muerto", "deadlift",
        "dominada", "dominadas", "pull up", "pullup",
        "press militar", "military press",
        "curl biceps", "curl de bíceps", "bicep curl",
        "extensiones", "extensión", "extension",
        "fondos", "dips",
        "remo", "row"
    ]
    
    # Convertir la consulta a minúsculas para facilitar la detección
    query_lower = query.lower()
    
    # Buscar coincidencias con ejercicios comunes
    for exercise in common_exercises:
        if exercise in query_lower:
            return exercise
    
    return ""

def format_context_for_llm(context: Dict[str, Any]) -> str:
    """
    Formatea el contexto con los datos recolectados para el análisis de progreso.
    
    Args:
        context: Datos recopilados (exercise_history, fitbit_data, etc.)
        
    Returns:
        Texto formateado para el prompt de IA
    """
    formatted_text = []
    
    # Añadir datos de historial de ejercicios si están disponibles
    if "exercise_history" in context and context["exercise_history"]:
        formatted_text.append("=== HISTORIAL DE EJERCICIOS ===\n")
        
        exercise_history = context["exercise_history"]
        
        # Agrupar ejercicios por tipo
        exercise_groups = {}
        for entry in exercise_history:
            exercise_name = entry.get('ejercicio', 'desconocido')
            if exercise_name not in exercise_groups:
                exercise_groups[exercise_name] = []
            exercise_groups[exercise_name].append(entry)
        
        # Si hay un ejercicio específico en la consulta, priorizarlo
        if "specific_exercise" in context:
            specific_exercise = context["specific_exercise"]
            if specific_exercise in exercise_groups:
                formatted_text.append(f"EJERCICIO ESPECÍFICO: {specific_exercise}")
                formatted_text.append(f"Total de sesiones: {len(exercise_groups[specific_exercise])}")
                
                # Ordenar por fecha
                sessions = sorted(exercise_groups[specific_exercise], 
                                 key=lambda x: x.get('fecha', ''))
                
                # Mostrar sesiones
                for i, session in enumerate(sessions, 1):
                    fecha = session.get('fecha', 'fecha desconocida')
                    repeticiones = session.get('repeticiones', [])
                    
                    formatted_text.append(f"  Sesión {i} - Fecha: {fecha}")
                    
                    if repeticiones:
                        if isinstance(repeticiones, str):
                            try:
                                repeticiones = json.loads(repeticiones)
                            except:
                                repeticiones = []
                        
                        if isinstance(repeticiones, list):
                            for j, serie in enumerate(repeticiones, 1):
                                if isinstance(serie, dict):
                                    reps = serie.get('repeticiones', 0)
                                    peso = serie.get('peso', 0)
                                    formatted_text.append(f"    Serie {j}: {reps} repeticiones × {peso} kg")
        
        # Mostrar resumen de todos los ejercicios
        formatted_text.append("\nRESUMEN DE EJERCICIOS:")
        for exercise_name, sessions in exercise_groups.items():
            # Si ya mostramos el ejercicio específico en detalle, solo un resumen
            if "specific_exercise" in context and exercise_name == context["specific_exercise"]:
                continue
                
            formatted_text.append(f"• {exercise_name}: {len(sessions)} sesiones")
            
        formatted_text.append("")  # Línea en blanco
    
    # Añadir datos de Fitbit si están disponibles
    if "fitbit_data" in context and context["fitbit_data"].get("available", False):
        formatted_text.append("=== DATOS DE FITBIT ===\n")
        fitbit_data = context["fitbit_data"]
        
        # Mostrar datos de peso si están disponibles
        if "weight" in fitbit_data:
            weight_entries = fitbit_data["weight"]
            formatted_text.append("REGISTRO DE PESO:")
            for entry in weight_entries:
                date = entry.get("date", "desconocida")
                weight = entry.get("weight", 0)
                formatted_text.append(f"  {date}: {weight} kg")
            
        # Mostrar actividad si está disponible
        if "activity_summary" in fitbit_data:
            activity = fitbit_data["activity_summary"]
            formatted_text.append("\nACTIVIDAD FÍSICA:")
            formatted_text.append(f"  Pasos: {activity.get('steps', 0)}")
            formatted_text.append(f"  Calorías: {activity.get('caloriesOut', 0)}")
            
        formatted_text.append("")  # Línea en blanco
    
    # Añadir instrucciones para análisis avanzado
    formatted_text.append("=== INSTRUCCIONES PARA ANÁLISIS ===")
    formatted_text.append("1. Si hay datos de peso y repeticiones, calcula el 1RM (repetición máxima) usando la fórmula de Brzycki:")
    formatted_text.append("   1RM = peso × (36 / (37 - repeticiones))")
    formatted_text.append("2. Analiza la tendencia de progreso basada en:")
    formatted_text.append("   - Aumento de peso utilizado")
    formatted_text.append("   - Aumento de repeticiones totales")
    formatted_text.append("   - Aumento de volumen total (peso × repeticiones)")
    formatted_text.append("3. Si hay un ejercicio específico mencionado, enfócate en él")
    formatted_text.append("4. Proporciona recomendaciones específicas para mejorar")
    
    # Si no hay datos suficientes
    if len(formatted_text) <= 3:  # Solo títulos sin contenido
        return "No hay datos suficientes para analizar el progreso."
    
    return "\n".join(formatted_text)