# fitness_chatbot/nodes/routine_analyzer_node.py
import logging
from typing import Tuple, Dict, Any

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.utils.api_utils import get_exercise_data
from fitness_chatbot.configs.llm_config import get_llm

logger = logging.getLogger("fitness_chatbot")

async def analyze_routine(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Analiza la rutina del usuario utilizando IA.
    Este nodo simplemente obtiene los datos y se los pasa directamente al LLM
    para que la IA haga todo el análisis.
    """
    logger.info("--- ANÁLISIS DE RUTINA INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Analizando rutina para usuario {user_id}: '{query}'")
    
    try:
        # Obtener el token de autenticación del contexto del usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        
        # Obtener datos de ejercicios de los últimos 30 días
        exercise_data = get_exercise_data(user_id, days=30, auth_token=auth_token)
        
        if not exercise_data.get("success", False) or not exercise_data.get("logs", []):
            logger.warning("No se pudieron obtener datos de ejercicios o no hay registros")
            respuesta = "No pude encontrar suficientes datos de ejercicios en tu historial. Para poder analizar tu rutina, necesito que registres tus entrenamientos durante al menos una semana. ¿Puedo ayudarte a registrar algún ejercicio que hayas hecho recientemente?"
        else:
            # Crear un sistema de prompt para el LLM con instrucciones específicas
            system_prompt = """Eres un entrenador personal experto en analizar rutinas de entrenamiento.
            Recibirás datos de ejercicios del usuario y tu tarea es analizarlos para detectar
            desequilibrios, áreas descuidadas y oportunidades de mejora.
            
            Sigue estas instrucciones:
            1. Identifica qué grupos musculares está entrenando (pecho, espalda, piernas, etc.)
            2. Detecta desequilibrios entre grupos antagonistas (ej. mucho pecho, poca espalda)
            3. Identifica grupos musculares descuidados u olvidados
            4. Analiza la frecuencia de entrenamiento por grupo muscular
            5. Sugiere ejercicios específicos para mejorar la rutina
            6. Da recomendaciones basadas en principios científicos
            7. Sé específico y detallado, pero mantén un tono motivador
            
            Formato de respuesta:
            - Comienza con un breve resumen del análisis
            - Incluye secciones específicas para cada punto importante
            - Utiliza una estructura clara con subtítulos
            - Termina con recomendaciones concretas"""
            
            # Preparar datos para el LLM
            logs = exercise_data.get("logs", [])
            # Crear un formato simplificado para que sea más fácil para la IA
            formatted_logs = []
            for log in logs:
                fecha = log.get("fecha", "")
                if isinstance(fecha, str) and len(fecha) > 10:
                    fecha = fecha[:10]
                    
                ejercicio = log.get("ejercicio", "desconocido")
                repeticiones = log.get("repeticiones", [])
                
                if isinstance(repeticiones, str):
                    try:
                        import json
                        repeticiones = json.loads(repeticiones)
                    except:
                        repeticiones = []
                
                # Crear resumen legible
                resumen_series = []
                for serie in repeticiones:
                    if isinstance(serie, dict):
                        reps = serie.get("repeticiones", 0)
                        peso = serie.get("peso", 0)
                        resumen_series.append(f"{reps} reps x {peso}kg")
                
                formatted_logs.append({
                    "fecha": fecha,
                    "ejercicio": ejercicio,
                    "series": resumen_series if resumen_series else "Sin datos de series"
                })
            
            # Ordenar por fecha
            formatted_logs.sort(key=lambda x: x["fecha"], reverse=True)
            
            # Convertir a formato de texto para el LLM
            logs_text = "HISTORIAL DE EJERCICIOS:\n\n"
            for log in formatted_logs:
                logs_text += f"Fecha: {log['fecha']}\n"
                logs_text += f"Ejercicio: {log['ejercicio']}\n"
                
                if isinstance(log['series'], list):
                    logs_text += "Series:\n"
                    for idx, serie in enumerate(log['series'], 1):
                        logs_text += f"  - Serie {idx}: {serie}\n"
                else:
                    logs_text += f"Series: {log['series']}\n"
                
                logs_text += "\n"
            
            # Añadir la consulta original del usuario
            user_message = f"""
            Analiza mi rutina de entrenamiento:
            
            {query}
            
            Aquí está mi historial de ejercicios recientes:
            
            {logs_text}
            """
            
            # Preparar mensajes para el LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Invocar el LLM
            llm = get_llm()
            if llm is None:
                logger.error("LLM no inicializado correctamente")
                respuesta = "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta más tarde."
            else:
                response = await llm.ainvoke(messages)
                respuesta = response.content if hasattr(response, 'content') else str(response)
    
    except Exception as e:
        logger.exception(f"Error analizando rutina: {str(e)}")
        respuesta = "Lo siento, tuve un problema al analizar tu rutina. ¿Podrías intentar preguntarme de otra manera?"
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- ANÁLISIS DE RUTINA FINALIZADO ---")
    return agent_state, memory_state