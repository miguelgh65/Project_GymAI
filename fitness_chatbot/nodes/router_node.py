# fitness_chatbot/nodes/router_node.py
import logging
import json
import re
from typing import Tuple, Dict, Any, Optional

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.schemas.prompt_schemas import IntentClassification
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

async def classify_intent(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Clasifica la intención del usuario basándose en su consulta.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- CLASIFICACIÓN DE INTENCIÓN INICIADA ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener la consulta del usuario
    query = agent_state["query"]
    logger.info(f"Consulta a clasificar: '{query}'")
    
    # Comprobar si hay una intención ya definida (para llamadas directas a nodos específicos)
    if agent_state.get("intent"):
        logger.info(f"Intención ya definida: {agent_state['intent']}")
        
        # Actualizar historial de mensajes
        if "messages" not in memory_state:
            memory_state["messages"] = []
        
        memory_state["messages"].append({"role": "user", "content": query})
        
        return agent_state, memory_state
    
    # PASO 1: Utilizar el LLM para clasificar la intención
    try:
        # Obtener mensajes de prompt para el router
        messages = PromptManager.get_prompt_messages("router", query=query)
        
        # Configuración para el LLM
        temp_llm = get_llm()
        if temp_llm is None:
            logger.error("LLM no inicializado correctamente. Usando clasificación por reglas.")
            normalized_intent = classify_by_rules(query)
            logger.info(f"Clasificación por reglas (LLM no disponible): {normalized_intent}")
        else:
            if hasattr(temp_llm, 'with_temperature'):
                llm = temp_llm.with_temperature(0.2)
            else:
                llm = temp_llm
            
            # Intentar configurar el modelo para obtener salida estructurada
            try:
                structured_llm = llm.with_structured_output(IntentClassification)
                
                # Llamar al LLM para clasificar
                classification = await structured_llm.ainvoke(messages)
                
                # Extraer la intención
                intent = classification.intent.lower()
                
                # Log para debug
                logger.info(f"LLM clasificó la intención como: {intent}")
                
                # Normalizar la intención
                normalized_intent = normalize_intent(intent, query)
                
                logger.info(f"Intención normalizada final: {normalized_intent}")
            except Exception as e:
                logger.error(f"Error con salida estructurada: {e}")
                # Si falla la salida estructurada, usar llamada normal al LLM
                try:
                    response = await llm.ainvoke(messages)
                    content = response.content if hasattr(response, 'content') else str(response)
                    
                    # Extraer intención del texto
                    intent_match = re.search(r'intent["\']?\s*:\s*["\']?(\w+)["\']?', content)
                    if intent_match:
                        intent = intent_match.group(1).lower()
                        normalized_intent = normalize_intent(intent, query)
                        logger.info(f"Intención extraída del texto: {normalized_intent}")
                    else:
                        # Si no se puede extraer, usar clasificación por reglas
                        normalized_intent = classify_by_rules(query)
                        logger.info(f"No se encontró intención en respuesta LLM. Usando reglas: {normalized_intent}")
                except Exception as inner_e:
                    logger.error(f"Error en llamada normal al LLM: {inner_e}")
                    normalized_intent = classify_by_rules(query)
                    logger.info(f"Fallback a clasificación por reglas: {normalized_intent}")
    except Exception as e:
        logger.error(f"Error en la clasificación con LLM: {str(e)}")
        
        # Si falla el LLM, usar un clasificador de reglas como fallback
        normalized_intent = classify_by_rules(query)
        logger.info(f"Fallback a clasificación por reglas: {normalized_intent}")
    
    # En este caso simplificado, solo necesitamos clasificar entre GENERAL y LOG_ACTIVITY
    # Simplificamos la normalización a estos dos casos
    if normalized_intent == IntentType.LOG_ACTIVITY:
        final_intent = IntentType.LOG_ACTIVITY
    else:
        final_intent = IntentType.GENERAL
    
    logger.info(f"Intención simplificada final: {final_intent}")
    
    # Actualizar estado con la intención detectada
    agent_state["intent"] = final_intent
    
    # Actualizar historial de mensajes
    if "messages" not in memory_state:
        memory_state["messages"] = []
    
    memory_state["messages"].append({"role": "user", "content": query})
    
    logger.info(f"RESULTADO FINAL DE CLASIFICACIÓN: {final_intent}")
    logger.info("--- CLASIFICACIÓN DE INTENCIÓN FINALIZADA ---")
    
    return agent_state, memory_state

def normalize_intent(intent: str, query: str) -> str:
    """
    Normaliza la intención detectada y aplica lógica adicional basada en la consulta.
    
    Args:
        intent: Intención detectada por el LLM
        query: Consulta original del usuario
        
    Returns:
        Intención normalizada
    """
    query_lower = query.lower()
    
    # Palabras clave que indican registro de actividad
    log_keywords = [
        "registra", "apunta", "anota", "agrega", "añade", 
        "he hecho", "hice", "realicé", "terminé"
    ]
    
    # Si la intención es "general" pero la consulta parece ser un registro, cambiar a "log_activity"
    if (intent == "general" or intent == IntentType.GENERAL):
        if any(keyword in query_lower for keyword in log_keywords) and \
           any(exercise in query_lower for exercise in ["press", "banca", "sentadilla", "curl", "dominada"]):
            logger.info("Reclasificando de 'general' a 'log_activity' basado en palabras clave de registro")
            return IntentType.LOG_ACTIVITY
    
    # Normalizar el formato de la intención
    if any(kw in intent for kw in ["registrar", "anotar", "log", "guardar"]) or intent == "log_activity":
        return IntentType.LOG_ACTIVITY
    else:
        return IntentType.GENERAL

def classify_by_rules(query: str) -> str:
    """
    Clasificador de reglas básico como fallback en caso de que falle el LLM.
    Versión simplificada que solo clasifica entre LOG_ACTIVITY y GENERAL.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Intención clasificada
    """
    query_lower = query.lower()
    
    # --- 1. DETECTAR REGISTRO DE EJERCICIO ---
    registration_keywords = [
        'registra', 'apunta', 'anota', 'guarda', 'agrega', 'añade', 
        'he hecho', 'hice', 'realicé', 'terminé'
    ]
    exercise_keywords = [
        'press banca', 'press de banca', 'banca', 'sentadilla', 'sentadillas', 
        'peso muerto', 'dominada', 'dominadas', 'curl', 'bíceps', 'fondos', 
        'press militar', 'elevaciones', 'remo', 'extensiones', 'tríceps'
    ]
    
    # Patrones numéricos típicos de ejercicios
    exercise_patterns = [
        r'\d+\s*[xX]\s*\d+',        # 10x20, 3x10
        r'\d+\s*series',            # 3 series
        r'\d+\s*repeticiones',      # 10 repeticiones
        r'\d+\s*reps',              # 10 reps
        r'\d+\s*kg',                # 60 kg
    ]
    
    # Detectar registro de ejercicio
    has_registration_keyword = any(keyword in query_lower for keyword in registration_keywords)
    has_exercise_keyword = any(keyword in query_lower for keyword in exercise_keywords)
    has_exercise_pattern = any(re.search(pattern, query_lower) for pattern in exercise_patterns)
    
    if (has_registration_keyword and has_exercise_keyword) or (has_exercise_keyword and has_exercise_pattern):
        return IntentType.LOG_ACTIVITY
    
    # Si no se puede clasificar, devolver general
    return IntentType.GENERAL

# Función auxiliar para procesar mensajes directamente (API)
async def process_message(user_id: str, message: str, auth_token: Optional[str] = None) -> Any:
    """
    Procesa un mensaje del usuario y devuelve una respuesta usando el grafo de fitness.
    Función auxiliar para compatibilidad con APIs.
    
    Args:
        user_id: ID del usuario (debe ser Google ID)
        message: Mensaje del usuario
        auth_token: Token JWT para autenticación con el backend
        
    Returns:
        Objeto con la respuesta del chatbot
    """
    # Importar el grafo aquí para evitar importaciones circulares
    from fitness_chatbot.graphs.fitness_graph import create_fitness_graph
    
    try:
        # Log para depuración
        logger.info(f"Procesando mensaje con ID de usuario: {user_id}")
        logger.info(f"Mensaje recibido: '{message}'")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Crear estado inicial - user_id ya debería ser el Google ID
        agent_state = AgentState(
            query=message,
            intent="",
            user_id=user_id,  
            user_context={
                "auth_token": auth_token  # Guardar el token en el contexto para usarlo en las llamadas a la API
            },
            intermediate_steps=[],
            retrieved_data=[],
            generation=""
        )
        
        memory_state = MemoryState(
            messages=[]
        )
        
        # Obtener el grafo de fitness
        fitness_graph = create_fitness_graph()
        
        if fitness_graph is None:
            logger.error("Error: fitness_graph es None. No se pudo crear el grafo.")
            class MessageResponse:
                def __init__(self, content):
                    self.content = content
            return MessageResponse("Lo siento, ocurrió un error interno al procesar tu mensaje. Por favor, intenta de nuevo más tarde.")
        
        # Invocar el grafo
        final_state = await fitness_graph.ainvoke((agent_state, memory_state))
        final_agent_state, final_memory_state = final_state
        
        # Obtener respuesta generada
        response = final_agent_state.get("generation", "")
        logger.info(f"Respuesta generada: '{response[:50]}...'")
        
        # Crear objeto de respuesta similar a MessageResponse
        class MessageResponse:
            def __init__(self, content):
                self.content = content
        
        return MessageResponse(response)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
        # Crear una clase de respuesta para devolver el error
        class MessageResponse:
            def __init__(self, content):
                self.content = content
        
        return MessageResponse(f"Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo más tarde.")