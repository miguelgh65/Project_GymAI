from typing import Dict, Any, List, Optional, TypedDict

# Definir tipos de intención
class IntentType:
    EXERCISE = "exercise"       # Consultas sobre ejercicios
    NUTRITION = "nutrition"     # Consultas sobre nutrición
    PROGRESS = "progress"       # Consultas sobre progreso
    LOG_ACTIVITY = "log_activity"  # Registrar actividad (ejercicio, comida, etc.)
    GENERAL = "general"         # Consultas generales/fallback

# Estado principal del agente
class AgentState(TypedDict):
    """Estado principal del grafo de fitness"""
    # Entrada y clasificación
    query: str                   # Consulta original del usuario
    intent: str                  # Intención detectada
    
    # Datos intermedios y contexto
    user_id: str                 # ID del usuario
    user_context: Dict[str, Any] # Contexto del usuario (datos de BD, etc)
    intermediate_steps: List[Dict[str, Any]]  # Pasos intermedios
    retrieved_data: List[Dict[str, Any]]  # Datos recuperados para RAG
    
    # Respuesta generada
    generation: str             # Respuesta generada para el usuario