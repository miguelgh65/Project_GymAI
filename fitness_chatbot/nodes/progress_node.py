# fitness_chatbot/nodes/progress_node.py
import logging
from typing import Tuple, Dict, Any, Optional, List

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.utils.api_utils import get_progress_data, get_exercise_data
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.configs.llm_config import get_llm

logger = logging.getLogger("fitness_chatbot")

async def process_progress_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas de progreso consultando la API del backend y dejando que
    la IA analice los resultados.
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de progreso: '{query}' para usuario {user_id}")
    
    # Mejorar la detección de ejercicio con una lista más completa
    ejercicio = detect_exercise_from_query(query)
    if ejercicio:
        logger.info(f"Ejercicio '{ejercicio}' detectado en la consulta")
    
    try:
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Usar nuestra función de API en lugar de llamadas directas a requests
        if ejercicio:
            # Consulta por ejercicio específico
            logger.info(f"Obteniendo datos de progreso para ejercicio: {ejercicio}")
            data = get_progress_data(user_id, ejercicio, auth_token=auth_token)
        else:
            # Consulta general
            logger.info(f"Obteniendo datos generales de progreso")
            data = get_progress_data(user_id, auth_token=auth_token)
        
        # Verificar si obtuvimos datos correctamente
        if data.get("success", False):
            logger.info(f"Datos recibidos de la API: {list(data.keys()) if isinstance(data, dict) else 'no es un dict'}")
            
            # Preparar los datos para enviar a la IA
            user_context = prepare_data_for_llm(data, ejercicio)
            
            # Obtener la respuesta del LLM usando el sistema de prompts
            messages = PromptManager.get_prompt_messages(
                "progress", 
                query=query, 
                user_context=user_context
            )
            
            # Invocar el LLM
            llm = get_llm()
            response = await llm.ainvoke(messages)
            respuesta = response.content if hasattr(response, 'content') else str(response)
        else:
            # Error al obtener datos
            error_message = data.get("error", "Error desconocido")
            logger.error(f"Error al obtener datos de progreso: {error_message}")
            respuesta = f"Lo siento, no pude obtener información sobre tu progreso en este momento. Error: {error_message}"
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de progreso: {e}")
        respuesta = "Tuve un problema al consultar tu historial de progreso. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO ---")
    return agent_state, memory_state

def detect_exercise_from_query(query: str) -> Optional[str]:
    """
    Detecta el ejercicio mencionado en la consulta del usuario.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Nombre del ejercicio detectado o None
    """
    query_lower = query.lower()
    
    # Mapeo de palabras clave a nombres de ejercicios estandarizados
    exercise_mapping = {
        "press banca": ["press banca", "press de banca", "banca", "bench press"],
        "sentadillas": ["sentadilla", "sentadillas", "squat", "squats"],
        "peso muerto": ["peso muerto", "deadlift"],
        "dominadas": ["dominada", "dominadas", "pull up", "pull-up", "pullup"],
        "curl de bíceps": ["curl", "bíceps", "biceps", "curl de biceps"],
        "press militar": ["press militar", "military press", "press hombro"],
        "fondos": ["fondos", "dips", "fondos de tríceps"],
        "remo": ["remo", "row", "remo con barra"]
    }
    
    # Buscar coincidencias
    for exercise_name, keywords in exercise_mapping.items():
        for keyword in keywords:
            if keyword in query_lower:
                return exercise_name
    
    return None

def prepare_data_for_llm(data: Dict[str, Any], ejercicio: Optional[str] = None) -> str:
    """
    Prepara los datos recibidos de la API para enviarlos al LLM.
    
    Args:
        data: Datos recibidos de la API
        ejercicio: Nombre del ejercicio si se ha especificado
        
    Returns:
        Contexto formateado para el LLM
    """
    context_parts = []
    
    if ejercicio:
        context_parts.append(f"ANÁLISIS DE PROGRESO PARA: {ejercicio}")
    else:
        context_parts.append("ANÁLISIS DE ACTIVIDAD FÍSICA")
    
    context_parts.append("=== DATOS DE EJERCICIOS ===")
    
    # Verificar si hay datos disponibles
    ejercicios_disponibles = data.get("ejercicios_disponibles", [])
    datos = data.get("datos", [])
    
    if not datos and ejercicios_disponibles:
        context_parts.append("\nNo hay datos para el período consultado, pero el usuario tiene los siguientes ejercicios registrados:")
        for idx, ej in enumerate(ejercicios_disponibles, 1):
            context_parts.append(f"  {idx}. {ej}")
    
    elif not datos and not ejercicios_disponibles:
        context_parts.append("\nNo hay ejercicios registrados para este usuario.")
    
    else:
        # Si hay datos, formatearlos para el LLM
        if ejercicio:
            context_parts.append(f"\nHistorial de {ejercicio} (ordenado por fecha):")
        else:
            context_parts.append("\nHistorial de ejercicios recientes:")
        
        for idx, entry in enumerate(datos, 1):
            fecha = entry.get("fecha", "")
            if isinstance(fecha, str) and len(fecha) > 10:
                fecha = fecha[:10]
                
            context_parts.append(f"\n[Sesión {idx}] - Fecha: {fecha}")
            context_parts.append("  Series:")
            
            max_peso = entry.get("max_peso", 0)
            total_reps = entry.get("total_reps", 0)
            volumen = entry.get("volumen", 0)
            
            context_parts.append(f"  - Serie con peso máximo: {max_peso}kg")
            context_parts.append(f"  - Total repeticiones: {total_reps}")
            context_parts.append(f"  - Volumen total: {volumen}kg")
    
    # Añadir estadísticas adicionales si están disponibles
    resumen = data.get("resumen", {})
    if resumen:
        context_parts.append("\n=== ESTADÍSTICAS ADICIONALES ===")
        context_parts.append("\nResumen estadístico:")
        
        if "total_sesiones" in resumen:
            context_parts.append(f"- Total de sesiones: {resumen['total_sesiones']}")
        if "max_weight_ever" in resumen:
            context_parts.append(f"- Peso máximo histórico: {resumen['max_weight_ever']}kg")
        if "max_volume_session" in resumen:
            context_parts.append(f"- Volumen máximo en una sesión: {resumen['max_volume_session']}kg")
        if "progress_percent" in resumen:
            context_parts.append(f"- Porcentaje de progreso: {resumen['progress_percent']}%")
    
    # Añadir instrucciones para la IA
    context_parts.append("\n=== INSTRUCCIONES PARA ANÁLISIS ===")
    context_parts.append("1. Analiza los datos anteriores para determinar el progreso")
    context_parts.append("2. Busca tendencias en pesos, repeticiones y volumen a lo largo del tiempo")
    context_parts.append("3. Indica si el progreso es positivo, negativo o mixto")
    context_parts.append("4. Proporciona recomendaciones basadas en los datos")
    
    return "\n".join(context_parts)