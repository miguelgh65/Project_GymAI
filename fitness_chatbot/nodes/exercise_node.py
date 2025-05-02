# fitness_chatbot/nodes/exercise_node.py - Versión simple con llamada a API
import logging
import requests
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm

logger = logging.getLogger("fitness_chatbot")

# URL base para la API - Conexión local dentro del mismo contenedor
API_BASE_URL = "http://127.0.0.1:5050"

async def process_exercise_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """Procesa consultas sobre ejercicios llamando al endpoint correspondiente."""
    logger.info("--- PROCESANDO CONSULTA DE EJERCICIO ---")
    
    agent_state, memory_state = states
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Consulta: '{query}' para usuario {user_id}")
    
    # Detectar si es consulta sobre ejercicio específico
    ejercicio = None
    query_lower = query.lower()
    
    if "press banca" in query_lower or "press de banca" in query_lower:
        ejercicio = "press banca"
    elif "sentadilla" in query_lower:
        ejercicio = "sentadillas"
    elif "peso muerto" in query_lower:
        ejercicio = "peso muerto"
    elif "dominada" in query_lower:
        ejercicio = "dominadas"
    elif "curl" in query_lower or "bíceps" in query_lower or "biceps" in query_lower:
        ejercicio = "curl de bíceps"
    
    if ejercicio:
        logger.info(f"Ejercicio '{ejercicio}' detectado en la consulta")
    
    try:
        # Si es consulta por último ejercicio, usar endpoint de logs
        if ("último" in query_lower or "ultimo" in query_lower or "reciente" in query_lower or 
            "dame" in query_lower or "muestra" in query_lower):
            
            # Elegir el endpoint según si se pregunta por un ejercicio específico
            if ejercicio:
                # Fechas para filtrado (último mes)
                fecha_hasta = datetime.now().strftime("%Y-%m-%d")
                fecha_desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                
                url = f"{API_BASE_URL}/api/ejercicios_stats"
                params = {
                    "desde": fecha_desde,
                    "hasta": fecha_hasta,
                    "ejercicio": ejercicio
                }
                logger.info(f"Consultando API por ejercicio específico: {ejercicio}")
            else:
                # Consulta general por últimos ejercicios
                url = f"{API_BASE_URL}/api/logs"
                params = {"days": 30}
                logger.info(f"Consultando API por logs generales")
            
            # Hacer la solicitud HTTP
            response = requests.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
                timeout=30
            )
            
            # Comprobar si la solicitud fue exitosa
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Recibida respuesta exitosa de la API")
                
                # Formatear la respuesta para el usuario
                if ejercicio and "datos" in data:
                    respuesta = format_specific_exercise_response(data, ejercicio)
                elif "logs" in data and data.get("logs"):
                    respuesta = format_exercise_logs_response(data["logs"])
                else:
                    respuesta = "No encontré registros de ejercicios en tu historial reciente. ¿Quieres registrar alguno nuevo?"
            else:
                logger.error(f"Error en la solicitud HTTP: {response.status_code}")
                respuesta = "No pude obtener información sobre tus ejercicios en este momento. ¿Puedo ayudarte con algo más?"
        else:
            # Si no es una consulta sobre últimos ejercicios, usar LLM para dar información general
            respuesta = await get_general_exercise_info(query)
            
    except Exception as e:
        logger.error(f"Error procesando consulta de ejercicio: {str(e)}")
        respuesta = "Tuve un problema al consultar tu historial de ejercicios. ¿Puedo ayudarte con algo más?"
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- FINALIZADO PROCESAMIENTO DE EJERCICIO ---")
    return agent_state, memory_state

