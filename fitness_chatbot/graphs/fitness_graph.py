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
    Crea el grafo principal para el chatbot de fitness.
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
    
    # Función para el router principal
    def decide_initial_node(states):
        agent_state, _ = states
        intent = agent_state.get("intent", IntentType.GENERAL)
        logger.info(f"🔀 Enrutando por intención: {intent}")
        
        if intent == IntentType.PROGRESS:
            # Para progress, marcamos un intent especial
            agent_state["is_progress"] = True
            # Primero vamos a process_history
            return "process_history"
        else:
            # Rutas normales
            if intent == IntentType.EXERCISE:
                return "process_exercise"
            elif intent == IntentType.NUTRITION:
                return "process_nutrition"
            elif intent == IntentType.HISTORY:
                return "process_history"
            elif intent == IntentType.LOG_ACTIVITY:
                return "log_activity"
            elif intent == IntentType.FITBIT:
                return "process_fitbit"
            elif intent == IntentType.TODAY_ROUTINE:
                return "process_today_routine"
            else:
                return "generate_response"
    
    # Añadir edge condicional desde classify_intent
    graph.add_conditional_edges(
        "classify_intent",
        decide_initial_node,
        {
            "process_exercise": "process_exercise",
            "process_nutrition": "process_nutrition",
            "process_history": "process_history",
            "log_activity": "log_activity", 
            "process_fitbit": "process_fitbit",
            "process_today_routine": "process_today_routine",
            "generate_response": "generate_response"
        }
    )
    
    # Función para decidir si vamos a progress o a generate_response desde history
    def from_history_decide_next(states):
        agent_state, _ = states
        is_progress = agent_state.get("is_progress", False)
        
        if is_progress:
            # Si es progress, vamos a fitbit
            return "process_fitbit"
        else:
            # Si no es progress, vamos a generate_response
            return "generate_response"
    
    # Añadir edge condicional desde process_history
    graph.add_conditional_edges(
        "process_history",
        from_history_decide_next,
        {
            "process_fitbit": "process_fitbit",
            "generate_response": "generate_response"
        }
    )
    
    # Función para decidir si vamos a progress o a generate_response desde fitbit
    def from_fitbit_decide_next(states):
        agent_state, _ = states
        is_progress = agent_state.get("is_progress", False)
        
        if is_progress:
            # Si es progress, vamos a process_progress
            return "process_progress"
        else:
            # Si no es progress, vamos a generate_response
            return "generate_response"
    
    # Añadir edge condicional desde process_fitbit
    graph.add_conditional_edges(
        "process_fitbit",
        from_fitbit_decide_next,
        {
            "process_progress": "process_progress",
            "generate_response": "generate_response"
        }
    )
    
    # Conexiones directas a generate_response
    graph.add_edge("process_exercise", "generate_response")
    graph.add_edge("process_nutrition", "generate_response") 
    graph.add_edge("process_today_routine", "generate_response")
    graph.add_edge("log_activity", "generate_response")
    graph.add_edge("process_progress", "generate_response")
    
    # Conexión final
    graph.add_edge("generate_response", END)
    
    # Definir el punto de entrada
    graph.set_entry_point("classify_intent")
    
    # Compilar el grafo
    return graph.compile()