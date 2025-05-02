# fitness_chatbot/nodes/log_activity_node.py
import logging
import json
import re
from typing import Tuple, Dict, Any, List
from datetime import datetime

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

# Importación de servicios del backend existente para mayor compatibilidad
try:
    from back_end.gym.services.database import insert_into_db
    from back_end.gym.services.prompt_service import format_for_postgres
    USE_LEGACY_SERVICES = True
    logger = logging.getLogger("fitness_chatbot")
    logger.info("✅ Servicios legacy para ejercicios disponibles")
except ImportError:
    # Si no podemos importar los servicios legacy, usamos nuestro propio stub
    def format_for_postgres(exercise_text):
        logger.warning(f"Usando stub para format_for_postgres: {exercise_text}")
        return extract_exercise_data(exercise_text)
    
    def insert_into_db(json_data, user_id):
        logger.warning(f"Usando stub para insert_into_db. Datos: {json_data}, user_id: {user_id}")
        return False
    
    USE_LEGACY_SERVICES = False
    logger = logging.getLogger("fitness_chatbot")
    logger.warning("⚠️ Servicios legacy para ejercicios NO disponibles, usando stubs")

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
    
    logger.info(f"Procesando solicitud de registro: '{query}'")
    
    # ESTRATEGIA 1: Usar el servicio legacy existente
    if USE_LEGACY_SERVICES:
        try:
            logger.info("Intentando usar format_for_postgres")
            # Esto es crítico: usar format_for_postgres del servicio existente
            formatted_json = format_for_postgres(query)
            
            if formatted_json:
                logger.info(f"format_for_postgres devolvió: {formatted_json}")
                
                # Insertar en la base de datos
                success = insert_into_db(formatted_json, user_id)
                
                if success:
                    # Si el registro fue exitoso, devolver respuesta positiva
                    message = f"¡He registrado tu ejercicio de {formatted_json.get('ejercicio', 'desconocido')} correctamente!"
                    agent_state["generation"] = message
                    memory_state["messages"].append({"role": "assistant", "content": message})
                    logger.info("✅ Ejercicio registrado con éxito mediante servicio legacy")
                    return agent_state, memory_state
                else:
                    logger.warning("❌ insert_into_db falló")
            else:
                logger.warning("❌ format_for_postgres devolvió None")
        except Exception as e:
            logger.error(f"❌ Error al usar servicio legacy: {e}")
    
    # ESTRATEGIA 2: Usar LLM para extracción estructurada
    try:
        logger.info("Intentando usar LLM para extracción estructurada")
        
        # Obtener mensajes de prompt para extracción de actividad
        messages = PromptManager.get_prompt_messages("log_activity", query=query)
        
        # Obtener LLM
        llm = get_llm()
        
        # Invocar LLM para extraer datos estructurados
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        logger.info(f"LLM devolvió: {content[:100]}...")
        
        # Extraer JSON de la respuesta
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        
        if json_match:
            activity_data = json.loads(json_match.group(1))
        else:
            # Intentar parsear directamente
            try:
                activity_data = json.loads(content)
            except json.JSONDecodeError:
                logger.warning("❌ No se pudo extraer JSON de la respuesta LLM")
                activity_data = None
        
        if activity_data:
            logger.info(f"Datos extraídos por LLM: {activity_data}")
            
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
                    
                    # Preparar JSON para insert_into_db
                    formatted_json = {
                        "ejercicio": exercise_name,
                        "repeticiones": formatted_sets,
                        "fecha": datetime.now().isoformat()
                    }
                    
                    if USE_LEGACY_SERVICES:
                        # Usar servicio legacy para insertar
                        success = insert_into_db(formatted_json, user_id)
                    else:
                        # Aquí implementaríamos nuestra propia lógica de inserción
                        # Por ahora, simulamos fallo para que se prueben otras estrategias
                        logger.warning("No hay implementación propia para insertar ejercicios")
                        success = False
                    
                    if success:
                        message = f"¡He registrado tu ejercicio de {exercise_name} correctamente!"
                        logger.info("✅ Ejercicio registrado con éxito mediante LLM")
            
            # Generar respuesta
            if success:
                agent_state["generation"] = message
                memory_state["messages"].append({"role": "assistant", "content": message})
                return agent_state, memory_state
    
    except Exception as e:
        logger.error(f"❌ Error en estrategia LLM: {e}")
    
    # ESTRATEGIA 3: Extraer manualmente con regex
    try:
        logger.info("Intentando extracción manual de datos del ejercicio")
        
        # Extraer datos del ejercicio
        exercise_data = extract_exercise_data(query)
        
        if exercise_data:
            logger.info(f"Datos extraídos manualmente: {exercise_data}")
            
            # Convertir al formato esperado por la BD e intentar insertar
            if USE_LEGACY_SERVICES:
                success = insert_into_db(exercise_data, user_id)
            else:
                # Aquí implementaríamos nuestra propia lógica de inserción
                logger.warning("No hay implementación propia para insertar ejercicios")
                success = False
            
            if success:
                message = f"¡He registrado tu ejercicio de {exercise_data.get('ejercicio', 'desconocido')} correctamente!"
                agent_state["generation"] = message
                memory_state["messages"].append({"role": "assistant", "content": message})
                logger.info("✅ Ejercicio registrado con éxito mediante extracción manual")
                return agent_state, memory_state
    
    except Exception as e:
        logger.error(f"❌ Error en extracción manual: {e}")
    
    # Si llegamos aquí, todas las estrategias fallaron
    message = "Lo siento, no pude registrar tu actividad. Por favor, intenta ser más específico, por ejemplo: 'Press banca 3 series de 10 repeticiones con 60kg'."
    agent_state["generation"] = message
    memory_state["messages"].append({"role": "assistant", "content": message})
    logger.warning("❌ Todas las estrategias de registro fallaron")
    
    logger.info("--- REGISTRO DE ACTIVIDAD FINALIZADO ---")
    
    return agent_state, memory_state

