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
    
    # PASO 1: Reglas de pre-clasificación para casos específicos
    query_lower = query.lower()
    
    # Detección directa para consultas sobre últimos ejercicios
    if (("último" in query_lower or "ultimo" in query_lower or "dame" in query_lower) and 
        ("ejercicio" in query_lower or any(ex in query_lower for ex in ["press", "banca", "sentadilla", "peso muerto"]))):
        logger.info("Clasificación directa: EXERCISE (consulta sobre último ejercicio)")
        normalized_intent = IntentType.EXERCISE
    # Detección directa para registro de ejercicios
    elif any(pattern in query_lower for pattern in ["registra", "anota", "apunta", "agrega", "he hecho"]) and \
         any(ex in query_lower for ex in ["press", "banca", "sentadilla", "peso muerto", "curl", "dominada"]):
        logger.info("Clasificación directa: LOG_ACTIVITY (registro de ejercicio)")
        normalized_intent = IntentType.LOG_ACTIVITY
    else:
        # PASO 2: Utilizar el LLM para clasificar la intención
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
    
    # Actualizar estado con la intención detectada
    agent_state["intent"] = normalized_intent
    
    # Actualizar historial de mensajes
    if "messages" not in memory_state:
        memory_state["messages"] = []
    
    memory_state["messages"].append({"role": "user", "content": query})
    
    logger.info(f"RESULTADO FINAL DE CLASIFICACIÓN: {normalized_intent}")
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
    
    # Palabras clave que indican solicitudes de listado general de ejercicios
    exercise_list_keywords = [
        "dame", "muestra", "listado", "lista", "ultimos", "últimos",
        "recientes", "historial", "ejercicios", "que he hecho"
    ]
    
    # Palabras clave que indican registro de actividad
    log_keywords = [
        "registra", "apunta", "anota", "agrega", "añade", 
        "he hecho", "hice", "realicé", "terminé"
    ]
    
    # Si la intención es "progress" pero la consulta parece ser una solicitud de 
    # listado de ejercicios, cambiar a "exercise"
    if intent == "progress" or intent == IntentType.PROGRESS:
        keyword_count = sum(1 for keyword in exercise_list_keywords if keyword in query_lower)
        
        if keyword_count >= 1 and ("ejercicio" in query_lower or "entrenamiento" in query_lower):
            logger.info(f"Reclasificando de 'progress' a 'exercise' basado en palabras clave: {keyword_count} coincidencias")
            return IntentType.EXERCISE
    
    # Si la intención es "general" pero la consulta parece ser un registro, cambiar a "log_activity"
    if (intent == "general" or intent == IntentType.GENERAL):
        if any(keyword in query_lower for keyword in log_keywords) and \
           any(exercise in query_lower for exercise in ["press", "banca", "sentadilla", "curl", "dominada"]):
            logger.info("Reclasificando de 'general' a 'log_activity' basado en palabras clave de registro")
            return IntentType.LOG_ACTIVITY
    
    # Normalizar el formato de la intención
    if "ejercicio" in intent or "entrenamiento" in intent or intent == "exercise":
        return IntentType.EXERCISE
    elif "nutri" in intent or "comida" in intent or "dieta" in intent or intent == "nutrition":
        return IntentType.NUTRITION
    elif "progreso" in intent or "estadística" in intent or "evolución" in intent or intent == "progress":
        return IntentType.PROGRESS
    elif any(kw in intent for kw in ["registrar", "anotar", "log", "guardar"]) or intent == "log_activity":
        return IntentType.LOG_ACTIVITY
    else:
        return IntentType.GENERAL

def classify_by_rules(query: str) -> str:
    """
    Clasificador de reglas básico como fallback en caso de que falle el LLM.
    
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
        'press militar', 'elevaciones', 'remo', 'extensiones', 'tríceps', 
        'jalón', 'abdominales', 'flexiones', 'pushups', 'series', 'repeticiones'
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
    
    # --- 2. DETECTAR CONSULTA DE LISTADO DE EJERCICIOS ---
    listing_keywords = [
        'dame', 'muestra', 'ver', 'mostrar', 'listar', 'últimos', 'ultimos', 
        'recientes', 'historia', 'historial', 'ejercicios', 'qué he hecho', 'que he hecho'
    ]
    
    has_listing_keyword = any(keyword in query_lower for keyword in listing_keywords)
    
    if has_listing_keyword and (has_exercise_keyword or "ejercicio" in query_lower):
        return IntentType.EXERCISE
    
    # --- 3. DETECTAR CONSULTA DE PROGRESO ---
    progress_keywords = [
        'progreso', 'avance', 'mejora', 'evolución', 'estadística', 'cómo voy', 
        'he mejorado', 'comparar', 'gráfica', 'tendencia', 'comparado con'
    ]
    
    has_progress_keyword = any(keyword in query_lower for keyword in progress_keywords)
    
    if has_progress_keyword:
        return IntentType.PROGRESS
    
    # --- 4. DETECTAR CONSULTA DE NUTRICIÓN ---
    nutrition_keywords = [
        'comida', 'dieta', 'nutrición', 'comer', 'proteína', 'carbohidratos', 
        'calorías', 'macros', 'plan alimenticio', 'suplemento', 'alimentación'
    ]
    
    has_nutrition_keyword = any(keyword in query_lower for keyword in nutrition_keywords)
    
    if has_nutrition_keyword:
        return IntentType.NUTRITION
    
    # --- 5. PREGUNTAS SOBRE EJERCICIOS (no registro) ---
    if has_exercise_keyword:
        return IntentType.EXERCISE
    
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
        logger.info(f"Token de autenticación recibido: {'Sí' if auth_token else 'No'}")
        
        # Crear estado inicial - user_id ya debería ser el Google ID
        agent_state = AgentState(
            query=message,
            intent="",
            user_id=user_id,  # Este ID debería ser el Google ID desde la API
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