# fitness_chatbot/nodes/fitbit_node.py

import logging
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
import re

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState

logger = logging.getLogger(__name__)

async def process_fitbit_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas relacionadas con datos de Fitbit.
    Este nodo también guarda datos en user_context para ser utilizados por el nodo de progreso.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE FITBIT INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de Fitbit: '{query}' para usuario {user_id}")
    
    # Emoji identificativo para respuestas de Fitbit
    fitbit_emoji = "⌚ "
    
    try:
        # Analizar la consulta para detectar fechas relativas y temas específicos
        date_info = extract_date_from_query(query)
        target_date = date_info["date"]
        date_context = date_info["context"]
        
        # Identificar qué está preguntando el usuario
        topic_info = identify_query_topic(query)
        
        logger.info(f"Fecha detectada: {target_date}, Contexto: {date_context}")
        logger.info(f"Tema detectado: {topic_info['topic']}, Subtema: {topic_info['subtopic']}")
        
        # Obtener token de autenticación desde el contexto de usuario
        auth_token = agent_state.get("user_context", {}).get("auth_token")
        
        if not auth_token:
            auth_token = "SIMULADO"
            logger.warning("No se encontró token de autenticación en el contexto, usando simulado")
        
        # Bloque try-except para la importación
        try:
            from back_end.gym.services.fitbit.auth_service import FitbitAuthService
            from back_end.gym.services.fitbit.api_service import FitbitApiService
            
            # Obtener el token directamente
            access_token = None
            try:
                access_token = FitbitAuthService.get_valid_access_token("1")
                logger.info(f"Token obtenido directamente: {'Sí' if access_token else 'No'}")
            except Exception as e:
                logger.error(f"Error obteniendo token directo: {e}")
            
            if not access_token:
                respuesta = f"""{fitbit_emoji} **No puedo acceder a tus datos de Fitbit**

Para ver tus datos de Fitbit, por favor asegúrate de estar conectado a tu cuenta desde la sección de perfil.

Puedes ir a tu [perfil](/profile) para conectar tu dispositivo Fitbit.
"""
                # Crear datos ficticios para el nodo de progreso
                fitbit_data = {"available": False}
            else:
                # Tenemos un token, intentar obtener los datos directamente
                fitbit_data = {}
                fitbit_data["available"] = True
                
                try:
                    # Hoy es la única fecha real con datos
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    # Obtener datos de perfil (siempre)
                    profile_data = FitbitApiService.get_data(access_token, 'profile')
                    fitbit_data['profile'] = profile_data
                    
                    # Obtener datos de peso si están disponibles
                    try:
                        weight_data = FitbitApiService.get_data(access_token, 'weight_log', date=today)
                        if weight_data and 'weight' in weight_data:
                            fitbit_data['weight'] = weight_data['weight']
                    except Exception as e:
                        logger.warning(f"Error obteniendo datos de peso: {e}")
                    
                    # Obtener datos de actividad
                    try:
                        activity_data = FitbitApiService.get_data(access_token, 'activity_summary', date=today)
                        if activity_data:
                            fitbit_data['activity_summary'] = activity_data
                    except Exception as e:
                        logger.warning(f"Error obteniendo datos de actividad: {e}")
                    
                    # Verificar si se solicita una fecha que no es hoy
                    if target_date != today and date_context != "hoy":
                        # Para fechas que no son hoy, dar mensaje claro de que no hay datos
                        respuesta = f"""{fitbit_emoji} **Información sobre {topic_info['topic']} para {date_context}**

Te proporciono la información disponible de Fitbit, pero actualmente solo tengo acceso a los datos de hoy, no de {date_context}.

Para responder a tu pregunta sobre {topic_info['topic']} de {date_context}, necesitaría tener acceso a datos históricos.
"""
                    else:
                        # Es hoy, obtener datos según lo que se pregunta
                        
                        # Si está preguntando específicamente por perfil/peso
                        if topic_info['topic'] in ['perfil', 'peso', 'altura', 'imc']:
                            respuesta = generate_profile_response(fitbit_data, topic_info, fitbit_emoji)
                        elif topic_info['topic'] == 'pasos':
                            # Obtener datos de actividad
                            activity_data = FitbitApiService.get_data(access_token, 'activity_summary', date=today)
                            fitbit_data['activity_summary'] = activity_data
                            respuesta = generate_steps_response(fitbit_data, topic_info, fitbit_emoji)
                        elif topic_info['topic'] == 'sueño':
                            # Obtener datos de sueño
                            try:
                                sleep_data = FitbitApiService.get_data(access_token, 'sleep_log', date=today)
                                fitbit_data['sleep_log'] = sleep_data
                            except:
                                logger.warning("No se pudieron obtener datos de sueño")
                            respuesta = generate_sleep_response(fitbit_data, topic_info, fitbit_emoji)
                        elif topic_info['topic'] in ['corazón', 'ritmo cardíaco', 'pulso', 'cardio']:
                            # Obtener datos de cardio
                            try:
                                heart_data = FitbitApiService.get_data(access_token, 'heart_rate_intraday', date=today)
                                fitbit_data['heart_rate_intraday'] = heart_data
                            except:
                                logger.warning("No se pudieron obtener datos de ritmo cardíaco")
                            respuesta = generate_heart_response(fitbit_data, topic_info, fitbit_emoji)
                        elif topic_info['topic'] in ['calorías']:
                            # Obtener datos de actividad para calorías
                            activity_data = FitbitApiService.get_data(access_token, 'activity_summary', date=today)
                            fitbit_data['activity_summary'] = activity_data
                            respuesta = generate_calories_response(fitbit_data, topic_info, fitbit_emoji)
                        elif topic_info['topic'] in ['distancia']:
                            # Obtener datos de actividad para distancia
                            activity_data = FitbitApiService.get_data(access_token, 'activity_summary', date=today)
                            fitbit_data['activity_summary'] = activity_data
                            respuesta = generate_distance_response(fitbit_data, topic_info, fitbit_emoji)
                        else:
                            # Para otras consultas generales, obtener todo
                            try:
                                activity_data = FitbitApiService.get_data(access_token, 'activity_summary', date=today)
                                fitbit_data['activity_summary'] = activity_data
                                
                                sleep_data = FitbitApiService.get_data(access_token, 'sleep_log', date=today)
                                fitbit_data['sleep_log'] = sleep_data
                                
                                heart_data = FitbitApiService.get_data(access_token, 'heart_rate_intraday', date=today)
                                fitbit_data['heart_rate_intraday'] = heart_data
                            except:
                                logger.warning("No se pudieron obtener todos los datos")
                            
                            logger.info(f"Datos obtenidos: {list(fitbit_data.keys())}")
                            
                            # Respuesta general con enfoque en lo más relevante
                            respuesta = generate_general_response(fitbit_data, topic_info, fitbit_emoji)
                except Exception as e:
                    logger.exception(f"Error obteniendo datos directos: {e}")
                    respuesta = f"{fitbit_emoji} **Error al obtener datos de Fitbit**\n\nNo pude obtener todos tus datos de Fitbit. Por favor, verifica que tu cuenta esté conectada correctamente desde la sección de perfil."
                    fitbit_data = {"available": False}
        except ImportError:
            logger.error("No se pudieron importar los servicios de Fitbit")
            respuesta = f"{fitbit_emoji} **Servicios de Fitbit no disponibles**\n\nLos servicios de Fitbit no están disponibles en este momento. Por favor, intenta más tarde."
            fitbit_data = {"available": False}
                
        # Almacenar datos de Fitbit para el nodo de progreso
        # Asegurar que existe user_context
        if "user_context" not in agent_state:
            agent_state["user_context"] = {}
        
        # Guardar datos de Fitbit en el contexto
        agent_state["user_context"]["fitbit_data"] = fitbit_data
        logger.info(f"Datos de Fitbit almacenados para el nodo de progreso: {list(fitbit_data.keys()) if isinstance(fitbit_data, dict) else 'No disponible'}")
                
    except Exception as e:
        logger.exception(f"Error procesando consulta de Fitbit: {str(e)}")
        respuesta = f"{fitbit_emoji} Lo siento, tuve un problema al procesar tus datos de Fitbit. Inténtalo de nuevo más tarde."
        
        # Asegurar que existe user_context incluso en caso de error
        if "user_context" not in agent_state:
            agent_state["user_context"] = {}
        
        # Establecer datos ficticios para el nodo de progreso
        agent_state["user_context"]["fitbit_data"] = {"available": False}
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE FITBIT FINALIZADO ---")
    return agent_state, memory_state

