# fitness_agent/agent/chains/fitness_workflow.py
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig

from fitness_agent.schemas.agent_state import AgentState, AgentIntentType
from fitness_agent.agent.nodes.router_node import determine_intent
from fitness_agent.agent.chains.exercise_chain import ExerciseChain
from fitness_agent.agent.chains.nutrition_chain import NutritionChain
from fitness_agent.agent.chains.progress_chain import ProgressChain

class FitnessWorkflow:
    def __init__(self, user_id: str):
        """
        Inicializa el workflow principal de fitness.
        
        Args:
            user_id: ID del usuario para el cual se crea el flujo
        """
        self.user_id = user_id
        self.workflow = self._create_fitness_workflow()
    
    def _create_fitness_workflow(self) -> StateGraph:
        """
        Crea el grafo de estado para el flujo principal de fitness.
        
        Returns:
            Grafo de estado configurado
        """
        workflow = StateGraph(AgentState)
        
        # Añadir nodos para cada tipo de intención
        workflow.add_node("start", self._route_intent)
        workflow.add_node("exercise", self._run_exercise_chain)
        workflow.add_node("nutrition", self._run_nutrition_chain)
        workflow.add_node("progress", self._run_progress_chain)
        workflow.add_node("fallback", self._run_fallback)
        
        # Definir las transiciones
        workflow.add_edge("start", {
            AgentIntentType.EXERCISE: "exercise",
            AgentIntentType.NUTRITION: "nutrition",
            AgentIntentType.PROGRESS: "progress",
            AgentIntentType.GENERAL: "fallback"
        })
        
        # Todos los nodos especializados convergen al final
        workflow.add_edge("exercise", END)
        workflow.add_edge("nutrition", END)
        workflow.add_edge("progress", END)
        workflow.add_edge("fallback", END)
        
        # Punto de entrada
        workflow.set_entry_point("start")
        
        return workflow.compile()
    
    def _route_intent(self, state: AgentState) -> Dict[str, Any]:
        """
        Determina la intención del mensaje.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado con la intención
        """
        last_message = state['messages'][-1]['content']
        intent_response = determine_intent(last_message)
        
        return {
            **state,
            "intent": intent_response.intent
        }
    
    def _run_exercise_chain(self, state: AgentState) -> Dict[str, Any]:
        """
        Ejecuta la cadena de ejercicios.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado
        """
        exercise_chain = ExerciseChain(self.user_id)
        result = exercise_chain.invoke(state['messages'][-1]['content'])
        
        return {
            **state,
            "messages": state['messages'] + result.get('messages', [])
        }
    
    def _run_nutrition_chain(self, state: AgentState) -> Dict[str, Any]:
        """
        Ejecuta la cadena de nutrición.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado
        """
        nutrition_chain = NutritionChain(self.user_id)
        result = nutrition_chain.invoke(state['messages'][-1]['content'])
        
        return {
            **state,
            "messages": state['messages'] + result.get('messages', [])
        }
    
    def _run_progress_chain(self, state: AgentState) -> Dict[str, Any]:
        """
        Ejecuta la cadena de progreso.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado
        """
        progress_chain = ProgressChain(self.user_id)
        result = progress_chain.invoke(state['messages'][-1]['content'])
        
        return {
            **state,
            "messages": state['messages'] + result.get('messages', [])
        }
    
    def _run_fallback(self, state: AgentState) -> Dict[str, Any]:
        """
        Maneja consultas generales o no clasificadas.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado
        """
        fallback_message = {
            "role": "assistant",
            "content": "Lo siento, no pude procesar completamente tu solicitud. ¿Podrías ser más específico?"
        }
        
        return {
            **state,
            "messages": state['messages'] + [fallback_message]
        }
    
    def invoke(self, input_message: str, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Invoca el flujo de fitness completo con un mensaje de entrada.
        
        Args:
            input_message: Mensaje del usuario
            config: Configuración opcional de ejecución
        
        Returns:
            Resultado final del flujo
        """
        initial_state = AgentState(
            messages=[{"role": "user", "content": input_message}],
            user_id=self.user_id,
            context={},
            intent="general"
        )
        
        return self.workflow.invoke(initial_state, config)

# Función de utilidad para crear y ejecutar el workflow
def create_fitness_workflow(user_id: str, message: str):
    """
    Función de utilidad para crear y ejecutar un flujo de fitness.
    
    Args:
        user_id: ID del usuario
        message: Mensaje de entrada
    
    Returns:
        Resultado del flujo de fitness
    """
    fitness_workflow = FitnessWorkflow(user_id)
    return fitness_workflow.invoke(message)