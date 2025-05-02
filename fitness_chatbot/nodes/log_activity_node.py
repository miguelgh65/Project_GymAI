# fitness_chatbot/nodes/log_activity_node.py - VERSIÓN SIMPLE
import logging
from typing import Tuple, Dict, Any
import re

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState

# Importar servicios del backend
try:
    from back_end.gym.services.database import insert_into_db
    from back_end.gym.services.prompt_service import format_for_postgres
    SERVICES_AVAILABLE = True
    logger = logging.getLogger("fitness_chatbot")
    logger.info("✅ Servicios de DB disponibles")
except ImportError:
    # Definir stubs simples
    def format_for_postgres(text):
        return None
    def insert_into_db(data, user_id):
        return False
    
    SERVICES_AVAILABLE = False
    logger = logging.getLogger("fitness_chatbot")
    logger.warning("⚠️ Servicios de DB NO disponibles")

async def log_activity(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """Registra ejercicios utilizando el servicio del backend."""
    logger.info("--- REGISTRO DE ACTIVIDAD ---")
    
    agent_state, memory_state = states
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando registro: '{query}' para usuario {user_id}")
    
    # Usar el servicio del backend para formatear
    try:
        if not SERVICES_AVAILABLE:
            logger.error("Servicios de backend no disponibles")
            respuesta = "Lo siento, el servicio de registro no está disponible en este momento."
        else:
            # 1. Formatear el texto con el servicio del backend
            formatted_json = format_for_postgres(query)
            
            if not formatted_json:
                logger.warning(f"No se pudo formatear la consulta: {query}")
                respuesta = "No pude entender qué ejercicio quieres registrar. Por favor, sé más específico, por ejemplo: 'Registra press banca 3 series de 10 repeticiones con 60kg'."
            else:
                # 2. Insertar en la base de datos
                success = insert_into_db(formatted_json, user_id)
                
                if success:
                    # Registro exitoso
                    ejercicio = formatted_json.get("ejercicio", "ejercicio")
                    respuesta = f"¡He registrado tu ejercicio de {ejercicio} correctamente! ¿Quieres registrar algo más?"
                    logger.info(f"Ejercicio registrado con éxito: {ejercicio}")
                else:
                    # Error en inserción
                    logger.error("Error al insertar en la base de datos")
                    respuesta = "Lo siento, hubo un error al guardar tu ejercicio en la base de datos. ¿Podrías intentarlo de nuevo?"
    except Exception as e:
        logger.error(f"Error en registro de actividad: {e}")
        respuesta = "Ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo con un formato más claro."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- FIN REGISTRO DE ACTIVIDAD ---")
    return agent_state, memory_state