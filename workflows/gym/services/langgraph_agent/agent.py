# Archivo: workflows/gym/services/langgraph_agent/agent.py
from typing import Dict, Any, List
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from config import llm
from services.langgraph_agent.state import ChatbotState
from services.langgraph_agent.tools import (
    get_recent_exercises,
    get_today_workout
)

def create_trainer_agent():
    """
    Crea un agente de entrenador personal utilizando LangGraph.
    Returns:
        Un grafo compilado listo para ser utilizado
    """
    # Definir las herramientas disponibles para el agente
    tools = [
        get_recent_exercises,
        get_today_workout
    ]
    
    # Preparar el LLM con las herramientas
    llm_with_tools = llm.bind_tools(tools)
    
    # Definir el grafo de estados
    graph_builder = StateGraph(ChatbotState)
    
    # Función para el nodo chatbot que usa el LLM con herramientas
    def chatbot(state):
        messages = state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}
    
    # Agregar nodos al grafo
    graph_builder.add_node("chatbot", chatbot)
    
    # Agregar nodo para ejecutar herramientas
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    
    # Definir las conexiones entre nodos
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    
    # Crear un checkpointer en memoria para mantener el estado
    memory = MemorySaver()
    
    # Compilar el grafo
    return graph_builder.compile(checkpointer=memory)

# Instanciar el agente globalmente
trainer_agent = create_trainer_agent()

def process_message(user_id: str, message: str) -> List[Dict[str, Any]]:
    """
    Procesa un mensaje del usuario y devuelve la respuesta del agente.
    Args:
        user_id: ID del usuario
        message: Mensaje del usuario
    Returns:
        Lista de mensajes de respuesta
    """
    # Configurar el ID de conversación único para este usuario
    config = {"configurable": {"thread_id": user_id}}
    
    # Preparar el mensaje de entrada
    input_state = {
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id,
        "context": {},
        "session": {}
    }
    
    # Invocar el agente
    result = trainer_agent.invoke(input_state, config)
    
    # Extraer los mensajes de respuesta
    response_messages = []
    for msg in result["messages"]:
        # CAMBIAR ESTA PARTE: Verificar el tipo de mensaje correctamente
        if hasattr(msg, "type") and msg.type == "ai":
            # Para AIMessages y mensajes del asistente
            response_messages.append({
                "role": "assistant",
                "content": msg.content
            })
        elif hasattr(msg, "type") and msg.type == "tool":
            # Para ToolMessages
            response_messages.append({
                "role": "tool",
                "content": msg.content
            })
        elif hasattr(msg, "role") and (msg.role == "assistant" or msg.role == "tool"):
            # Si el mensaje ya tiene atributos role y content
            response_messages.append({
                "role": msg.role,
                "content": msg.content
            })
    
    return response_messages