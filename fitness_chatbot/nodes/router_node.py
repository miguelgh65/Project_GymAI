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
        
        # Invocar LLM para clasificación
        llm = get_llm()
        
        if not llm:
            logger.error("No se pudo obtener el LLM para clasificación")
            # Asignar intención general como fallback
            intent = IntentType.GENERAL
        else:
            # Configurar una temperatura más baja para respuestas más consistentes
            if hasattr(llm, 'with_temperature'):
                llm = llm.with_temperature(0.1)
            
            # Invocar LLM con el prompt optimizado
            response = await llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"Respuesta cruda del LLM: {content[:200]}...")
            
            # Intentar extraer el JSON de la respuesta
            try:
                # Buscar un objeto JSON en la respuesta
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    json_data = json.loads(json_str)
                    
                    if 'intent' in json_data:
                        intent = json_data['intent'].lower()
                        explanation = json_data.get('explanation', '')
                        logger.info(f"Intención extraída del JSON: {intent}")
                        logger.info(f"Explicación: {explanation}")
                    else:
                        logger.warning("JSON encontrado pero sin campo 'intent'")
                        intent = IntentType.GENERAL
                else:
                    # Fallback: intentar extraer con regex si no hay JSON válido
                    intent_match = re.search(r'intent["\']?\s*:\s*["\']?(\w+)["\']?', content)
                    if intent_match:
                        intent = intent_match.group(1).lower()
                        logger.info(f"Intención extraída por regex: {intent}")
                    else:
                        logger.warning("No se pudo extraer la intención de la respuesta")
                        intent = IntentType.GENERAL
            except json.JSONDecodeError as e:
                logger.warning(f"Error decodificando JSON: {e}")
                # Intentar extraer con regex
                intent_match = re.search(r'intent["\']?\s*:\s*["\']?(\w+)["\']?', content)
                if intent_match:
                    intent = intent_match.group(1).lower()
                    logger.info(f"Intención extraída por regex (después de JSON fallido): {intent}")
                else:
                    logger.warning("No se pudo extraer la intención")
                    intent = IntentType.GENERAL
    
    except Exception as e:
        logger.error(f"Error en la clasificación de intención: {str(e)}")
        intent = IntentType.GENERAL
    
    # Normalizar la intención a un formato estándar
    normalized_intent = normalize_intent(intent)
    
    # Actualizar estado del agente
    agent_state["intent"] = normalized_intent
    
    # Actualizar historial de mensajes
    if "messages" not in memory_state:
        memory_state["messages"] = []
    
    memory_state["messages"].append({"role": "user", "content": query})
    
    logger.info(f"RESULTADO FINAL DE CLASIFICACIÓN: {normalized_intent}")
    logger.info("--- CLASIFICACIÓN DE INTENCIÓN FINALIZADA ---")
    
    return agent_state, memory_state

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
        IntentType.PROGRESS: ["progress", "progreso", "evolución", "evolucion", "estadística", "estadistica", "histórico", "historico"],
        IntentType.LOG_ACTIVITY: ["log_activity", "log", "registrar", "anotar", "registro", "actividad"],
        IntentType.FITBIT: ["fitbit", "datos", "personal", "salud", "health", "métrica", "metrica", "medición", "medicion"],
        IntentType.GENERAL: ["general", "otro", "other", "desconocido", "unknown"]
    }
    
    # Buscar coincidencias en el mapeo
    for standard_intent, variants in intent_map.items():
        if any(variant in intent_lower for variant in variants):
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