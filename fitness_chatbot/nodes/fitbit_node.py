# fitness_chatbot/nodes/fitbit_node.py
import logging
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState

logger = logging.getLogger(__name__)

async def process_fitbit_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """Procesa consultas de Fitbit y muestra los datos básicos."""
    logger.info("⌚⌚⌚ --- PROCESAMIENTO DE FITBIT INICIADO --- ⌚⌚⌚")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    is_progress = agent_state.get("is_progress", False)
    
    logger.info(f"🔍 Procesando consulta de Fitbit: '{query}' para usuario {user_id}")
    
    try:
        # Obtener token y servicio Fitbit
        from back_end.gym.services.fitbit.auth_service import FitbitAuthService
        from back_end.gym.services.fitbit.api_service import FitbitApiService
        
        # Obtener token de acceso
        access_token = FitbitAuthService.get_valid_access_token("1")
        
        if not access_token:
            logger.warning("❌ No se pudo obtener token de Fitbit")
            respuesta = "No puedo acceder a tus datos de Fitbit. Verifica que tu cuenta esté conectada."
        else:
            # Recolectar datos básicos
            fitbit_data = {}
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Obtener datos principales
            profile_data = FitbitApiService.get_data(access_token, 'profile')
            activity_data = FitbitApiService.get_data(access_token, 'activity_summary', date=today)
            
            # Intentar obtener datos adicionales
            try:
                sleep_data = FitbitApiService.get_data(access_token, 'sleep_log', date=today)
                heart_data = FitbitApiService.get_data(access_token, 'heart_rate_intraday', date=today)
                fitbit_data['sleep_log'] = sleep_data
                fitbit_data['heart_rate_intraday'] = heart_data
            except Exception as e:
                logger.warning(f"⚠️ Algunos datos de Fitbit no disponibles: {e}")
            
            # Guardar todos los datos
            fitbit_data['profile'] = profile_data
            fitbit_data['activity_summary'] = activity_data
            fitbit_data['available'] = True
            
            # Guardar datos en contexto para posible uso posterior
            logger.info(f"💾 Guardando datos crudos de Fitbit: {list(fitbit_data.keys())}")
            if "user_context" not in agent_state:
                agent_state["user_context"] = {}
            agent_state["user_context"]["fitbit_data"] = fitbit_data
            
            # Si es flujo de progress, solo almacenar los datos
            if is_progress:
                respuesta = agent_state.get("generation", "")
                logger.info("✅ Datos de Fitbit extraídos para análisis de progreso")
            else:
                # Formatear datos para mostrar al usuario (sin análisis)
                respuesta = format_basic_fitbit_data(fitbit_data, query)
                logger.info("✅ Datos formateados para mostrar al usuario")
    
    except Exception as e:
        logger.exception(f"❌ Error accediendo a datos de Fitbit: {str(e)}")
        respuesta = "Lo siento, tuve un problema al obtener tus datos de Fitbit."
    
    # Actualizar estado si no estamos en flujo de progress
    if not is_progress:
        agent_state["generation"] = respuesta
        memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("🏁🏁🏁 --- PROCESAMIENTO DE FITBIT FINALIZADO --- 🏁🏁🏁")
    return agent_state, memory_state

