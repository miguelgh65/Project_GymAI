# fitness_agent/agent/chains/nutrition_chain.py
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from fitness_agent.schemas.agent_state import AgentState
from fitness_agent.agent.utils.llm_utils import get_llm, format_llm_response
from fitness_agent.agent.utils.prompt_utils import get_formatted_prompt

class NutritionChain:
    def __init__(self, user_id: str):
        """
        Inicializa la cadena de nutrición.
        
        Args:
            user_id: ID del usuario para el cual se crea el flujo
        """
        self.user_id = user_id
        self.workflow = self._create_nutrition_workflow()
    
    def _create_nutrition_workflow(self) -> StateGraph:
        """
        Crea el grafo de estado para el flujo de nutrición.
        
        Returns:
            Grafo de estado configurado
        """
        workflow = StateGraph(AgentState)
        
        # Añadir nodos
        workflow.add_node("start", self._prepare_nutrition_analysis)
        workflow.add_node("end", self._prepare_final_response)
        
        # Definir conexiones
        workflow.add_edge("start", "end")
        workflow.set_entry_point("start")
        workflow.set_finish_point("end")
        
        return workflow.compile()
    
    def _prepare_nutrition_analysis(self, state: AgentState) -> Dict[str, Any]:
        """
        Prepara el análisis nutricional usando LLM.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado con contexto de análisis
        """
        # Obtener mensaje del usuario
        last_message = state['messages'][-1]['content']
        
        # Obtener prompt de sistema
        system_prompt = get_formatted_prompt(
            "nutrition", 
            "system", 
            user_context="Sin datos nutricionales específicos"
        )
        
        # Obtener instancia de LLM
        llm = get_llm()
        
        # Preparar mensajes para el LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message}
        ]
        
        # Generar respuesta
        response = llm.invoke(messages)
        analysis_result = format_llm_response(response.content)
        
        return {
            **state,
            "context": {
                "analysis": analysis_result
            }
        }
    
    def _prepare_final_response(self, state: AgentState) -> Dict[str, Any]:
        """
        Prepara la respuesta final para el usuario.
        
        Args:
            state: Estado final del agente
        
        Returns:
            Estado con mensaje de respuesta final
        """
        # Formatear el resultado del análisis para el usuario
        analysis_result = state['context'].get('analysis', '')
        
        # Crear mensaje de respuesta
        response_message = {
            "role": "assistant",
            "content": analysis_result or "No pude procesar completamente tu consulta nutricional."
        }
        
        return {
            **state,
            "messages": state['messages'] + [response_message]
        }
    
    def invoke(self, input_message: str, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Invoca el flujo de nutrición con un mensaje de entrada.
        
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
            intent="nutrition"
        )
        
        return self.workflow.invoke(initial_state, config)

# Función de utilidad para crear y ejecutar un flujo de nutrición
def create_nutrition_workflow(user_id: str, message: str):
    """
    Función de utilidad para crear y ejecutar un flujo de nutrición.
    
    Args:
        user_id: ID del usuario
        message: Mensaje de entrada
    
    Returns:
        Resultado del flujo de nutrición
    """
    nutrition_chain = NutritionChain(user_id)
    return nutrition_chain.invoke(message)