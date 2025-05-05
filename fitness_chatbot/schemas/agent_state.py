# fitness_chatbot/schemas/agent_state.py

from typing import Dict, Any, List, Optional, TypedDict
from enum import Enum

# Define intent types as constants for better type safety
class IntentType:
    EXERCISE = "exercise"       # Consultas sobre ejercicios
    NUTRITION = "nutrition"     # Consultas sobre nutrición
    PROGRESS = "progress"       # Consultas sobre evolución y tendencias
    HISTORY = "history"         # Consultas sobre historial de ejercicios
    LOG_ACTIVITY = "log_activity"  # Registrar actividad (ejercicio, comida, etc.)
    FITBIT = "fitbit"           # Consultas sobre datos de Fitbit
    TODAY_ROUTINE = "today_routine"  # Consulta sobre rutina del día actual
    EDIT_ROUTINE = "edit_routine"    # Modificar rutina existente
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