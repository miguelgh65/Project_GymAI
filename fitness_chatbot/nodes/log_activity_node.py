# fitness_chatbot/nodes/log_activity_node.py
import logging
import json
import re
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.schemas.prompt_schemas import LoggedExercise, LoggedNutrition
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager
from fitness_chatbot.core.services import FitnessDataService

# Importación de servicios del backend existente para mayor compatibilidad
try:
    from back_end.gym.services.database import insert_into_db
    from back_end.gym.services.prompt_service import format_for_postgres
    USE_LEGACY_SERVICES = True
except ImportError:
    USE_LEGACY_SERVICES = False

logger = logging.getLogger("fitness_chatbot")

async def log_activity(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa y registra actividades (ejercicios, comidas, etc.) en la base de datos.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- REGISTRO DE ACTIVIDAD INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    # Detectar si es un ejercicio o una comida directamente para decidir la estrategia
    is_likely_exercise = any(word in query.lower() for word in ["ejercicio", "press", "sentadilla", "serie", "repeticion", "peso", "kg", "entrenamiento", "cardio"])
    is_likely_nutrition = any(word in query.lower() for word in ["comida", "desayuno", "almuerzo", "cena", "calorías", "proteína", "carbohidratos", "grasas", "comí", "aliment"])
    
    if is_likely_exercise and USE_LEGACY_SERVICES:
        # Usar el formato existente para ejercicios
        logger.info("Detectado posible registro de ejercicio, usando servicio legacy")
        try:
            formatted_json = format_for_postgres(query)
            if formatted_json:
                success = insert_into_db(formatted_json, user_id)
                if success:
                    # Actualizar estado
                    message = f"¡He registrado tu ejercicio correctamente!"
                    agent_state["generation"] = message
                    memory_state["messages"].append({"role": "assistant", "content": message})
                    logger.info(f"Ejercicio registrado con éxito mediante servicio legacy para usuario {user_id}")
                    return agent_state, memory_state
        except Exception as e:
            logger.warning(f"Error al usar servicio legacy para registrar ejercicio: {e}")
            # Continuar con flujo normal si falla
    
    # Obtener mensajes de prompt para extracción de actividad
    messages = PromptManager.get_prompt_messages("log_activity", query=query)
    
    # Obtener LLM
    llm = get_llm()
    
    try:
        # Invocar LLM para extraer datos estructurados
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        # Extraer JSON de la respuesta
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        
        if json_match:
            activity_data = json.loads(json_match.group(1))
        else:
            # Intentar parsear directamente
            activity_data = json.loads(content)
        
        # Extraer el tipo de actividad
        activity_type = activity_data.get("type", "unknown").lower()
        
        # Procesar según el tipo de actividad
        success = False
        message = "No he podido procesar tu solicitud de registro."
        
        if activity_type == "exercise":
            # Registrar ejercicio
            exercise_name = activity_data.get("exercise_name")
            sets = activity_data.get("sets", [])
            
            if exercise_name and sets:
                # Convertir sets al formato esperado por la BD
                formatted_sets = []
                for s in sets:
                    formatted_sets.append({
                        "repeticiones": s.get("reps", 0),
                        "peso": s.get("weight", 0)
                    })
                
                # Registrar en la BD
                result = await FitnessDataService.log_exercise(
                    user_id=user_id,
                    exercise_name=exercise_name,
                    repetitions=formatted_sets
                )
                
                if result:
                    success = True
                    message = f"¡He registrado tu ejercicio de {exercise_name} correctamente!"
        
        elif activity_type == "nutrition":
            # Registrar comida
            meal_type = activity_data.get("meal_type", "")
            foods = activity_data.get("foods", [])
            calories = activity_data.get("calories")
            protein = activity_data.get("protein")
            
            if meal_type and (foods or calories):
                # Registrar en la BD
                result = await FitnessDataService.log_nutrition(
                    user_id=user_id,
                    meal_type=meal_type,
                    foods=foods,
                    calories=calories,
                    protein=protein
                )
                
                if result:
                    success = True
                    message = f"¡He registrado tu {meal_type} correctamente!"
        
        # Generar respuesta
        if not success:
            # Mensaje de error más detallado
            message = "No pude registrar tu actividad. Asegúrate de incluir todos los detalles necesarios."
        
        # Actualizar estado
        agent_state["generation"] = message
        
        # Actualizar historial de mensajes
        memory_state["messages"].append({"role": "assistant", "content": message})
        
        logger.info(f"Registro de actividad completado: {success}")
        
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error al registrar actividad: {str(e)}")
        agent_state["generation"] = "Lo siento, ocurrió un error al intentar registrar tu actividad. ¿Podrías intentarlo de nuevo con más detalles?"
        memory_state["messages"].append({"role": "assistant", "content": agent_state["generation"]})
    
    logger.info("--- REGISTRO DE ACTIVIDAD FINALIZADO ---")
    
    return agent_state, memory_state

# Función auxiliar para integración con APIs externas
async def extract_activity_data(text: str) -> Dict[str, Any]:
    """
    Extrae datos estructurados de una descripción de actividad.
    Útil para APIs que necesitan parsear texto en formato estructurado.
    
    Args:
        text: Texto con la descripción de la actividad
        
    Returns:
        Dict con datos estructurados de la actividad o None si hay error
    """
    try:
        # Obtener mensajes de prompt para extracción de actividad
        messages = PromptManager.get_prompt_messages("log_activity", query=text)
        
        # Obtener LLM
        llm = get_llm()
        
        # Invocar LLM para extraer datos estructurados
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        # Extraer JSON de la respuesta
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(1))
        else:
            # Intentar parsear directamente
            return json.loads(content)
    except Exception as e:
        logger.error(f"Error al extraer datos de actividad: {str(e)}")
        return None

# Función para registrar ejercicio usando el formato existente
async def register_exercise_legacy(user_id: str, exercise_text: str) -> Dict[str, Any]:
    """
    Registra un ejercicio usando el sistema existente.
    
    Args:
        user_id: ID del usuario
        exercise_text: Texto con la descripción del ejercicio
        
    Returns:
        Dict con resultado del registro
    """
    if not USE_LEGACY_SERVICES:
        return {"success": False, "message": "Servicios legacy no disponibles"}
    
    try:
        formatted_json = format_for_postgres(exercise_text)
        if not formatted_json:
            return {
                "success": False,
                "message": "No se pudo interpretar la descripción del ejercicio"
            }
        
        success = insert_into_db(formatted_json, user_id)
        
        if success:
            return {
                "success": True,
                "message": "Ejercicio registrado correctamente"
            }
        else:
            return {
                "success": False,
                "message": "Error al registrar el ejercicio en la base de datos"
            }
    except Exception as e:
        logger.error(f"Error al registrar ejercicio con formato legacy: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }