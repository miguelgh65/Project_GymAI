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
    
    # PASO 1: Detección rápida con reglas para casos comunes
    query_lower = query.lower()
    
    # --- 1. DETECTAR REGISTRO DE EJERCICIO ---
    
    # Palabras clave para detectar registro de ejercicio
    registration_keywords = [
        'registra', 'apunta', 'anota', 'guarda', 'agrega', 'añade', 
        'he hecho', 'hice', 'realicé', 'terminé'
    ]
    
    # Ejercicios comunes (en español)
    exercise_keywords = [
        'press banca', 'press de banca', 'banca', 'sentadilla', 'sentadillas', 
        'peso muerto', 'dominada', 'dominadas', 'curl', 'bíceps', 'fondos', 
        'press militar', 'elevaciones', 'remo', 'extensiones', 'tríceps', 
        'jalón', 'abdominales', 'flexiones', 'pushups', 'series', 'repeticiones'
    ]
    
    # Patrones numéricos típicos de ejercicios (3x10, 10x20kg, etc.)
    exercise_patterns = [
        r'\d+\s*[xX]\s*\d+',        # 10x20, 3x10
        r'\d+\s*series',            # 3 series
        r'\d+\s*repeticiones',      # 10 repeticiones
        r'\d+\s*reps',              # 10 reps
        r'\d+\s*kg',                # 60 kg
        r'\d+\s*con\s*\d+',         # 10 con 60
    ]
    
    # Verificar si hay palabras clave de registro
    has_registration_keyword = any(keyword in query_lower for keyword in registration_keywords)
    
    # Verificar si hay palabras clave de ejercicio
    has_exercise_keyword = any(keyword in query_lower for keyword in exercise_keywords)
    
    # Verificar si hay patrones numéricos de ejercicio
    has_exercise_pattern = any(re.search(pattern, query_lower) for pattern in exercise_patterns)
    
    # Detectar caso específico: "He hecho press banca 10x20, 10x20 y 10x60"
    is_specific_pattern = (
        ('he hecho' in query_lower or 'hice' in query_lower) and 
        any(ex in query_lower for ex in ['press', 'banca', 'sentadilla', 'peso muerto']) and
        re.search(r'\d+\s*[xX]\s*\d+', query_lower)
    )
    
    # --- 2. DETECTAR CONSULTA DE PROGRESO ---
    
    # Palabras clave para progreso
    progress_keywords = [
        'progreso', 'avance', 'mejora', 'evolución', 'estadística', 'cómo voy', 
        'he mejorado', 'comparar', 'gráfica', 'tendencia', 'comparado con'
    ]
    
    has_progress_keyword = any(keyword in query_lower for keyword in progress_keywords)
    
    # --- 3. DETECTAR CONSULTA DE NUTRICIÓN ---
    
    # Palabras clave para nutrición
    nutrition_keywords = [
        'comida', 'dieta', 'nutrición', 'comer', 'proteína', 'carbohidratos', 
        'calorías', 'macros', 'plan alimenticio', 'suplemento', 'alimentación',
        'desayuno', 'almuerzo', 'cena', 'merienda', 'hidratación'
    ]
    
    has_nutrition_keyword = any(keyword in query_lower for keyword in nutrition_keywords)
    
    # --- 4. DETECTAR CONSULTA DE FITBIT ---
    
    # Palabras clave para Fitbit
    fitbit_keywords = [
        'fitbit', 'pulsera', 'smartwatch', 'pasos', 'actividad', 'dormir', 
        'sueño', 'cardio', 'frecuencia cardíaca', 'ritmo', 'dispositivo'
    ]
    
    has_fitbit_keyword = any(keyword in query_lower for keyword in fitbit_keywords)
    
    # --- 5. DETECTAR PREGUNTAS SOBRE CONSULTA DE EJERCICIOS (no registro) ---
    
    # Patrones de preguntas comunes
    question_patterns = [
        r'¿',                           # Preguntas en español
        r'\?',                          # Signo de interrogación
        r'^(qué|cómo|cuál|cuándo|cuánto)',  # Palabras interrogativas
        r'dime',                        # Comando de pregunta
        r'muéstrame',                   # Comando de mostrar
        r'cuáles'                       # Palabra interrogativa
    ]
    
    has_question_pattern = any(re.search(pattern, query_lower) for pattern in question_patterns)
    
    # --- DECISIÓN BASADA EN REGLAS ---
    
    # 1. Prioridad para registro de ejercicio
    if is_specific_pattern or (has_registration_keyword and has_exercise_keyword) or (has_exercise_keyword and has_exercise_pattern):
        logger.info("✅ Detectada intención LOG_ACTIVITY mediante reglas")
        normalized_intent = IntentType.LOG_ACTIVITY
    
    # 2. Preguntas sobre progreso
    elif has_progress_keyword and has_exercise_keyword:
        logger.info("✅ Detectada intención PROGRESS mediante reglas")
        normalized_intent = IntentType.PROGRESS
    
    # 3. Preguntas sobre nutrición
    elif has_nutrition_keyword:
        logger.info("✅ Detectada intención NUTRITION mediante reglas")
        normalized_intent = IntentType.NUTRITION
    
    # 4. Preguntas sobre ejercicios (no registro)
    elif has_exercise_keyword and has_question_pattern:
        logger.info("✅ Detectada intención EXERCISE mediante reglas")
        normalized_intent = IntentType.EXERCISE
    
    # 5. Utilizar el LLM para casos menos claros
    else:
        try:
            # Obtener mensajes de prompt para el router
            messages = PromptManager.get_prompt_messages("router", query=query)
            
            # Obtener el modelo LLM configurado con salida estructurada
            llm = get_llm().with_structured_output(IntentClassification)
            
            # Llamar al LLM para clasificar
            classification = await llm.ainvoke(messages)
            
            # Extraer la intención
            intent = classification.intent.lower()
            
            # Normalizar la intención
            if "ejercicio" in intent or "entrenamiento" in intent or intent == "exercise":
                normalized_intent = IntentType.EXERCISE
            elif "nutri" in intent or "comida" in intent or "dieta" in intent or intent == "nutrition":
                normalized_intent = IntentType.NUTRITION
            elif "progreso" in intent or "estadística" in intent or intent == "progress":
                normalized_intent = IntentType.PROGRESS
            elif any(kw in intent for kw in ["registrar", "anotar", "log"]) or intent == "log_activity":
                normalized_intent = IntentType.LOG_ACTIVITY
            else:
                normalized_intent = IntentType.GENERAL
            
            logger.info(f"LLM clasificó la intención como: {intent} → {normalized_intent}")
                
        except Exception as e:
            logger.error(f"Error en la clasificación con LLM: {str(e)}")
            
            # Si falla el LLM, determinar intención basada en palabras clave
            if has_exercise_keyword:
                if has_registration_keyword or has_exercise_pattern:
                    normalized_intent = IntentType.LOG_ACTIVITY
                    logger.info("Fallback a intención LOG_ACTIVITY por palabras clave")
                else:
                    normalized_intent = IntentType.EXERCISE
                    logger.info("Fallback a intención EXERCISE por palabras clave")
            elif has_nutrition_keyword:
                normalized_intent = IntentType.NUTRITION
                logger.info("Fallback a intención NUTRITION por palabras clave")
            elif has_progress_keyword:
                normalized_intent = IntentType.PROGRESS
                logger.info("Fallback a intención PROGRESS por palabras clave")
            else:
                normalized_intent = IntentType.GENERAL
                logger.info("Fallback a intención GENERAL por error")
    
    # Actualizar estado con la intención detectada
    agent_state["intent"] = normalized_intent
    
    # Actualizar historial de mensajes
    if "messages" not in memory_state:
        memory_state["messages"] = []
    
    memory_state["messages"].append({"role": "user", "content": query})
    
    logger.info(f"Intención normalizada final: {normalized_intent}")
    logger.info("--- CLASIFICACIÓN DE INTENCIÓN FINALIZADA ---")
    
    return agent_state, memory_state

