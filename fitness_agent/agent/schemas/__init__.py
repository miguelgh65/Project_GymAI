# fitness_agent/agent/schemas/__init__.py
from .agent_roles import (AgentCapability, AgentProfile, AgentRegistry,
                          AgentRole, FitnessCoachAgent, NutritionAdvisorAgent,
                          SystemAgent, UserAgent, initialize_default_agents)
from .agent_schemas import *
from .exercise_schemas import *
from .fitbit_schemas import *
from .nutrition_schemas import *

# Inicializar agentes por defecto al importar el módulo
initialize_default_agents()

# Exportar todos los tipos para facilitar la importación
__all__ = [
    # Roles de agentes
    'AgentRole',
    'AgentCapability',
    'AgentProfile',
    'SystemAgent',
    'UserAgent',
    'FitnessCoachAgent',
    'NutritionAdvisorAgent',
    'AgentRegistry',
    'initialize_default_agents',
    
    # Schemas de mensajes y respuestas
    'MessageRole',
    'Message',
    'UserQuery',
    'NodeType',
    'AgentResponse',
    'TraceMetadata'
]