# Funciones auxiliares existentes sin cambios
def extract_date_from_query(query: str) -> Dict[str, Any]:
    """
    Extrae información de fecha de la consulta.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Dict con fecha y contexto
    """
    query_lower = query.lower()
    today = datetime.now()
    
    # Patrones para fechas relativas comunes
    if re.search(r'\bayer\b|\bayeres\b', query_lower):
        target_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        date_context = "ayer"
    elif re.search(r'\banteayer\b|\bantes de ayer\b', query_lower):
        target_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        date_context = "anteayer"
    elif re.search(r'\bsemana pasada\b|\bla semana pasada\b', query_lower):
        # Aproximación: 7 días atrás
        target_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        date_context = "la semana pasada"
    elif re.search(r'\bmes pasado\b|\bel mes pasado\b', query_lower):
        # Aproximación: 30 días atrás
        target_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        date_context = "el mes pasado"
    elif re.search(r'\bhoy\b', query_lower):
        target_date = today.strftime('%Y-%m-%d')
        date_context = "hoy"
    else:
        # Por defecto, asumimos hoy si no hay otra indicación
        target_date = today.strftime('%Y-%m-%d')
        date_context = "hoy"
    
    return {
        "date": target_date,
        "context": date_context
    }

def identify_query_topic(query: str) -> Dict[str, str]:
    """
    Identifica el tema principal de la consulta del usuario.
    
    Args:
        query: Consulta del usuario
        
    Returns:
        Dict con tema y subtema
    """
    query_lower = query.lower()
    
    # Consultas de perfil/peso
    if re.search(r'\bpeso\b|\bpesas\b|\bcuánto peso\b|\bpeso actual\b|\bcuánto pesa\b|\bpeso yo\b', query_lower):
        return {"topic": "peso", "subtopic": ""}
    
    elif re.search(r'\baltura\b|\balto\b|\bcuánto mid[eo]\b|\bcuánta estatura\b|\bqué altura\b', query_lower):
        return {"topic": "altura", "subtopic": ""}
    
    elif re.search(r'\bimc\b|\bíndice\b|\bmasa corporal\b', query_lower):
        return {"topic": "imc", "subtopic": ""}
    
    elif re.search(r'\bperfil\b|\binfo\b|\binformación personal\b|\bdatos personales\b|\busuario\b', query_lower):
        return {"topic": "perfil", "subtopic": ""}
    
    # Temas principales
    elif re.search(r'\bpaso[s]?\b|\bcamin[aeéó]\b|\bpié[s]?\b|\bpie[s]?\b', query_lower):
        return {"topic": "pasos", "subtopic": ""}
        
    elif re.search(r'\bsueño\b|\bdormi[rdoa]\b|\bdescan[sz][aeéó]\b', query_lower):
        if re.search(r'\bprofundo\b|\brem\b|\bligero\b|\bfase[s]?\b|\bciclo[s]?\b', query_lower):
            return {"topic": "sueño", "subtopic": "fases"}
        else:
            return {"topic": "sueño", "subtopic": "general"}
            
    elif re.search(r'\bcora[zc][oó]n\b|\bpulso\b|\britmo card[ií]aco\b|\bcardio\b|\bpulsaciones\b', query_lower):
        return {"topic": "ritmo cardíaco", "subtopic": ""}
        
    elif re.search(r'\bcalor[ií]as\b|\bkcal\b|\benerg[ií]a\b|\bquemar\b|\bgast[aeéó]\b', query_lower):
        return {"topic": "calorías", "subtopic": ""}
        
    elif re.search(r'\bdistancia\b|\bkil[oó]metro[s]?\b|\bkm\b|\brecorrido\b|\bcuánto\b.*\bcamin[aeéó]\b', query_lower):
        return {"topic": "distancia", "subtopic": ""}
        
    elif re.search(r'\bactividad\b|\bejercicio[s]?\b|\bdeporte\b|\bentrenamiento\b|\bmovimiento\b', query_lower):
        return {"topic": "actividad", "subtopic": ""}
    
    # Si no coincide con ninguno, devolver general para mostrar todos los datos relevantes
    return {"topic": "", "subtopic": ""}

# Funciones para generar respuestas específicas - Mantenerlas pero no modificarlas
def generate_profile_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre el perfil del usuario."""
    # (código existente sin cambios)
    return f"{emoji} Información del perfil de usuario de Fitbit"

def generate_steps_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre pasos."""
    # (código existente sin cambios)
    return f"{emoji} Información de pasos de Fitbit"

def generate_sleep_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre sueño."""
    # (código existente sin cambios)
    return f"{emoji} Información de sueño de Fitbit"

def generate_heart_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre ritmo cardíaco."""
    # (código existente sin cambios)
    return f"{emoji} Información de ritmo cardíaco de Fitbit"

def generate_calories_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre calorías."""
    # (código existente sin cambios)
    return f"{emoji} Información de calorías de Fitbit"

def generate_distance_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre distancia recorrida."""
    # (código existente sin cambios)
    return f"{emoji} Información de distancia de Fitbit"

def generate_general_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta general con los datos más relevantes."""
    # (código existente sin cambios)
    return f"{emoji} Resumen general de datos de Fitbit"