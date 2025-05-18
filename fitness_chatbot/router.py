from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse


from fitness_chatbot.schemas.api_schemas import ChatRequest, ChatResponse
from fitness_chatbot.graphs.fitness_graph import create_fitness_graph
from fitness_chatbot.schemas.agent_state import AgentState, MemoryState
from fitness_chatbot.core.services import FitnessDataService
from back_end.gym.middlewares import get_current_user

# Crear el grafo una sola vez al iniciar
fitness_graph = create_fitness_graph()

router = APIRouter(
    prefix="/api/chatbot",
    tags=["chatbot"]
)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    user = Depends(get_current_user)
):
    """Endpoint principal para conversaciones con el chatbot de fitness"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado"
        )
    
    try:
        # Obtener ID de usuario para consultar datos
        user_id = str(user.get('id'))
        
        # Crear estado inicial para el grafo
        initial_state = AgentState(
            query=request.message,
            intent="",
            user_id=user_id,
            user_context={},
            intermediate_steps=[],
            retrieved_data=[],
            generation=""
        )
        
        # Crear estado de memoria
        memory_state = MemoryState(
            messages=[]
        )
        
        # Si hay contexto en la solicitud, añadirlo al estado
        if request.context:
            initial_state["user_context"].update(request.context)
        
        # Ejecutar el grafo
        final_state = await fitness_graph.ainvoke((initial_state, memory_state))
        
        # Extraer los estados finales
        final_agent_state, final_memory_state = final_state
        
        # Obtener la respuesta generada
        response_content = final_agent_state.get("generation", "")
        
        return ChatResponse(
            response=response_content,
            intent=final_agent_state.get("intent", "general")
        )
    
    except Exception as e:
        # Log the error
        print(f"Error en endpoint de chatbot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando la solicitud: {str(e)}"
        )