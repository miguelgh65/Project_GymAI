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
        
        fitbit_data = user_context.get("fitbit_data", {})
        has_fitbit_data = fitbit_data.get("available", False)
        
        if not has_exercise_history:
            logger.warning("⚠️ No hay datos suficientes para análisis de progreso")
            return "No tengo suficientes datos para analizar tu progreso. Necesito que registres más ejercicios primero."
        
        # Preparar el contexto para el LLM sin filtrar ni procesar los datos
        analysis_context = prepare_analysis_context(user_context)
        logger.info(f"Preparado contexto de análisis con {len(analysis_context)} caracteres")
        
        # Usar el LLM para generar el análisis
        llm = get_llm()
        if not llm:
            logger.error("LLM no disponible para generar análisis de progreso")
            return "Lo siento, no puedo analizar tu progreso en este momento debido a un problema técnico."
        
        # Configurar el LLM con baja temperatura para respuestas más deterministas
        if hasattr(llm, 'with_temperature'):
            llm = llm.with_temperature(0.1)
        
        # Obtener prompts para análisis de progreso
        messages = PromptManager.get_prompt_messages(
            "progress",
            query=query,
            user_context=analysis_context
        )
        
        # Invocar el LLM
        response = await llm.ainvoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        return content
    
    except Exception as e:
        logger.exception(f"❌ Error en ProgressChain: {str(e)}")
        return "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."

def prepare_analysis_context(user_context: Dict[str, Any]) -> str:
    """
    Prepara un contexto detallado para el LLM basado en los datos recopilados.
    Pasa los datos tal cual sin procesar.
    
    Args:
        user_context: Contexto de usuario completo
        
    Returns:
        Contexto formateado para el LLM
    """
    # Obtener los datos tal cual llegan, sin filtrar
    exercise_history = user_context.get("exercise_history", [])
    fitbit_data = user_context.get("fitbit_data", {})
    
    context = "=== HISTORIAL DE EJERCICIOS ===\n\n"
    
    # Mostrar información básica del historial
    context += f"Total de ejercicios registrados: {len(exercise_history)}\n\n"
    
    # Mostrar cada registro de ejercicio sin filtrar
    for i, session in enumerate(exercise_history):
        ejercicio = session.get('ejercicio', 'Desconocido')
        fecha = session.get('fecha', 'Fecha desconocida')
        
        # Extraer la fecha en formato legible
        if isinstance(fecha, str) and 'T' in fecha:
            fecha = fecha.split('T')[0]
        
        context += f"Ejercicio {i+1}: {ejercicio} - Fecha: {fecha}\n"
        
        # Añadir detalles disponibles sin procesamiento
        for key, value in session.items():
            if key not in ['ejercicio', 'fecha']:
                context += f"  {key}: {value}\n"
        
        context += "\n"
    
    # Incluir datos de Fitbit si están disponibles
    if fitbit_data.get("available", False):
        context += "=== DATOS DE FITBIT ===\n\n"
        
        # Añadir datos de perfil disponibles
        if 'profile' in fitbit_data:
            context += "PERFIL:\n"
            user_data = fitbit_data['profile'].get('user', {})
            for key, value in user_data.items():
                context += f"  {key}: {value}\n"
        
        # Añadir datos de actividad
        if 'activity_summary' in fitbit_data:
            context += "\nACTIVIDAD:\n"
            summary = fitbit_data['activity_summary'].get('summary', {})
            for key, value in summary.items():
                context += f"  {key}: {value}\n"
    
    # Instrucciones MUY CLARAS para el LLM
    context += "\n=== INSTRUCCIONES PARA ANÁLISIS ===\n"
    context += "1. ANALIZA los datos disponibles para evaluar el progreso del usuario\n"
    context += "2. IMPORTANTE: NUNCA pidas más información al usuario - usa lo que tienes disponible\n"
    context += "3. Si la consulta menciona un ejercicio específico (ej. press banca), enfócate en esos registros\n"
    context += "4. Proporciona un análisis completo basado en los datos disponibles, aunque sean limitados\n"
    context += "5. Evalúa tendencias en repeticiones, frecuencia y consistencia\n"
    context += "6. Proporciona recomendaciones específicas para mejorar\n"
    context += "7. IMPORTANTE: Debes proporcionar un análisis completo y no solicitar más datos al usuario\n"
    
    return context