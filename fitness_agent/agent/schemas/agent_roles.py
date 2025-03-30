# fitness_agent/agent/schemas/agent_roles.py
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AgentRole(str, Enum):
    """
    Roles de agentes en el sistema de fitness.
    """
    SYSTEM = "system"  # Agente de gestión y coordinación
    USER = "user"      # Agente que representa al usuario final
    FITNESS_COACH = "fitness_coach"  # Agente especializado en entrenamiento
    NUTRITION_ADVISOR = "nutrition_advisor"  # Agente especializado en nutrición
    DATA_ANALYST = "data_analyst"  # Agente para análisis de datos
    PROGRESS_TRACKER = "progress_tracker"  # Agente para seguimiento de progreso

class AgentCapability(str, Enum):
    """
    Capacidades específicas de los agentes.
    """
    EXERCISE_RECOMMENDATION = "exercise_recommendation"
    PROGRESS_ANALYSIS = "progress_analysis"
    NUTRITION_GUIDANCE = "nutrition_guidance"
    DATA_INTERPRETATION = "data_interpretation"
    GOAL_SETTING = "goal_setting"

class AgentProfile(BaseModel):
    """
    Perfil detallado de un agente en el sistema.
    """
    id: str = Field(..., description="Identificador único del agente")
    name: str = Field(..., description="Nombre del agente")
    role: AgentRole = Field(..., description="Rol principal del agente")
    capabilities: List[AgentCapability] = Field(
        default_factory=list, 
        description="Capacidades específicas del agente"
    )
    description: Optional[str] = Field(
        default=None, 
        description="Descripción detallada del agente"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Contexto adicional del agente"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="Timestamp de creación del perfil"
    )

class SystemAgent(AgentProfile):
    """
    Agente de sistema con capacidades de gestión y coordinación.
    """
    role: AgentRole = AgentRole.SYSTEM
    capabilities: List[AgentCapability] = [
        AgentCapability.DATA_INTERPRETATION,
        AgentCapability.GOAL_SETTING
    ]

class UserAgent(AgentProfile):
    """
    Agente que representa al usuario final.
    """
    role: AgentRole = AgentRole.USER
    capabilities: List[AgentCapability] = []

class FitnessCoachAgent(AgentProfile):
    """
    Agente especializado en entrenamiento y ejercicios.
    """
    role: AgentRole = AgentRole.FITNESS_COACH
    capabilities: List[AgentCapability] = [
        AgentCapability.EXERCISE_RECOMMENDATION,
        AgentCapability.PROGRESS_ANALYSIS
    ]

class NutritionAdvisorAgent(AgentProfile):
    """
    Agente especializado en nutrición y dieta.
    """
    role: AgentRole = AgentRole.NUTRITION_ADVISOR
    capabilities: List[AgentCapability] = [
        AgentCapability.NUTRITION_GUIDANCE
    ]

class AgentRegistry:
    """
    Registro y gestión de agentes en el sistema.
    """
    _agents: Dict[str, AgentProfile] = {}

    @classmethod
    def register_agent(cls, agent: AgentProfile):
        """
        Registra un nuevo agente en el sistema.
        
        Args:
            agent: Perfil del agente a registrar
        """
        cls._agents[agent.id] = agent
    
    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[AgentProfile]:
        """
        Obtiene un agente por su ID.
        
        Args:
            agent_id: ID del agente
        
        Returns:
            Perfil del agente o None si no se encuentra
        """
        return cls._agents.get(agent_id)
    
    @classmethod
    def list_agents_by_role(cls, role: AgentRole) -> List[AgentProfile]:
        """
        Lista todos los agentes de un rol específico.
        
        Args:
            role: Rol a buscar
        
        Returns:
            Lista de agentes con ese rol
        """
        return [agent for agent in cls._agents.values() if agent.role == role]

def initialize_default_agents():
    """
    Inicializa agentes predeterminados en el sistema.
    """
    AgentRegistry.register_agent(SystemAgent(
        id="system_coordinator",
        name="Coordinador de Sistema",
        description="Agente principal de coordinación y gestión"
    ))
    
    AgentRegistry.register_agent(FitnessCoachAgent(
        id="fitness_coach_primary",
        name="Entrenador Personal AI",
        description="Asistente especializado en entrenamiento y progreso físico"
    ))
    
    AgentRegistry.register_agent(NutritionAdvisorAgent(
        id="nutrition_advisor_primary",
        name="Asesor Nutricional AI",
        description="Especialista en guía nutricional y planes de alimentación"
    ))

# Inicializar agentes al importar el módulo
initialize_default_agents()