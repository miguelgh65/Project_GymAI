# fitness_chatbot/nodes/exercise_node.py
import logging
import json
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.api_utils import get_exercise_data
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

async def process_exercise_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas sobre ejercicios.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE EJERCICIO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de ejercicio: '{query}' para usuario {user_id}")
    
    # Detectar si es consulta sobre ejercicio específico
    ejercicio = detect_specific_exercise(query)
    if ejercicio:
        logger.info(f"Ejercicio específico detectado: {ejercicio}")
    
    try:
        # Detectar tipo de consulta
        if is_listing_query(query):
            # Consulta por listado de ejercicios
            logger.info("Detectada consulta por listado de ejercicios")
            
            # Obtener el token de autenticación del contexto del usuario
            auth_token = agent_state.get("user_context", {}).get("auth_token")
            logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
            
            # MEJORA: Reintentar con URL alternativa o usar acceso directo a BD
            try:
                if ejercicio:
                    # Consulta por ejercicio específico
                    logger.info(f"Obteniendo datos para ejercicio específico: {ejercicio}")
                    exercise_data = get_exercise_data(user_id, ejercicio, auth_token=auth_token)
                    respuesta = format_specific_exercise_response(exercise_data, ejercicio)
                else:
                    # Consulta general por todos los ejercicios
                    logger.info("Obteniendo listado general de ejercicios")
                    exercise_data = get_exercise_data(user_id, auth_token=auth_token)
                    respuesta = format_exercise_list_response(exercise_data)
            except Exception as api_error:
                logger.error(f"Error en solicitud API: {str(api_error)}")
                # Respuesta de fallback si la API falla
                respuesta = "Lo siento, no pude obtener tus ejercicios en este momento. El servicio parece estar ocupado. Por favor, intenta de nuevo más tarde."
        else:
            # Consulta sobre información general de ejercicios
            logger.info("Consulta sobre información general de ejercicios")
            
            # Preparar contexto para el LLM
            if ejercicio:
                # Información sobre un ejercicio específico
                user_context = f"Ejercicio consultado: {ejercicio}"
                logger.info(f"Preparando prompt para ejercicio específico: {ejercicio}")
            else:
                # Información general
                user_context = "Consulta general sobre ejercicios y entrenamiento"
            
            # Usar PromptManager para obtener prompts del sistema
            messages = PromptManager.get_prompt_messages(
                "exercise", 
                query=query,
                user_context=user_context
            )
            
            # Invocar el LLM
            llm = get_llm()
            if llm is None:
                logger.error("LLM no inicializado correctamente")
                respuesta = "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta más tarde."
            else:
                response = await llm.ainvoke(messages)
                respuesta = response.content if hasattr(response, 'content') else str(response)
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de ejercicio: {str(e)}")
        respuesta = "Lo siento, tuve un problema al procesar tu consulta sobre ejercicios. ¿Podrías intentar reformularla?"
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE EJERCICIO FINALIZADO ---")
    return agent_state, memory_state

def detect_specific_exercise(query: str) -> Optional[str]:
    """
    Detecta si la consulta menciona un ejercicio específico.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Nombre del ejercicio mencionado o None
    """
    query_lower = query.lower()
    
    # Mapeo de ejercicios comunes
    exercise_mapping = {
        "press banca": ["press banca", "press de banca", "bench press", "banca"],
        "sentadillas": ["sentadilla", "sentadillas", "squat", "squats"],
        "peso muerto": ["peso muerto", "deadlift"],
        "dominadas": ["dominada", "dominadas", "pull up", "pull-up", "chin up"],
        "curl de bíceps": ["curl", "bíceps", "biceps", "curl de biceps", "curl biceps"],
        "press militar": ["press militar", "military press", "press hombro", "press de hombro"],
        "fondos": ["fondos", "dips", "fondos de tríceps", "triceps dips"],
        "remo": ["remo", "row", "remo con barra"]
    }
    
    # Buscar coincidencias
    for standard_name, variations in exercise_mapping.items():
        for variation in variations:
            if variation in query_lower:
                return standard_name
    
    return None

def is_listing_query(query: str) -> bool:
    """
    Determina si la consulta es sobre listar ejercicios.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        True si es una consulta de listado, False en caso contrario
    """
    query_lower = query.lower()
    
    # Palabras clave que indican solicitud de listado
    listing_keywords = [
        "dame", "muestra", "ver", "mostrar", "listar", "últimos", "ultimos",
        "recientes", "histórico", "historia", "historial", "ejercicios",
        "qué he hecho", "que he hecho", "cuáles son", "cuales son",
        "qué ejercicios", "que ejercicios"
    ]
    
    return any(keyword in query_lower for keyword in listing_keywords)

