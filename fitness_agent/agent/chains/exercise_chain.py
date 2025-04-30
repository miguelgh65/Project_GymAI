# fitness_agent/agent/chains/exercise_chain.py
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from fitness_agent.agent.nodes.exercise_node import get_user_exercise_context
from fitness_agent.agent.tools.exercise_tools import (
    get_exercise_stats, get_recent_exercises, recommend_exercise_progression)
from fitness_agent.agent.utils.llm_utils import format_llm_response, get_llm
from fitness_agent.agent.utils.prompt_utils import get_formatted_prompt
from fitness_agent.agent.utils.text_utils import extract_exercise_name
from fitness_agent.schemas.agent_state import AgentState


class ExerciseChain:
    def __init__(self, user_id: str):
        """
        Inicializa la cadena de ejercicios.
        
        Args:
            user_id: ID del usuario para el cual se crea el flujo
        """
        self.user_id = user_id
        self.workflow = self._create_exercise_workflow()
    
    def _create_exercise_workflow(self) -> StateGraph:
        """
        Crea el grafo de estado para el flujo de ejercicios.
        
        Returns:
            Grafo de estado configurado
        """
        workflow = StateGraph(AgentState)
        
        # Definir herramientas
        tools = {
            "get_recent_exercises": get_recent_exercises,
            "get_exercise_stats": get_exercise_stats,
            "recommend_exercise_progression": recommend_exercise_progression
        }
        tool_node = ToolNode(tools)
        
        # Añadir nodos
        workflow.add_node("start", self._extract_exercise_context)
        workflow.add_node("tools", tool_node)
        workflow.add_node("analysis", self._run_exercise_analysis)
        workflow.add_node("end", self._prepare_final_response)
        
        # Definir conexiones
        workflow.add_edge("start", "tools")
        workflow.add_edge("tools", "analysis")
        workflow.add_edge("analysis", "end")
        workflow.set_entry_point("start")
        workflow.set_finish_point("end")
        
        return workflow.compile()
    
    def _extract_exercise_context(self, state: AgentState) -> Dict[str, Any]:
        """
        Extrae el contexto inicial para el análisis de ejercicios.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado con información de contexto
        """
        # Extraer información del último mensaje
        last_message = state['messages'][-1]['content']
        
        # Intentar extraer nombre de ejercicio u otros detalles
        exercise_name = extract_exercise_name(last_message)
        
        # Obtener contexto general de ejercicios del usuario
        user_context = get_user_exercise_context(self.user_id)
        
        return {
            **state,
            "context": {
                "exercise_name": exercise_name,
                "user_id": self.user_id,
                "user_context": user_context
            }
        }
    
    def _run_exercise_analysis(self, state: AgentState) -> Dict[str, Any]:
        """
        Analiza la consulta de ejercicio usando herramientas y LLM.
        
        Args:
            state: Estado actual del agente
        
        Returns:
            Estado actualizado con resultados del análisis
        """
        context = state.get('context', {})
        exercise_name = context.get('exercise_name')
        user_context = context.get('user_context', '')
        
        # Obtener prompt para análisis de ejercicio
        system_prompt = get_formatted_prompt(
            "exercise", 
            "analysis", 
            exercise_name=exercise_name or "ejercicio",
            user_context=user_context
        )
        
        # Obtener instancia de LLM
        llm = get_llm()
        
        # Preparar mensajes para el LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state['messages'][-1]['content']}
        ]
        
        # Generar respuesta
        response = llm.invoke(messages)
        analysis_result = format_llm_response(response.content)
        
        return {
            **state,
            "context": {
                **context,
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
            "content": analysis_result or "No pude procesar completamente tu consulta sobre ejercicios."
        }
        
        return {
            **state,
            "messages": state['messages'] + [response_message]
        }
    
    def invoke(self, input_message: str, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Invoca el flujo de ejercicios con un mensaje de entrada.
        
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
            intent="exercise"
        )
        
        return self.workflow.invoke(initial_state, config)

# Función de utilidad para crear y ejecutar un flujo de ejercicios
def create_exercise_workflow(user_id: str, message: str):
    """
    Función de utilidad para crear y ejecutar un flujo de ejercicios.
    
    Args:
        user_id: ID del usuario
        message: Mensaje de entrada
    
    Returns:
        Resultado del flujo de ejercicios
    """
    exercise_chain = ExerciseChain(user_id)
    return exercise_chain.invoke(message)