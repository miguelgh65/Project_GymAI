# fitness_chatbot/nodes/progress_node.py
import logging
from typing import Tuple, Dict, Any, List, Optional
import json
from datetime import datetime, timedelta

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.services import FitnessDataService

# Servicios adicionales que podríamos necesitar para obtener datos
# Estos se usarían solo para obtener datos, el análisis lo hace la IA
from fitness_chatbot.utils.api_utils import get_exercise_data, get_progress_data

logger = logging.getLogger("fitness_chatbot")

# Make sure this function name matches exactly what's being imported
async def process_progress_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas relacionadas con progreso y analiza la evolución del usuario.
    Utiliza IA para realizar todo el análisis, sin lógica programática.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de progreso: '{query}' para usuario {user_id}")
    
    try:
        # 1. Recolectar datos relevantes para el análisis
        
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Crear un contexto completo con todos los datos disponibles
        progress_context = {}
        
        # 1a. Obtener datos de ejercicios del usuario (90 días para ver tendencia)
        try:
            exercise_data = await FitnessDataService.get_user_exercises(user_id, limit=100)
            if exercise_data:
                progress_context["exercise_history"] = exercise_data
                logger.info(f"Obtenidos {len(exercise_data)} registros de ejercicios")
        except Exception as e:
            logger.warning(f"Error obteniendo datos de ejercicios: {str(e)}")
        
        # 1b. Intentar detectar ejercicio específico en la consulta
        # No usamos regex ni patrones programáticos, enviamos toda la consulta a la IA
        specific_exercise = None
        
        # 1c. Si hay un ejercicio específico, obtener su historial detallado
        if specific_exercise:
            try:
                specific_history = await FitnessDataService.get_user_progress(user_id, specific_exercise)
                if specific_history:
                    progress_context["specific_exercise"] = specific_exercise
                    progress_context["specific_history"] = specific_history
                    logger.info(f"Obtenidos {len(specific_history)} registros para {specific_exercise}")
            except Exception as e:
                logger.warning(f"Error obteniendo datos específicos: {str(e)}")
        
        # 1d. Intentar obtener datos de Fitbit si están disponibles
        try:
            # Esto simula obtener datos de Fitbit - en un sistema real obtendríamos datos reales
            # Nota: No estamos usando patrones para detectar si necesitamos datos de Fitbit
            # La IA decidirá si usar estos datos basándose en la consulta
            fitbit_data = {"available": False}  # Placeholder
            
            # Si hay un servicio real de Fitbit conectado, lo usaríamos aquí
            # fitbit_data = get_fitbit_data(user_id, auth_token)
            
            if fitbit_data and fitbit_data.get("available"):
                progress_context["fitbit_data"] = fitbit_data
                logger.info("Datos de Fitbit obtenidos e incluidos en el contexto")
        except Exception as e:
            logger.warning(f"Error obteniendo datos de Fitbit: {str(e)}")
        
        # 2. Preparar el contexto para la IA
        # Convertir el contexto a formato texto para el prompt
        context_text = format_progress_context(progress_context)
        
        # 3. Obtener prompts para el análisis de progreso
        messages = PromptManager.get_prompt_messages(
            "progress", 
            query=query,
            user_context=context_text
        )
        
        # 4. Invocar el LLM para realizar el análisis
        llm = get_llm()
        
        if not llm:
            logger.error("LLM no disponible para análisis de progreso")
            respuesta = "Lo siento, no puedo analizar tu progreso en este momento debido a problemas técnicos. Por favor, intenta más tarde."
        else:
            # Configurar para análisis detallado
            if hasattr(llm, 'with_temperature'):
                llm = llm.with_temperature(0.3)  # Menor temperatura para respuestas más consistentes
                
            if hasattr(llm, 'with_max_tokens'):
                llm = llm.with_max_tokens(2048)  # Tokens suficientes para análisis detallado
            
            # Invocar LLM para el análisis
            logger.info("Generando análisis de progreso mediante IA")
            response = await llm.ainvoke(messages)
            respuesta = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"Análisis de progreso generado: {len(respuesta)} caracteres")
    
    except Exception as e:
        logger.exception(f"Error analizando progreso: {str(e)}")
        respuesta = "Lo siento, tuve un problema al analizar tu progreso. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO ---")
    return agent_state, memory_state

def format_progress_context(context_data: Dict[str, Any]) -> str:
    """
    Formatea el contexto para el prompt de progreso.
    Todo el análisis lo realizará la IA, aquí solo convertimos los datos a texto.
    
    Args:
        context_data: Datos de contexto (ejercicios, fitbit, etc.)
        
    Returns:
        Texto formateado para el prompt
    """
    formatted_text = []
    
    # Añadir datos de ejercicios si están disponibles
    if "exercise_history" in context_data and context_data["exercise_history"]:
        formatted_text.append("=== HISTORIAL DE EJERCICIOS ===\n")
        
        # Agrupar por ejercicio
        exercise_groups = {}
        for entry in context_data["exercise_history"]:
            ejercicio = entry.get('ejercicio', 'desconocido')
            if ejercicio not in exercise_groups:
                exercise_groups[ejercicio] = []
            exercise_groups[ejercicio].append(entry)
        
        # Formatear cada grupo
        for ejercicio, entries in exercise_groups.items():
            formatted_text.append(f"Ejercicio: {ejercicio}")
            formatted_text.append(f"Sesiones registradas: {len(entries)}")
            
            # Mostrar algunas sesiones como ejemplo
            samples = sorted(entries, key=lambda x: x.get('fecha', ''), reverse=True)[:5]
            for i, session in enumerate(samples, 1):
                fecha = session.get('fecha', 'fecha desconocida')
                repeticiones = session.get('repeticiones', [])
                
                # Formatear en texto simple
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
            
            formatted_text.append("")  # Línea en blanco entre ejercicios
    
    # Añadir datos específicos de un ejercicio si están disponibles
    if "specific_exercise" in context_data and "specific_history" in context_data:
        ejercicio = context_data["specific_exercise"]
        history = context_data["specific_history"]
        
        formatted_text.append(f"=== ANÁLISIS DETALLADO: {ejercicio} ===\n")
        formatted_text.append(f"Total de sesiones registradas: {len(history)}")
        
        # Ordenar por fecha
        history_sorted = sorted(history, key=lambda x: x.get('fecha', ''))
        
        # Mostrar evolución
        if len(history_sorted) >= 2:
            primera_sesion = history_sorted[0]
            ultima_sesion = history_sorted[-1]
            
            # Fechas
            fecha_primera = primera_sesion.get('fecha', 'desconocida')
            fecha_ultima = ultima_sesion.get('fecha', 'desconocida')
            
            formatted_text.append(f"Primera sesión registrada: {fecha_primera}")
            formatted_text.append(f"Última sesión registrada: {fecha_ultima}")
            
            # Mostrar todas las sesiones para análisis detallado
            formatted_text.append("\nHistorial completo:")
            for i, session in enumerate(history_sorted, 1):
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
    
    # Añadir datos de Fitbit si están disponibles
    if "fitbit_data" in context_data and context_data["fitbit_data"].get("available"):
        fitbit_data = context_data["fitbit_data"]
        formatted_text.append("=== DATOS DE FITBIT ===\n")
        
        # Formatear datos de Fitbit según su estructura
        # Esto dependerá de los datos disponibles realmente
        formatted_text.append("Datos de actividad física disponibles de Fitbit.")
    
    # Si no hay datos
    if not formatted_text:
        return "No hay datos suficientes para analizar el progreso."
    
    return "\n".join(formatted_text)

# Add this to explicitly export the function
__all__ = ['process_progress_query']