def format_basic_fitbit_data(data: Dict[str, Any], query: str) -> str:
    """
    Formatea los datos de Fitbit de manera básica, sin análisis excesivo.
    Solo muestra la información solicitada o un resumen general.
    """
    # Verificar qué tipo de datos quiere el usuario
    query_lower = query.lower()
    
    # Si pregunta por el peso
    if 'peso' in query_lower:
        if 'profile' in data and 'user' in data['profile']:
            user = data['profile']['user']
            if 'weight' in user:
                weight = user.get('weight', 0)
                return f"⌚ **Tu peso actual**: {weight} kg"
            else:
                return "No tengo datos de tu peso en Fitbit. Puedes configurarlo en la app de Fitbit."
    
    # Si pregunta por pasos o actividad
    elif any(word in query_lower for word in ['pasos', 'actividad', 'caminar']):
        if 'activity_summary' in data:
            summary = data['activity_summary'].get('summary', {})
            steps = summary.get('steps', 0)
            return f"⌚ **Pasos de hoy**: {steps}"
    
    # Si pregunta por datos de sueño
    elif any(word in query_lower for word in ['sueño', 'dormir', 'descanso']):
        if 'sleep_log' in data and 'sleep' in data['sleep_log'] and data['sleep_log']['sleep']:
            sleep = data['sleep_log']['sleep'][0]
            minutes = sleep.get('minutesAsleep', 0)
            hours = minutes // 60
            mins = minutes % 60
            return f"⌚ **Sueño registrado**: {hours}h {mins}m"
        else:
            return "No tengo datos de sueño registrados para hoy."
    
    # Si pregunta por ritmo cardíaco
    elif any(word in query_lower for word in ['corazón', 'cardíaco', 'pulso', 'pulsaciones']):
        if 'heart_rate_intraday' in data and 'activities-heart' in data['heart_rate_intraday']:
            heart = data['heart_rate_intraday']['activities-heart'][0]
            if 'value' in heart and 'restingHeartRate' in heart['value']:
                rate = heart['value']['restingHeartRate']
                return f"⌚ **Ritmo cardíaco en reposo**: {rate} ppm"
        return "No tengo datos de ritmo cardíaco disponibles para hoy."
    
    # Por defecto, mostrar resumen básico
    respuesta = "⌚ **Datos básicos de Fitbit**\n\n"
    
    # 1. Perfil
    if 'profile' in data and 'user' in data['profile']:
        user = data['profile']['user']
        respuesta += "**Perfil:**\n"
        
        # Nombre
        if 'firstName' in user:
            respuesta += f"- Nombre: {user.get('firstName', '')} {user.get('lastName', '')}\n"
        
        # Peso si está disponible
        if 'weight' in user:
            respuesta += f"- Peso: {user.get('weight', 0)} kg\n"
        
        # Altura si está disponible
        if 'height' in user:
            respuesta += f"- Altura: {user.get('height', 0)} cm\n"
        
        respuesta += "\n"
    
    # 2. Actividad
    if 'activity_summary' in data:
        summary = data['activity_summary'].get('summary', {})
        respuesta += "**Actividad de hoy:**\n"
        respuesta += f"- Pasos: {summary.get('steps', 0)}\n"
        respuesta += f"- Calorías quemadas: {summary.get('caloriesOut', 0)} kcal\n"
        
        # Distancia si está disponible
        if 'distances' in summary:
            for dist in summary['distances']:
                if dist.get('activity') == 'total':
                    respuesta += f"- Distancia: {dist.get('distance', 0):.2f} km\n"
                    break
        
        respuesta += "\n"
    
    # 3. Sueño (resumido)
    if 'sleep_log' in data and 'sleep' in data['sleep_log'] and data['sleep_log']['sleep']:
        sleep = data['sleep_log']['sleep'][0]
        minutes = sleep.get('minutesAsleep', 0)
        hours = minutes // 60
        mins = minutes % 60
        respuesta += f"**Sueño**: {hours}h {mins}m\n\n"
    
    # 4. Ritmo cardíaco (básico)
    if 'heart_rate_intraday' in data and 'activities-heart' in data['heart_rate_intraday']:
        heart = data['heart_rate_intraday']['activities-heart'][0]
        if 'value' in heart and 'restingHeartRate' in heart['value']:
            rate = heart['value']['restingHeartRate']
            respuesta += f"**Ritmo cardíaco en reposo**: {rate} ppm\n"
    
    return respuesta

def from_fitbit_decide_next(states):
    """Decide el siguiente nodo después de procesar datos de Fitbit."""
    agent_state, _ = states
    is_progress = agent_state.get("is_progress", False)
    
    logger.info(f"🔄 Decidiendo siguiente nodo: is_progress={is_progress}")
    
    if is_progress:
        # Si es progress, vamos a process_progress
        logger.info("🔄 Redirigiendo a process_progress")
        return "process_progress"
    else:
        # Si no es progress, vamos a generate_response
        logger.info("🔄 Redirigiendo a generate_response")
        return "generate_response"