# fitness_chatbot/nodes/exercise_node.py
import logging
from typing import Tuple, Dict, Any, Optional
import json

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

# Importar servicios de base de datos si están disponibles
try:
    from back_end.gym.services.database import get_exercise_logs
    DB_SERVICES_AVAILABLE = True
    logger = logging.getLogger("fitness_chatbot")
    logger.info("✅ Servicios de DB para consulta de ejercicios disponibles")
except ImportError:
    # Definir stub para get_exercise_logs
    def get_exercise_logs(user_id, days=7):
        logger.warning(f"Usando stub para get_exercise_logs: user_id={user_id}, days={days}")
        return []
    
    DB_SERVICES_AVAILABLE = False
    logger = logging.getLogger("fitness_chatbot")
    logger.warning("⚠️ Servicios de DB para consulta de ejercicios NO disponibles, usando stubs")

async def process_exercise_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas relacionadas con ejercicios.
    
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
    
    # Inicializar contexto de usuario si no existe
    if "user_context" not in agent_state:
        agent_state["user_context"] = {}
    
    # Extraer nombre de ejercicio (si existe)
    exercise_name = extract_exercise_name(query)
    logger.info(f"Nombre de ejercicio extraído: {exercise_name}")
    
    # Obtener datos históricos de ejercicios
    try:
        if DB_SERVICES_AVAILABLE:
            # Obtener datos recientes
            recent_exercises = get_exercise_logs(user_id, days=30)
            
            # Procesar los datos para tener un formato más amigable
            processed_exercises = []
            for exercise in recent_exercises:
                try:
                    # Convertir 'repeticiones' de JSON a objeto si es necesario
                    repetitions = exercise.get('repeticiones')
                    if repetitions and isinstance(repetitions, str):
                        try:
                            repetitions = json.loads(repetitions)
                        except json.JSONDecodeError:
                            repetitions = []
                    
                    # Añadir ejercicio procesado
                    processed_exercises.append({
                        "fecha": exercise.get('fecha'),
                        "ejercicio": exercise.get('ejercicio'),
                        "repeticiones": repetitions
                    })
                except Exception as e:
                    logger.error(f"Error procesando ejercicio: {e}")
            
            # Filtrar por ejercicio específico si se mencionó uno
            if exercise_name:
                filtered_exercises = [ex for ex in processed_exercises 
                                     if ex.get('ejercicio') and exercise_name.lower() in ex.get('ejercicio').lower()]
                
                if filtered_exercises:
                    agent_state["user_context"]["exercise_history"] = filtered_exercises
                    logger.info(f"Obtenidos {len(filtered_exercises)} registros históricos para {exercise_name}")
            
            # Almacenar todos los ejercicios recientes
            agent_state["user_context"]["recent_exercises"] = processed_exercises
            logger.info(f"Obtenidos {len(processed_exercises)} ejercicios recientes")
            
        else:
            # Usar datos simulados para testing
            logger.warning("Usando datos simulados para testing")
            agent_state["user_context"]["recent_exercises"] = [
                {
                    "fecha": "2024-04-25",
                    "ejercicio": "press banca",
                    "repeticiones": [
                        {"repeticiones": 10, "peso": 60},
                        {"repeticiones": 8, "peso": 70},
                        {"repeticiones": 6, "peso": 75}
                    ]
                },
                {
                    "fecha": "2024-04-23",
                    "ejercicio": "sentadillas",
                    "repeticiones": [
                        {"repeticiones": 10, "peso": 100},
                        {"repeticiones": 10, "peso": 100},
                        {"repeticiones": 8, "peso": 110}
                    ]
                }
            ]
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos: {e}")
        # Crear contexto básico en caso de error
        agent_state["user_context"]["recent_exercises"] = []
        agent_state["user_context"]["error"] = str(e)
    
    # Formatear el contexto para el LLM
    context = format_exercise_context(agent_state["user_context"])
    
    # Obtener mensajes de prompt para ejercicios
    messages = PromptManager.get_prompt_messages("exercise", query=query, user_context=context)
    
    # Obtener LLM
    llm = get_llm()
    
    # Invocar LLM
    try:
        response = await llm.ainvoke(messages)
        generation = response.content.strip()
        
        # Actualizar estado
        agent_state["generation"] = generation
        
        # Actualizar historial de mensajes
        memory_state["messages"].append({"role": "assistant", "content": generation})
        
        logger.info(f"Generada respuesta de {len(generation)} caracteres")
        
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        agent_state["generation"] = "Lo siento, hubo un error procesando tu consulta sobre ejercicios."
        memory_state["messages"].append({"role": "assistant", "content": agent_state["generation"]})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE EJERCICIO FINALIZADO ---")
    
    return agent_state, memory_state

def extract_exercise_name(query: str) -> Optional[str]:
    """Extrae el nombre del ejercicio de la consulta."""
    # Lista de ejercicios comunes para detectar
    common_exercises = [
        "press banca", "sentadilla", "peso muerto", "dominadas", 
        "press militar", "curl biceps", "fondos", "elevaciones laterales",
        "remo", "extensiones", "triceps"
    ]
    
    query_lower = query.lower()
    for exercise in common_exercises:
        if exercise in query_lower:
            return exercise
    
    return None

def format_exercise_context(user_context: Dict[str, Any]) -> str:
    """Formatea el contexto de ejercicio para el LLM."""
    context = []
    
    # Añadir información sobre ejercicio específico
    if "exercise_history" in user_context and user_context["exercise_history"]:
        history = user_context["exercise_history"]
        exercise_name = history[0].get("ejercicio", "desconocido") if history else "desconocido"
        
        context.append(f"Ejercicio consultado: {exercise_name}")
        context.append(f"\nHistorial del ejercicio (últimas {len(history)} sesiones):")
        
        for i, session in enumerate(history, 1):
            fecha = session.get("fecha", "fecha desconocida")
            repeticiones = session.get("repeticiones", "N/A")
            context.append(f"  {i}. Fecha: {fecha}")
            
            # Formatear repeticiones si es un objeto JSON
            if isinstance(repeticiones, dict) or isinstance(repeticiones, list):
                context.append("     Series:")
                for j, serie in enumerate(repeticiones if isinstance(repeticiones, list) else [repeticiones], 1):
                    reps = serie.get("repeticiones", "?")
                    peso = serie.get("peso", "?")
                    context.append(f"       - Serie {j}: {reps} repeticiones x {peso}kg")
    
    # Añadir ejercicios recientes
    if "recent_exercises" in user_context and user_context["recent_exercises"]:
        exercises = user_context["recent_exercises"]
        context.append("\nEjercicios recientes:")
        for i, ex in enumerate(exercises, 1):
            fecha = ex.get("fecha", "fecha desconocida")
            nombre = ex.get("ejercicio", "ejercicio desconocido")
            context.append(f"  {i}. {nombre} (Fecha: {fecha})")
    
    # Si no hay datos
    if not context:
        context.append("No hay datos disponibles sobre ejercicios para este usuario.")
    
    # Añadir mensaje de error si existe
    if "error" in user_context and user_context["error"]:
        context.append(f"\nERROR: {user_context['error']}")
    
    return "\n".join(context)