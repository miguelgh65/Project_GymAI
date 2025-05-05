# fitness_chatbot/nodes/router_node.py

import logging
import json
import re
from typing import Tuple, Dict, Any, Optional

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

logger = logging.getLogger("fitness_chatbot")

async def classify_intent(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Clasifica la intención del usuario utilizando un enfoque Chain of Thought con LLM.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("🔍 --- CLASIFICACIÓN DE INTENCIÓN INICIADA --- 🔍")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener la consulta del usuario
    query = agent_state["query"]
    logger.info(f"📝 Consulta a clasificar: '{query}'")
    
    # Comprobar si hay una intención ya definida (para llamadas directas a nodos específicos)
    if agent_state.get("intent"):
        logger.info(f"⚡ Intención ya definida: {agent_state['intent']}")
        
        # Actualizar historial de mensajes
        if "messages" not in memory_state:
            memory_state["messages"] = []
        
        memory_state["messages"].append({"role": "user", "content": query})
        
        return agent_state, memory_state
    
    try:
        # Obtener mensajes de prompt para el router
        messages = PromptManager.get_prompt_messages("router", query=query)
        
        # Invocar LLM para clasificación con Chain of Thought
        llm = get_llm()
        
        if not llm:
            logger.error("❌ No se pudo obtener el LLM para clasificación")
            # Asignar intención general como fallback
            intent = IntentType.GENERAL
            explanation = "Error: LLM no disponible"
        else:
            # Configurar una temperatura más baja para respuestas más consistentes
            if hasattr(llm, 'with_temperature'):
                llm = llm.with_temperature(0.1)
            
            # Invocar LLM con el prompt optimizado
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"📊 Respuesta cruda del LLM:\n{content[:200]}...")
            
            # Extraer el JSON con la clasificación
            intent_data = extract_intent_from_response(content)
            
            if intent_data and "intent" in intent_data:
                intent = intent_data["intent"].lower()
                explanation = intent_data.get("explanation", "")
                logger.info(f"🎯 Intención extraída del JSON: {intent}")
                logger.info(f"📋 Explicación: {explanation}")
            else:
                logger.warning("⚠️ No se pudo extraer la intención")
                intent = IntentType.GENERAL
                explanation = "No se pudo determinar la intención con suficiente confianza"
    
    except Exception as e:
        logger.error(f"❌ Error en la clasificación de intención: {str(e)}")
        intent = IntentType.GENERAL
        explanation = f"Error durante la clasificación: {str(e)}"
    
    # Normalizar la intención a un formato estándar
    normalized_intent = normalize_intent(intent)
    
    # Actualizar estado del agente
    agent_state["intent"] = normalized_intent
    
    # Actualizar historial de mensajes
    if "messages" not in memory_state:
        memory_state["messages"] = []
    
    memory_state["messages"].append({"role": "user", "content": query})
    
    # Log con emojis para mejor visibilidad
    intent_emojis = {
        IntentType.EXERCISE: "🏋️",
        IntentType.NUTRITION: "🍎",
        IntentType.PROGRESS: "📈",
        IntentType.HISTORY: "📋",
        IntentType.LOG_ACTIVITY: "✏️",
        IntentType.FITBIT: "⌚",
        IntentType.TODAY_ROUTINE: "📅",
        IntentType.EDIT_ROUTINE: "✍️",
        IntentType.GENERAL: "💬"
    }
    emoji = intent_emojis.get(normalized_intent, "❓")
    
    logger.info(f"{emoji} RESULTADO FINAL DE CLASIFICACIÓN: {normalized_intent} {emoji}")
    logger.info("🏁 --- CLASIFICACIÓN DE INTENCIÓN FINALIZADA --- 🏁")
    
    return agent_state, memory_state

def extract_intent_from_response(content: str) -> Optional[Dict[str, str]]:
    """
    Extrae la intención y explicación de la respuesta del LLM.
    
    Args:
        content: Respuesta del LLM
        
    Returns:
        Dict con intent y explanation, o None si no se pudo extraer
    """
    try:
        # Buscar un objeto JSON en la respuesta
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if not json_match:
            logger.warning("No se encontró JSON en la respuesta del LLM")
            return None
        
        json_str = json_match.group(0)
        intent_data = json.loads(json_str)
        
        # Verificar que tenga los campos necesarios
        if "intent" not in intent_data:
            logger.warning("JSON encontrado pero sin campo 'intent'")
            return None
        
        return intent_data
    
    except json.JSONDecodeError:
        logger.error("Error decodificando JSON de la respuesta del LLM")
        
        # Fallback: intentar extraer con regex si no hay JSON válido
        try:
            intent_match = re.search(r'intent["\']?\s*:\s*["\']?(\w+)["\']?', content)
            if intent_match:
                intent = intent_match.group(1).lower()
                
                # Intentar extraer explicación si está disponible
                explanation_match = re.search(r'explanation["\']?\s*:\s*["\']?(.*?)["\']?[,}]', content)
                explanation = explanation_match.group(1) if explanation_match else "Sin explicación disponible"
                
                return {
                    "intent": intent,
                    "explanation": explanation
                }
        except Exception:
            pass
        
        return None
    except Exception as e:
        logger.error(f"Error extrayendo intención: {str(e)}")
        return None

