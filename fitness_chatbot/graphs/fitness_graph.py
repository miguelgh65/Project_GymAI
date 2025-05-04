# fitness_chatbot/graphs/fitness_graph.py

import logging
from typing import Dict, Any, Tuple

from langgraph.graph import END, StateGraph

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.nodes.router_node import classify_intent
from fitness_chatbot.nodes.exercise_node import process_exercise_query
from fitness_chatbot.nodes.nutrition_node import process_nutrition_query
# MODIFICADO: Usar history_node en lugar de progress_node
from fitness_chatbot.nodes.history_node import process_history_query
from fitness_chatbot.nodes.log_activity_node import log_activity
from fitness_chatbot.nodes.fitbit_node import process_fitbit_query
from fitness_chatbot.nodes.response_node import generate_final_response

logger = logging.getLogger("fitness_chatbot")

def create_fitness_graph():
    """
    Crea el grafo principal para el chatbot de fitness.
    
    Returns:
        Un grafo compilado para procesar consultas de fitness
    """
    # Inicializar el grafo con el tipo de estado combinado
    graph = StateGraph((AgentState, MemoryState))
    
    # Añadir nodos
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("process_exercise", process_exercise_query)
    graph.add_node("process_nutrition", process_nutrition_query)
    # MODIFICADO: Usar process_history_query en lugar del eliminado process_progress_query
    graph.add_node("process_progress", process_history_query)
    graph.add_node("log_activity", log_activity)
    graph.add_node("process_fitbit", process_fitbit_query)
    graph.add_node("generate_response", generate_final_response)
    
    # Función para enrutar según la intención
    def route_by_intent(states):
        """Determina el siguiente nodo según la intención detectada."""
        agent_state, _ = states
        intent = agent_state.get("intent", IntentType.GENERAL)
        logger.info(f"🔀 Enrutando por intención: {intent}")
        
        # Ya no necesitamos la redirección especial porque ahora sí tenemos un nodo para PROGRESS
        return intent
    
    # Definir flujos condicionales basados en la intención
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            IntentType.EXERCISE: "process_exercise",
            IntentType.NUTRITION: "process_nutrition",
            # MODIFICADO: Ahora sí direccionamos a process_progress (que utiliza history_node)
            IntentType.PROGRESS: "process_progress",
            IntentType.LOG_ACTIVITY: "log_activity",
            IntentType.FITBIT: "process_fitbit",
            IntentType.GENERAL: "generate_response"
        }
    )
    
    # Conexiones entre nodos y respuesta final
    graph.add_edge("process_exercise", "generate_response")
    graph.add_edge("process_nutrition", "generate_response")
    # MODIFICADO: Esta conexión ahora sí existe
    graph.add_edge("process_progress", "generate_response")
    graph.add_edge("log_activity", "generate_response")
    graph.add_edge("process_fitbit", "generate_response")
    graph.add_edge("generate_response", END)
    
    # Definir el punto de entrada
    graph.set_entry_point("classify_intent")
    
    # Compilar el grafo SIN checkpointer para evitar error
    return graph.compile()