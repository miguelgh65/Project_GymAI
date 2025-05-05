# fitness_chatbot/nodes/today_routine_node.py
import logging
from datetime import datetime
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.utils.api_utils import make_api_request

logger = logging.getLogger("fitness_chatbot")

async def process_today_routine(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas sobre la rutina de ejercicios del día actual.
    Hace una llamada simple al endpoint /api/rutina_hoy y formatea la respuesta.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE RUTINA DIARIA INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de rutina diaria: '{query}' para usuario {user_id}")
    
    try:
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        logger.info(f"Token de autenticación disponible: {'Sí' if auth_token else 'No'}")
        
        # Determinar qué día de la semana es hoy
        today = datetime.now()
        day_of_week = today.weekday() + 1  # datetime.weekday() devuelve 0-6 donde 0 es lunes
        day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        day_name = day_names[day_of_week - 1]
        
        logger.info(f"Consultando rutina para hoy ({day_name})")
        
        # Llamar al endpoint directamente (sin usar ninguna chain)
        endpoint = "rutina_hoy"
        params = {"format": "json"}
        
        # Usar un timeout reducido
        response_data = make_api_request(
            endpoint=endpoint, 
            method="GET", 
            params=params, 
            auth_token=auth_token,
            timeout=8,      # Timeout reducido
            retries=1       # Solo un intento
        )
        
        # Procesar la respuesta
        if response_data.get("success", False) and response_data.get("rutina"):
            ejercicios = response_data["rutina"].get("ejercicios", [])
            respuesta = format_routine_response(ejercicios, day_name)
        else:
            # Respuesta cuando no hay rutina configurada
            respuesta = f"No tienes una rutina configurada para hoy ({day_name}). Normalmente, el {day_name} es un buen día para entrenar los siguientes grupos musculares:\n\n"
            
            # Recomendaciones por día
            if day_of_week == 1:  # Lunes
                respuesta += "- **Pecho y tríceps**: Press banca, fondos, extensiones de tríceps\n"
            elif day_of_week == 2:  # Martes
                respuesta += "- **Espalda y bíceps**: Dominadas, remo, curl de bíceps\n"
            elif day_of_week == 3:  # Miércoles
                respuesta += "- **Piernas**: Sentadillas, peso muerto, extensiones\n"
            elif day_of_week == 4:  # Jueves
                respuesta += "- **Hombros y abdomen**: Press militar, elevaciones laterales, planchas\n"
            elif day_of_week == 5:  # Viernes
                respuesta += "- **Fullbody**: Combinación de los principales grupos musculares\n"
            else:  # Fin de semana
                respuesta += "- **Cardio o descanso activo**: Carrera, natación, ciclismo\n"
            
            respuesta += "\n¿Te gustaría que te ayude a crear una rutina para este día?"
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de rutina diaria: {str(e)}")
        respuesta = f"Lo siento, tuve un problema al consultar tu rutina de hoy. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE RUTINA DIARIA FINALIZADO ---")
    return agent_state, memory_state

def format_routine_response(ejercicios, day: str) -> str:
    """
    Formatea la respuesta con los datos de la rutina.
    
    Args:
        ejercicios: Lista de ejercicios
        day: Nombre del día de la semana
        
    Returns:
        Respuesta formateada
    """
    # Verificar si hay ejercicios
    if not ejercicios or len(ejercicios) == 0:
        return f"No tienes una rutina configurada para hoy ({day}). ¿Quieres que te ayude a crear una?"
    
    # Construir respuesta
    respuesta = f"## 📅 Tu rutina de hoy ({day.capitalize()})\n\n"
    
    # Si ejercicios es una lista simple de strings
    if isinstance(ejercicios, list) and all(isinstance(ej, str) for ej in ejercicios):
        respuesta += "Hoy te toca entrenar:\n\n"
        for i, ej in enumerate(ejercicios, 1):
            respuesta += f"### {i}. {ej}\n\n"
    # Si ejercicios es una lista de objetos
    elif isinstance(ejercicios, list) and all(isinstance(ej, dict) for ej in ejercicios):
        for i, ej in enumerate(ejercicios, 1):
            nombre = ej.get("nombre", f"Ejercicio {i}")
            series = ej.get("series", "3-4")
            repeticiones = ej.get("repeticiones", "8-12")
            
            respuesta += f"### {i}. {nombre}\n"
            respuesta += f"- **Series:** {series}\n"
            respuesta += f"- **Repeticiones:** {repeticiones}\n"
            
            if "notas" in ej:
                respuesta += f"- **Notas:** {ej['notas']}\n"
            
            respuesta += "\n"
    # Si es un solo string
    elif isinstance(ejercicios, str):
        respuesta += f"Hoy te toca hacer: **{ejercicios}**\n\n"
    
    # Añadir mensaje motivacional
    respuesta += "💪 ¡A por ello! ¿Necesitas más información sobre algún ejercicio en particular?"
    
    return respuesta