def normalize_intent(intent: str) -> str:
    """
    Normaliza la intención a uno de los tipos estándar definidos en IntentType.
    
    Args:
        intent: Intención detectada por el LLM
        
    Returns:
        Intención normalizada
    """
    intent_lower = intent.lower().strip()
    
    # Mapeo de variantes comunes a los tipos estándar
    intent_map = {
        IntentType.EXERCISE: ["exercise", "ejercicio", "entrenamiento", "ejercitar"],
        IntentType.NUTRITION: ["nutrition", "nutricion", "nutrición", "dieta", "alimentacion", "alimentación"],
        IntentType.PROGRESS: ["progress", "progreso", "evolución", "evolucion", "analisis", "análisis", "tendencia"],
        IntentType.HISTORY: ["history", "historial", "histórico", "historico", "registro", "ver", "mostrar", "último"],
        IntentType.LOG_ACTIVITY: ["log_activity", "log", "registrar", "anotar", "registro", "actividad"],
        IntentType.FITBIT: ["fitbit", "datos", "personal", "salud", "health", "métrica", "metrica", "medición", "medicion"],
        IntentType.TODAY_ROUTINE: ["today_routine", "rutina_hoy", "hoy", "plan_diario", "día_actual"],
        IntentType.EDIT_ROUTINE: ["edit_routine", "editar", "modificar", "cambiar", "actualizar"],
        IntentType.GENERAL: ["general", "otro", "other", "desconocido", "unknown"]
    }
    
    # Si la intención ya coincide exactamente con un tipo estándar
    if intent_lower in IntentType.__dict__.values():
        return intent_lower
    
    # Buscar coincidencias en el mapeo
    for standard_intent, variants in intent_map.items():
        if any(variant == intent_lower for variant in variants) or any(variant in intent_lower for variant in variants):
            return standard_intent
    
    # Si no hay coincidencias, usar general como fallback
    return IntentType.GENERAL

# Función auxiliar para procesar mensajes directamente (API)
async def process_message(user_id: str, message: str, auth_token: Optional[str] = None) -> Any:
    """
    Procesa un mensaje del usuario y devuelve una respuesta usando el grafo de fitness.
    Función auxiliar para compatibilidad con APIs.
    
    Args:
        user_id: ID del usuario
        message: Mensaje del usuario
        auth_token: Token JWT para autenticación con el backend
        
    Returns:
        Objeto con la respuesta del chatbot
    """
    # Importar el grafo aquí para evitar importaciones circulares
    from fitness_chatbot.graphs.fitness_graph import create_fitness_graph
    
    try:
        # Log para depuración
        logger.info(f"🚀 Procesando mensaje con ID de usuario: {user_id}")
        logger.info(f"📝 Mensaje recibido: '{message}'")
        logger.info(f"🔑 Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
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
            logger.error("❌ Error: fitness_graph es None. No se pudo crear el grafo.")
            class MessageResponse:
                def __init__(self, content):
                    self.content = content
            return MessageResponse("Lo siento, ocurrió un error interno al procesar tu mensaje. Por favor, intenta de nuevo más tarde.")
        
        # Invocar el grafo
        final_state = await fitness_graph.ainvoke((agent_state, memory_state))
        final_agent_state, final_memory_state = final_state
        
        # Obtener respuesta generada
        response = final_agent_state.get("generation", "")
        logger.info(f"✉️ Respuesta generada: '{response[:50]}...'")
        
        # Crear objeto de respuesta similar a MessageResponse
        class MessageResponse:
            def __init__(self, content):
                self.content = content
        
        return MessageResponse(response)
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {str(e)}", exc_info=True)
        # Crear una clase de respuesta para devolver el error
        class MessageResponse:
            def __init__(self, content):
                self.content = content
        
        return MessageResponse(f"Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo más tarde.")