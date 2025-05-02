# fitness_chatbot/nodes/exercise_node.py - VERSIÓN SIMPLE
import logging
from typing import Tuple, Dict, Any
import json

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm

# Importar servicio de base de datos
try:
    from back_end.gym.services.database import get_exercise_logs
    DB_SERVICES_AVAILABLE = True
    logger = logging.getLogger("fitness_chatbot")
    logger.info("✅ Servicios de DB disponibles")
except ImportError:
    # Definir stub para get_exercise_logs
    def get_exercise_logs(user_id, days=30):
        return []
    
    DB_SERVICES_AVAILABLE = False
    logger = logging.getLogger("fitness_chatbot")
    logger.warning("⚠️ Servicios de DB NO disponibles")

async def process_exercise_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """Procesa consultas sobre ejercicios."""
    logger.info("--- PROCESANDO CONSULTA DE EJERCICIO ---")
    
    agent_state, memory_state = states
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Consulta: '{query}' para usuario {user_id}")
    
    # Obtener datos de ejercicios
    try:
        # Llamar al servicio del backend
        exercise_logs = get_exercise_logs(user_id, days=30) 
        
        # Log para depuración
        logger.info(f"Obtenidos {len(exercise_logs)} ejercicios de la BD")
        
        # Formatear para respuesta
        if exercise_logs:
            # Hay datos
            respuesta = generar_respuesta_ejercicios(exercise_logs, query)
        else:
            # No hay datos
            respuesta = "No encontré registros de ejercicios en tu historial. Puedes registrar tus entrenamientos diciéndome algo como 'Registra press banca 3 series de 10 repeticiones con 60kg'."
            
    except Exception as e:
        logger.error(f"Error obteniendo datos: {e}")
        respuesta = "Lo siento, ocurrió un error al consultar tu historial de ejercicios."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- FINALIZADO PROCESAMIENTO DE EJERCICIO ---")
    return agent_state, memory_state

def generar_respuesta_ejercicios(logs, query):
    """Genera una respuesta simple con los ejercicios."""
    try:
        # Ordenar por fecha (del más reciente al más antiguo)
        logs = sorted(logs, key=lambda x: x.get('fecha', ''), reverse=True)
        
        # Formatear para mostrar los últimos ejercicios
        ejercicios_texto = []
        for i, log in enumerate(logs[:5]):
            fecha = log.get('fecha', 'fecha desconocida')
            if isinstance(fecha, str) and len(fecha) > 10:
                fecha = fecha[:10]  # Solo la fecha
                
            nombre = log.get('ejercicio', 'ejercicio desconocido')
            
            # Formatear repeticiones
            reps_texto = ""
            repeticiones = log.get('repeticiones')
            if repeticiones:
                if isinstance(repeticiones, str):
                    try:
                        repeticiones = json.loads(repeticiones)
                    except:
                        repeticiones = None
                
                if isinstance(repeticiones, list) and repeticiones:
                    series = []
                    for rep in repeticiones:
                        if isinstance(rep, dict):
                            r = rep.get('repeticiones', '?')
                            p = rep.get('peso', '?')
                            series.append(f"{r}×{p}kg")
                    reps_texto = ", ".join(series)
            
            ejercicios_texto.append(f"• {fecha}: {nombre} - {reps_texto}")
        
        # Crear respuesta
        return f"## Tus últimos ejercicios\n\n" + "\n".join(ejercicios_texto) + "\n\nSi quieres registrar un nuevo ejercicio, puedes decírmelo directamente."
        
    except Exception as e:
        logger.error(f"Error generando respuesta de ejercicios: {e}")
        return "He encontrado tus registros de ejercicios, pero tuve problemas al mostrarlos. Intenta preguntar de otra manera."