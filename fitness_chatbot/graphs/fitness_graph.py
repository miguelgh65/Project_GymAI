# fitness_chatbot/graphs/fitness_graph.py

import logging
from typing import Dict, Any, Tuple

from langgraph.graph import END, StateGraph

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.nodes.router_node import classify_intent
from fitness_chatbot.nodes.exercise_node import process_exercise_query
from fitness_chatbot.nodes.nutrition_node import process_nutrition_query
from fitness_chatbot.nodes.progress_node import process_progress_query
from fitness_chatbot.nodes.log_activity_node import log_activity
from fitness_chatbot.nodes.fitbit_node import process_fitbit_query
from fitness_chatbot.nodes.response_node import generate_final_response
from fitness_chatbot.nodes.history_node import process_history_query
from fitness_chatbot.nodes.today_routine_node import process_today_routine

logger = logging.getLogger("fitness_chatbot")

def create_fitness_graph():
    """
    Crea el grafo principal para el chatbot de fitness con ejecución paralela
    de nodos para consultas complejas como progress.
    
    Returns:
        Un grafo compilado para procesar consultas de fitness
    """
    # Inicializar el grafo con el tipo de estado combinado
    graph = StateGraph((AgentState, MemoryState))
    
    # Añadir nodos
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("process_exercise", process_exercise_query)
    graph.add_node("process_nutrition", process_nutrition_query)
    graph.add_node("process_history", process_history_query)
    graph.add_node("log_activity", log_activity)
    graph.add_node("process_fitbit", process_fitbit_query)
    graph.add_node("process_today_routine", process_today_routine)
    graph.add_node("process_progress", process_progress_query)
    graph.add_node("generate_response", generate_final_response)
    
    # Función para enrutar según la intención
    def route_by_intent(states):
        """Determina el siguiente nodo según la intención detectada."""
        agent_state, _ = states
        intent = agent_state.get("intent", IntentType.GENERAL)
        logger.info(f"🔀 Enrutando por intención: {intent}")
        
        # Si es PROGRESS, vamos a ejecutar history y fitbit en paralelo
        # TODAY_ROUTINE NO forma parte del fan-in/fan-out
        if intent == IntentType.PROGRESS:
            return ["process_history", "process_fitbit"]
        
        # Para otras intenciones, seguimos el flujo normal
        return intent
    
    # Definir flujos condicionales basados en la intención
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            IntentType.EXERCISE: "process_exercise",
            IntentType.NUTRITION: "process_nutrition",
            IntentType.HISTORY: "process_history",
            IntentType.LOG_ACTIVITY: "log_activity",
            IntentType.FITBIT: "process_fitbit",
            IntentType.TODAY_ROUTINE: "process_today_routine",
            IntentType.GENERAL: "generate_response",
            # Fan-out para PROGRESS - Solo history y fitbit en paralelo
            ["process_history", "process_fitbit"]: None  # None significa que usaremos otros edges para dirigir el flujo
        }
    )
    
    # Conexiones estándar para nodos simples (non-PROGRESS)
    graph.add_edge("process_exercise", "generate_response")
    graph.add_edge("process_nutrition", "generate_response")
    graph.add_edge("process_today_routine", "generate_response")
    graph.add_edge("log_activity", "generate_response")
    graph.add_edge("generate_response", END)
    
    # Para nodos que pueden ejecutarse solos o como parte de PROGRESS
    # añadimos una edge condicional basada en si son parte de PROGRESS o no
    def route_to_final_or_join(states: Tuple[AgentState, MemoryState]) -> str:
        """Determina si el nodo debe ir a generate_response o a process_progress"""
        agent_state, _ = states
        intent = agent_state.get("intent", IntentType.GENERAL)
        
        # Si el intent es PROGRESS, estos nodos deben ir a process_progress
        if intent == IntentType.PROGRESS:
            return "process_progress"
        
        # De lo contrario, van directo a generate_response
        return "generate_response"
    
    # Aplicar routing condicional para history y fitbit
    graph.add_conditional_edges("process_history", route_to_final_or_join, 
                              ["process_progress", "generate_response"])
    graph.add_conditional_edges("process_fitbit", route_to_final_or_join, 
                              ["process_progress", "generate_response"])
    
    # Fan-in: El nodo de progress va a generate_response
    graph.add_edge("process_progress", "generate_response")
    
    # Definir el punto de entrada
    graph.set_entry_point("classify_intent")
    
    # Compilar el grafo
    return graph.compile()