def format_specific_exercise_response(data: Dict[str, Any], ejercicio: str) -> str:
    """
    Formatea la respuesta para un ejercicio específico.
    
    Args:
        data: Datos obtenidos de la API
        ejercicio: Nombre del ejercicio
        
    Returns:
        Texto formateado con la respuesta
    """
    try:
        if not data.get("success", False):
            logger.warning(f"API devolvió error para ejercicio {ejercicio}: {data.get('detail', 'Error desconocido')}")
            return f"Lo siento, no pude obtener información sobre tu historial de {ejercicio}. ¿Te gustaría información general sobre este ejercicio?"
        
        # Verificar si hay datos
        datos = data.get("datos", [])
        if not datos:
            return f"No encontré registros recientes de **{ejercicio}** en tu historial. ¿Quieres que te ayude a registrar este ejercicio?"
        
        # Obtener el ejercicio más reciente
        ultimo_ejercicio = datos[0]  # Asumimos que vienen ordenados por fecha
        fecha = ultimo_ejercicio.get("fecha", "")
        if isinstance(fecha, str) and len(fecha) > 10:
            fecha = fecha[:10]  # Tomar solo la parte de la fecha
        
        # Construir respuesta detallada
        respuesta = f"## Tu último ejercicio de {ejercicio}\n\n"
        respuesta += f"**Fecha:** {fecha}\n\n"
        
        # Detalles del ejercicio
        max_peso = ultimo_ejercicio.get("max_peso", 0)
        total_reps = ultimo_ejercicio.get("total_reps", 0)
        volumen = ultimo_ejercicio.get("volumen", 0)
        
        respuesta += f"• **Peso máximo:** {max_peso}kg\n"
        respuesta += f"• **Repeticiones totales:** {total_reps}\n"
        respuesta += f"• **Volumen total:** {volumen}kg\n\n"
        
        # Si hay información de progreso
        resumen = data.get("resumen", {})
        if resumen and "progress_percent" in resumen:
            progress = resumen.get("progress_percent", 0)
            if progress > 0:
                respuesta += f"📈 Has progresado un **{progress}%** desde tu primera sesión registrada.\n\n"
            elif progress < 0:
                respuesta += f"📉 Has retrocedido un **{abs(progress)}%** desde tu primera sesión registrada.\n\n"
            else:
                respuesta += "Tu rendimiento se ha mantenido estable.\n\n"
        
        # Si hay múltiples sesiones, mostrar tendencia
        if len(datos) > 1:
            respuesta += "### Historial reciente\n\n"
            # Mostrar solo las últimas 3 sesiones como máximo
            for i, sesion in enumerate(datos[:3]):
                fecha_sesion = sesion.get("fecha", "")[:10]
                max_peso_sesion = sesion.get("max_peso", 0)
                total_reps_sesion = sesion.get("total_reps", 0)
                
                respuesta += f"**Sesión {i+1}** ({fecha_sesion}): {max_peso_sesion}kg x {total_reps_sesion} reps\n"
        
        respuesta += "\n¿Quieres registrar una nueva sesión de este ejercicio?"
        return respuesta
    
    except Exception as e:
        logger.exception(f"Error formateando respuesta para ejercicio específico: {str(e)}")
        return f"Encontré información sobre tu {ejercicio}, pero tuve problemas al analizarla. ¿Quieres información general sobre este ejercicio?"

def format_exercise_list_response(data: Dict[str, Any]) -> str:
    """
    Formatea la respuesta con un listado de ejercicios.
    
    Args:
        data: Datos obtenidos de la API
        
    Returns:
        Texto formateado con la respuesta
    """
    try:
        if not data.get("success", False):
            logger.warning(f"API devolvió error para listado: {data.get('detail', 'Error desconocido')}")
            return "Lo siento, tuve problemas al obtener tu historial de ejercicios. ¿Puedo ayudarte con algo más?"
        
        # Verificar si hay datos
        logs = data.get("logs", [])
        if not logs:
            return "No encontré registros de ejercicios en tu historial reciente. ¿Quieres registrar algún ejercicio nuevo?"
        
        # Agrupar ejercicios por fecha
        logs_by_date = {}
        for log in logs:
            fecha = log.get("fecha", "")
            if isinstance(fecha, str) and len(fecha) > 10:
                fecha = fecha[:10]  # Tomar solo la parte de la fecha
            
            if fecha not in logs_by_date:
                logs_by_date[fecha] = []
            
            logs_by_date[fecha].append(log)
        
        # Construir respuesta
        respuesta = "## Tus ejercicios recientes\n\n"
        
        # Ordenar fechas de más reciente a más antigua
        fechas_ordenadas = sorted(logs_by_date.keys(), reverse=True)
        
        # Mostrar ejercicios agrupados por fecha (limitados a los últimos 5 días)
        for fecha in fechas_ordenadas[:5]:
            respuesta += f"### {fecha}\n"
            
            ejercicios = logs_by_date[fecha]
            for ejercicio in ejercicios:
                nombre = ejercicio.get("ejercicio", "ejercicio desconocido")
                # Intentar obtener detalles adicionales si están disponibles
                detalles = ""
                if "repeticiones" in ejercicio and ejercicio["repeticiones"]:
                    # Intentar formatear repeticiones si están disponibles
                    try:
                        if isinstance(ejercicio["repeticiones"], str):
                            # Intentar parsear JSON si es string
                            reps = json.loads(ejercicio["repeticiones"])
                        else:
                            reps = ejercicio["repeticiones"]
                        
                        if isinstance(reps, list) and len(reps) > 0:
                            num_series = len(reps)
                            detalles = f" ({num_series} series)"
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                respuesta += f"• **{nombre}**{detalles}\n"
            
            respuesta += "\n"
        
        respuesta += "¿Quieres ver más detalles sobre algún ejercicio específico o registrar uno nuevo?"
        return respuesta
    
    except Exception as e:
        logger.exception(f"Error formateando listado de ejercicios: {str(e)}")
        return "Encontré tus registros de ejercicios, pero tuve problemas al mostrarlos. ¿Puedo ayudarte con algo más?"