# Función auxiliar para procesar mensajes directamente (API)
async def process_message(user_id: str, message: str) -> Any:
    """
    Procesa un mensaje del usuario y devuelve una respuesta usando el grafo de fitness.
    Función auxiliar para compatibilidad con APIs.
    
    Args:
        user_id: ID del usuario (debe ser Google ID)
        message: Mensaje del usuario
        
    Returns:
        Objeto con la respuesta del chatbot
    """
    # Importar el grafo aquí para evitar importaciones circulares
    from fitness_chatbot.graphs.fitness_graph import create_fitness_graph
    
    try:
        # Log para depuración
        logger.info(f"Procesando mensaje con ID de usuario: {user_id}")
        
        # Crear estado inicial - user_id ya debería ser el Google ID
        agent_state = AgentState(
            query=message,
            intent="",
            user_id=user_id,  # Este ID debería ser el Google ID desde la API
            user_context={},
            intermediate_steps=[],
            retrieved_data=[],
            generation=""
        )
        
        memory_state = MemoryState(
            messages=[]
        )
        
        # Obtener el grafo de fitness
        fitness_graph = create_fitness_graph()
        
        # Invocar el grafo
        final_state = await fitness_graph.ainvoke((agent_state, memory_state))
        final_agent_state, final_memory_state = final_state
        
        # Obtener respuesta generada
        response = final_agent_state.get("generation", "")
        
        # Crear objeto de respuesta similar a MessageResponse
        class MessageResponse:
            def __init__(self, content):
                self.content = content
        
        return MessageResponse(response)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
        return MessageResponse(f"Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo más tarde.")