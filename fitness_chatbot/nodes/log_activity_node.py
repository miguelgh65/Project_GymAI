# fitness_chatbot/nodes/log_activity_node.py - VERSIÓN CORREGIDA
import logging
import json
import os
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.utils.prompt_service_stub import format_for_postgres
from fitness_chatbot.utils.api_utils import make_api_request

logger = logging.getLogger("fitness_chatbot")

# URL base para la API - Usando la variable de entorno o el nombre del servicio de Docker
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend")

async def log_activity(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """Registra ejercicios utilizando la API del backend."""
    logger.info("--- REGISTRO DE ACTIVIDAD ---")
    
    agent_state, memory_state = states
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando registro: '{query}' para usuario {user_id}")
    
    try:
        # 1. Formatear localmente para previsualización (opcional)
        # Esta función sólo se usa para obtener información local sobre el ejercicio
        formatted_json = format_for_postgres(query)
        
        # Log del resultado del formateo
        if formatted_json:
            logger.info(f"Texto formateado localmente: {formatted_json.get('ejercicio', 'desconocido')}")
        else:
            logger.warning("No se pudo formatear el texto localmente")
        
        # 2. Llamar a la API para registrar el ejercicio usando nuestra utilidad
        payload = {
            "exercise_data": query  # Enviamos el texto original para que el backend lo procese
        }
        
        logger.info(f"Enviando solicitud a API para registrar ejercicio")
        
        # Hacer la solicitud a la API usando nuestra utilidad
        response = make_api_request("log-exercise", method="POST", json_data=payload)
        
        if response.get("success", False):
            # Registro exitoso
            # Usamos el ejercicio parseado localmente si está disponible
            ejercicio = formatted_json.get("ejercicio", "ejercicio") if formatted_json else "ejercicio"
            respuesta = f"¡He registrado tu ejercicio de {ejercicio} correctamente! ¿Quieres registrar algo más?"
            logger.info(f"Ejercicio registrado con éxito: {ejercicio}")
        else:
            # Error en la API
            error = response.get("error", "Error desconocido")
            mensaje_error = response.get("message", error)
            logger.error(f"Error en la API: {mensaje_error}")
            
            # Verificar si el error es porque no se pudo interpretar el ejercicio
            if response.get("status_code") == 422:
                respuesta = "No pude entender qué ejercicio quieres registrar. Por favor, sé más específico, por ejemplo: 'Registra press banca 3 series de 10 repeticiones con 60kg'."
            else:
                # Otro tipo de error
                respuesta = f"Lo siento, hubo un error al guardar tu ejercicio. ¿Podrías intentarlo de nuevo con un formato más claro?"
    except Exception as e:
        logger.error(f"Error en registro de actividad: {e}")
        respuesta = "Ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- FIN REGISTRO DE ACTIVIDAD ---")
    return agent_state, memory_state