def format_specific_exercise_response(data: Dict[str, Any], ejercicio: str) -> str:
    """Formatea la respuesta para un ejercicio específico."""
    try:
        datos = data.get("datos", [])
        if not datos:
            return f"No encontré registros recientes de {ejercicio} en tu historial. ¿Quieres registrar uno nuevo?"
        
        # Obtener la sesión más reciente
        ultimo_ejercicio = datos[0]  # Asumimos que vienen ordenados por fecha
        fecha = ultimo_ejercicio.get("fecha", "")
        if isinstance(fecha, str) and len(fecha) > 10:
            fecha = fecha[:10]
        
        # Construir la respuesta
        respuesta = f"## Tu último ejercicio de {ejercicio}\n\n"
        respuesta += f"**Fecha:** {fecha}\n\n"
        
        # Detalles del ejercicio
        max_peso = ultimo_ejercicio.get("max_peso", 0)
        total_reps = ultimo_ejercicio.get("total_reps", 0)
        volumen = ultimo_ejercicio.get("volumen", 0)
        
        respuesta += f"• **Peso máximo:** {max_peso}kg\n"
        respuesta += f"• **Repeticiones totales:** {total_reps}\n"
        respuesta += f"• **Volumen total:** {volumen}kg\n\n"
        
        # Si hay información de progreso
        resumen = data.get("resumen", {})
        if resumen and "progress_percent" in resumen:
            progress = resumen["progress_percent"]
            if progress > 0:
                respuesta += f"📈 Has progresado un **{progress}%** desde tu primera sesión registrada.\n\n"
            elif progress < 0:
                respuesta += f"📉 Has retrocedido un **{abs(progress)}%** desde tu primera sesión registrada.\n\n"
        
        respuesta += "¿Quieres registrar una nueva sesión de este ejercicio?"
        return respuesta
    
    except Exception as e:
        logger.error(f"Error formateando respuesta específica: {e}")
        return f"Encontré información sobre tu {ejercicio}, pero tuve problemas al procesarla. ¿Puedo ayudarte con información general sobre este ejercicio?"

def format_exercise_logs_response(logs: List[Dict[str, Any]]) -> str:
    """Formatea la respuesta con los logs de ejercicios recientes."""
    try:
        if not logs:
            return "No encontré registros de ejercicios en tu historial reciente. ¿Quieres registrar alguno nuevo?"
        
        # Agrupar ejercicios por fecha (más reciente primero)
        logs_by_date = {}
        for log in logs[:10]:  # Limitamos a los 10 más recientes
            fecha = log.get("fecha", "")
            if isinstance(fecha, str) and len(fecha) > 10:
                fecha = fecha[:10]
            
            if fecha not in logs_by_date:
                logs_by_date[fecha] = []
            
            logs_by_date[fecha].append(log)
        
        # Construir la respuesta
        respuesta = "## Tus ejercicios recientes\n\n"
        
        for fecha, ejercicios in sorted(logs_by_date.items(), reverse=True)[:5]:  # Mostrar los últimos 5 días
            respuesta += f"### {fecha}\n"
            
            for ejercicio in ejercicios:
                nombre = ejercicio.get("ejercicio", "ejercicio desconocido")
                respuesta += f"• {nombre}\n"
            
            respuesta += "\n"
        
        respuesta += "¿Quieres ver más detalles sobre algún ejercicio específico o registrar uno nuevo?"
        return respuesta
    
    except Exception as e:
        logger.error(f"Error formateando logs: {e}")
        return "Encontré tus registros de ejercicios, pero tuve problemas al mostrarlos. ¿Puedo ayudarte con algo más?"

async def get_general_exercise_info(query: str) -> str:
    """Obtiene información general sobre ejercicios usando el LLM."""
    try:
        # Crear un prompt para el LLM
        system_message = """Eres un entrenador personal especializado en ejercicios y fitness. 
        Proporciona información precisa, basada en evidencia científica y útil. 
        Sé conciso pero informativo, y adapta tu respuesta a la consulta específica del usuario."""
        
        prompt = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]
        
        # Obtener respuesta del LLM
        llm = get_llm()
        response = await llm.ainvoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
    
    except Exception as e:
        logger.error(f"Error obteniendo información general: {e}")
        return "Puedo proporcionarte información sobre técnicas de ejercicios, programas de entrenamiento o recomendaciones para mejorar tu rendimiento. ¿Qué te gustaría saber específicamente?"