def extract_exercise_data(text: str) -> Dict[str, Any]:
    """
    Extrae datos estructurados de ejercicio de texto en formato adecuado para la BD.
    
    Args:
        text: Texto con descripción del ejercicio
        
    Returns:
        Dict con datos estructurados del ejercicio para la BD
    """
    try:
        # Nombres comunes de ejercicios
        exercise_names = [
            "press banca", "press de banca", "banca", "sentadilla", "squad", "peso muerto", 
            "dominadas", "dominada", "pull up", "press militar", "militar", "curl", 
            "curl biceps", "fondos", "elevaciones laterales", "laterales", 
            "remo", "extensiones", "extensión", "triceps", "jalon", "jalón",
            "prensa", "hip thrust", "flexiones", "pushups"
        ]
        
        # Buscar el ejercicio en el texto
        exercise_name = None
        for name in exercise_names:
            if name in text.lower():
                exercise_name = name
                break
        
        if not exercise_name:
            # Si no encontramos un nombre específico, usar regex genérico
            exercise_match = re.search(r'([a-záéíóúñ\s]+)(?:he hecho|hice|realicé|de|con|a)', text.lower())
            if exercise_match:
                exercise_name = exercise_match.group(1).strip()
        
        # Si aún no tenemos nombre, buscar la primera palabra que no sea un número
        if not exercise_name:
            words = text.lower().split()
            for word in words:
                if not re.match(r'^\d+$', word) and len(word) > 3:  # Palabras de más de 3 letras
                    exercise_name = word
                    break
        
        # Extraer series y repeticiones usando regex
        sets = []
        
        # Patrón 1: NxN (3x10) o NxNxN (3x10x60)
        set_pattern1 = re.findall(r'(\d+)\s*[xX]\s*(\d+)(?:\s*[xX]\s*(\d+))?', text)
        for match in set_pattern1:
            if len(match) == 3 and match[2]:  # 3 grupos: series, reps, peso
                for _ in range(int(match[0])):
                    sets.append({"repeticiones": int(match[1]), "peso": float(match[2])})
            elif len(match) >= 2:  # Puede ser repsxpeso
                sets.append({"repeticiones": int(match[0]), "peso": float(match[1])})
        
        # Patrón 2: N series de N
        set_pattern2 = re.findall(r'(\d+)\s*series\s*(?:de)?\s*(\d+)(?:\s*(?:con)?\s*(\d+)\s*kg)?', text)
        for match in set_pattern2:
            num_sets = int(match[0])
            reps = int(match[1])
            weight = float(match[2]) if match[2] else 0
            for _ in range(num_sets):
                sets.append({"repeticiones": reps, "peso": weight})
        
        # Patrón 3: Repeticiones con peso
        set_pattern3 = re.findall(r'(\d+)\s*(?:reps|repeticiones)(?:\s*(?:con|a)?\s*(\d+)\s*kg)?', text)
        for match in set_pattern3:
            reps = int(match[0])
            weight = float(match[1]) if len(match) > 1 and match[1] else 0
            sets.append({"repeticiones": reps, "peso": weight})
        
        # Patrón 4: Detector de múltiples conjuntos (10x20, 10x20 y 10x60)
        multi_set_pattern = re.findall(r'(\d+)\s*[xX]\s*(\d+)', text)
        if multi_set_pattern and 'y' in text:
            # Esto podría indicar múltiples conjuntos enumerados
            # Ya se procesan en el patrón 1, solo verificamos por claridad
            pass
        
        # Si no detectamos series específicas pero hay números, asumimos repeticiones
        if not sets:
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:  # Al menos 2 números (reps y peso)
                try:
                    sets.append({"repeticiones": int(numbers[0]), "peso": float(numbers[1])})
                except:
                    pass
        
        # Fallback para repeticiones sin peso
        if not sets:
            just_reps = re.findall(r'\b(\d+)\b', text)
            if just_reps:
                sets.append({"repeticiones": int(just_reps[0]), "peso": 0})
        
        # Si no hay sets pero hay ejercicio, usar valores por defecto
        if not sets and exercise_name:
            sets = [{"repeticiones": 10, "peso": 0}]
        
        # Validar datos extraídos
        if not exercise_name or not sets:
            logger.warning(f"Extracción insuficiente: ejercicio={exercise_name}, sets={sets}")
            return None
        
        # Devolver en formato correcto para la BD
        return {
            "ejercicio": exercise_name,
            "repeticiones": sets,
            "fecha": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error extrayendo datos de ejercicio: {e}")
        return None