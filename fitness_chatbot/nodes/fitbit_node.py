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
        else:
            # Tenemos un token, intentar obtener los datos directamente
            fitbit_data = {}
            
            try:
                # Hoy es la única fecha real con datos
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Obtener datos de perfil (siempre)
                profile_data = FitbitApiService.get_data(access_token, 'profile')
                fitbit_data['profile'] = profile_data
                
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
                
    except Exception as e:
        logger.exception(f"Error procesando consulta de Fitbit: {str(e)}")
        respuesta = f"{fitbit_emoji} Lo siento, tuve un problema al procesar tus datos de Fitbit. Inténtalo de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE FITBIT FINALIZADO ---")
    return agent_state, memory_state

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

def generate_profile_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre el perfil del usuario."""
    
    if 'profile' not in data or 'user' not in data['profile']:
        return f"{emoji} No tengo información sobre tu perfil en Fitbit. Verifica que tu cuenta esté conectada correctamente."
    
    user = data['profile']['user']
    
    # Si está preguntando específicamente por el peso
    if topic_info['topic'] == 'peso':
        if 'weight' not in user:
            return f"{emoji} No tengo información sobre tu peso en Fitbit. Puedes configurarlo en la aplicación de Fitbit."
        
        weight = user.get('weight', 0)
        height = user.get('height', 0)
        
        # Calcular IMC si tenemos altura
        imc_info = ""
        if height > 0:
            height_m = height / 100  # convertir cm a m
            imc = weight / (height_m * height_m)
            
            imc_category = ""
            if imc < 18.5:
                imc_category = "bajo peso"
            elif imc < 25:
                imc_category = "peso normal"
            elif imc < 30:
                imc_category = "sobrepeso"
            else:
                imc_category = "obesidad"
                
            imc_info = f"\n\n**IMC**: {imc:.1f} ({imc_category})"
        
        return f"{emoji} **Información sobre tu peso**\n\n**Peso actual**: {weight} kg{imc_info}"
    
    # Si está preguntando por la altura
    elif topic_info['topic'] == 'altura':
        if 'height' not in user:
            return f"{emoji} No tengo información sobre tu altura en Fitbit. Puedes configurarla en la aplicación de Fitbit."
        
        height = user.get('height', 0)
        
        return f"{emoji} **Información sobre tu altura**\n\n**Altura**: {height} cm"
    
    # Si está preguntando por el IMC
    elif topic_info['topic'] == 'imc':
        if 'weight' not in user or 'height' not in user:
            return f"{emoji} No tengo suficiente información para calcular tu IMC. Necesito tu peso y altura, que puedes configurar en la aplicación de Fitbit."
        
        weight = user.get('weight', 0)
        height = user.get('height', 0)
        
        # Calcular IMC
        height_m = height / 100  # convertir cm a m
        imc = weight / (height_m * height_m)
        
        imc_category = ""
        if imc < 18.5:
            imc_category = "bajo peso"
        elif imc < 25:
            imc_category = "peso normal"
        elif imc < 30:
            imc_category = "sobrepeso"
        else:
            imc_category = "obesidad"
        
        return f"{emoji} **Información sobre tu IMC**\n\n**IMC actual**: {imc:.1f}\n**Categoría**: {imc_category}\n\nEl IMC (Índice de Masa Corporal) es un indicador general que relaciona tu peso y altura, pero no tiene en cuenta la composición corporal (músculo vs grasa)."
    
    # Información de perfil general
    else:
        # Base de la respuesta
        response = f"{emoji} **Información de tu perfil de Fitbit**\n\n"
        
        # Añadir información disponible
        if 'firstName' in user or 'lastName' in user:
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                response += f"**Nombre**: {full_name}\n"
        
        if 'age' in user:
            response += f"**Edad**: {user['age']} años\n"
        
        if 'height' in user:
            response += f"**Altura**: {user['height']} cm\n"
        
        if 'weight' in user:
            response += f"**Peso**: {user['weight']} kg\n"
        
        if 'gender' in user:
            gender = "Masculino" if user['gender'].lower() == 'male' else "Femenino"
            response += f"**Género**: {gender}\n"
        
        # Calcular IMC si tenemos peso y altura
        if 'weight' in user and 'height' in user:
            weight = user['weight']
            height = user['height'] / 100  # convertir cm a m
            imc = weight / (height * height)
            
            imc_category = ""
            if imc < 18.5:
                imc_category = "bajo peso"
            elif imc < 25:
                imc_category = "peso normal"
            elif imc < 30:
                imc_category = "sobrepeso"
            else:
                imc_category = "obesidad"
                
            response += f"\n**IMC**: {imc:.1f} ({imc_category})"
        
        return response

def generate_steps_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre pasos."""
    
    if 'activity_summary' not in data:
        return f"{emoji} No tengo información sobre tus pasos hoy. Verifica que tu Fitbit esté sincronizado correctamente."
    
    summary = data['activity_summary'].get('summary', {})
    goals = data['activity_summary'].get('goals', {})
    
    if 'steps' not in summary:
        return f"{emoji} No tengo información sobre tus pasos hoy. Verifica que tu Fitbit esté sincronizado correctamente."
    
    steps = summary['steps']
    
    # Calcular progreso si hay meta de pasos
    progress_text = ""
    if 'steps' in goals:
        steps_goal = goals['steps']
        progress = (steps / steps_goal) * 100 if steps_goal > 0 else 0
        progress_text = f"\n\n**Progreso**: {steps} de {steps_goal} pasos ({progress:.1f}% de tu objetivo diario)"
    
    # Obtener distancia si está disponible
    distance_text = ""
    if 'distances' in summary:
        for dist in summary['distances']:
            if dist.get('activity') == 'total':
                distance = dist.get('distance', 0)
                distance_text = f"\n\n**Distancia recorrida**: {distance:.2f} km"
    
    # Construir respuesta
    response = f"{emoji} **Información sobre tus pasos hoy**\n\nHoy has dado **{steps} pasos**{progress_text}{distance_text}"
    
    # Añadir alguna interpretación
    if steps < 5000:
        response += "\n\nEstás por debajo de la recomendación mínima de 5000 pasos diarios. ¡Aún tienes tiempo para caminar un poco más hoy!"
    elif steps < 10000:
        response += "\n\nVas por buen camino. La recomendación general es de 7500-10000 pasos diarios para mantener un estilo de vida activo."
    else:
        response += "\n\n¡Excelente! Has superado la recomendación general de 10000 pasos diarios. ¡Sigue así!"
    
    return response

def generate_sleep_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre sueño."""
    
    if 'sleep_log' not in data or 'sleep' not in data['sleep_log'] or not data['sleep_log']['sleep']:
        return f"{emoji} No tengo información sobre tu sueño hoy. Esto puede deberse a que aún no has sincronizado tu dispositivo después de dormir o que no has usado tu Fitbit durante el sueño."
    
    sleep_list = data['sleep_log']['sleep']
    
    # Buscar el sueño principal
    main_sleep = None
    for sleep in sleep_list:
        if sleep.get('isMainSleep', False):
            main_sleep = sleep
            break
    
    if not main_sleep and sleep_list:
        main_sleep = sleep_list[0]
    
    if not main_sleep:
        return f"{emoji} No tengo información detallada sobre tu sueño hoy."
    
    # Extraer datos clave
    minutes_asleep = main_sleep.get('minutesAsleep', 0)
    hours = minutes_asleep // 60
    minutes = minutes_asleep % 60
    efficiency = main_sleep.get('efficiency', 0)
    
    # Base de la respuesta
    response = f"{emoji} **Información sobre tu sueño hoy**\n\n**Tiempo total de sueño**: {hours}h {minutes}m\n**Eficiencia del sueño**: {efficiency}%"
    
    # Añadir info de fases si está disponible
    if 'levels' in main_sleep and 'summary' in main_sleep['levels']:
        response += "\n\n**Desglose por fases de sueño**:"
        summary = main_sleep['levels']['summary']
        
        # Procesar cada fase si existe
        phases = [
            ('deep', 'Sueño profundo'),
            ('light', 'Sueño ligero'),
            ('rem', 'Sueño REM'),
            ('wake', 'Tiempo despierto')
        ]
        
        for phase_key, phase_name in phases:
            if phase_key in summary and 'minutes' in summary[phase_key]:
                phase_mins = summary[phase_key]['minutes']
                if phase_mins > 0:
                    response += f"\n- **{phase_name}**: {phase_mins} min"
    
    # Añadir alguna interpretación
    if hours < 6:
        response += "\n\nTu tiempo de sueño está por debajo de las 7-9 horas recomendadas para adultos."
    elif hours >= 7 and hours <= 9:
        response += "\n\nTu tiempo de sueño está dentro del rango recomendado de 7-9 horas para adultos."
    
    if efficiency < 80:
        response += "\n\nLa eficiencia de tu sueño está por debajo del 85% considerado óptimo."
    else:
        response += "\n\nTu eficiencia del sueño es buena (por encima del 80%)."
    
    return response

def generate_heart_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre ritmo cardíaco."""
    
    if 'heart_rate_intraday' not in data or 'activities-heart' not in data['heart_rate_intraday'] or not data['heart_rate_intraday']['activities-heart']:
        return f"{emoji} No tengo información sobre tu ritmo cardíaco hoy. Verifica que tu Fitbit esté sincronizado correctamente."
    
    heart_summary = data['heart_rate_intraday']['activities-heart'][0]
    
    if 'value' not in heart_summary:
        return f"{emoji} No tengo información detallada sobre tu ritmo cardíaco hoy."
    
    value = heart_summary['value']
    
    # Extraer ritmo cardíaco en reposo
    resting_rate = value.get('restingHeartRate')
    
    if not resting_rate:
        return f"{emoji} No tengo información sobre tu ritmo cardíaco en reposo hoy."
    
    # Base de la respuesta
    response = f"{emoji} **Información sobre tu ritmo cardíaco hoy**\n\n**Ritmo cardíaco en reposo**: {resting_rate} bpm"
    
    # Añadir info de zonas si está disponible
    if 'heartRateZones' in value:
        zones = value['heartRateZones']
        active_zones = [zone for zone in zones if zone.get('minutes', 0) > 0]
        
        if active_zones:
            response += "\n\n**Tiempo en zonas cardíacas**:"
            for zone in active_zones:
                zone_name = zone.get('name', 'Desconocida')
                zone_minutes = zone.get('minutes', 0)
                response += f"\n- **{zone_name}**: {zone_minutes} min"
    
    # Añadir alguna interpretación
    if resting_rate < 60:
        response += "\n\nTu ritmo cardíaco en reposo es excelente, típico de personas con buena condición física."
    elif resting_rate < 70:
        response += "\n\nTu ritmo cardíaco en reposo está en un buen rango saludable."
    elif resting_rate < 80:
        response += "\n\nTu ritmo cardíaco en reposo está dentro del rango normal."
    else:
        response += "\n\nTu ritmo cardíaco en reposo está ligeramente elevado. Factores como estrés, cafeína o falta de actividad física pueden influir."
    
    return response

def generate_calories_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre calorías."""
    
    if 'activity_summary' not in data:
        return f"{emoji} No tengo información sobre tus calorías quemadas hoy. Verifica que tu Fitbit esté sincronizado correctamente."
    
    summary = data['activity_summary'].get('summary', {})
    
    if 'caloriesOut' not in summary:
        return f"{emoji} No tengo información detallada sobre tus calorías quemadas hoy."
    
    calories = summary.get('caloriesOut', 0)
    
    # Obtener información de perfil para contexto
    profile_info = ""
    if 'profile' in data and 'user' in data['profile']:
        user = data['profile']['user']
        if 'age' in user and 'gender' in user:
            gender = user.get('gender', 'male')
            age = user.get('age', 30)
            
            # Estimación muy básica de metabolismo basal (BMR)
            if gender.lower() == 'female':
                bmr_estimate = 1400  # Valor aproximado para mujer de 30 años
            else:
                bmr_estimate = 1700  # Valor aproximado para hombre de 30 años
                
            if calories > bmr_estimate:
                profile_info = f" (por encima de tu metabolismo basal estimado de ~{bmr_estimate} calorías)"
    
    # Base de la respuesta
    response = f"{emoji} **Información sobre calorías quemadas hoy**\n\n**Calorías totales quemadas**: {calories} kcal{profile_info}"
    
    # Añadir contexto de actividad si está disponible
    if 'activeMinutes' in summary:
        active_minutes = summary.get('activeMinutes', 0)
        response += f"\n\n**Minutos de actividad**: {active_minutes} min"
        
    if 'steps' in summary:
        steps = summary.get('steps', 0)
        response += f"\n**Pasos dados**: {steps} pasos"
    
    return response

def generate_distance_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta específica sobre distancia recorrida."""
    
    if 'activity_summary' not in data:
        return f"{emoji} No tengo información sobre la distancia que has recorrido hoy. Verifica que tu Fitbit esté sincronizado correctamente."
    
    summary = data['activity_summary'].get('summary', {})
    
    if 'distances' not in summary:
        return f"{emoji} No tengo información detallada sobre la distancia recorrida hoy."
    
    # Buscar la distancia total
    total_distance = 0
    for dist in summary['distances']:
        if dist.get('activity') == 'total':
            total_distance = dist.get('distance', 0)
            break
    
    if total_distance == 0:
        return f"{emoji} No tengo información sobre la distancia total recorrida hoy."
    
    # Obtener pasos para contexto
    steps_info = ""
    if 'steps' in summary:
        steps = summary.get('steps', 0)
        steps_info = f"\n**Pasos dados**: {steps} pasos"
    
    # Base de la respuesta
    response = f"{emoji} **Información sobre la distancia recorrida hoy**\n\n**Distancia total**: {total_distance:.2f} km{steps_info}"
    
    return response

def generate_general_response(data: Dict[str, Any], topic_info: Dict[str, str], emoji: str) -> str:
    """Genera una respuesta general con los datos más relevantes."""
    
    # Base de la respuesta
    response = f"{emoji} **Resumen de tus datos de Fitbit para hoy**\n\n"
    
    # Información de perfil
    if 'profile' in data and 'user' in data['profile']:
        user = data['profile']['user']
        name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
        
        if name:
            response += f"**Usuario**: {name}\n"
        
        if 'age' in user:
            response += f"**Edad**: {user['age']} años\n"
            
        if 'height' in user and 'weight' in user:
            response += f"**Altura**: {user['height']} cm\n"
            response += f"**Peso**: {user['weight']} kg\n"
        
        response += "\n"
    
    # Datos de actividad (siempre incluirlos si están disponibles)
    if 'activity_summary' in data:
        summary = data['activity_summary'].get('summary', {})
        goals = data['activity_summary'].get('goals', {})
        
        response += "**Actividad Física**:\n"
        
        # Pasos
        if 'steps' in summary:
            steps = summary['steps']
            steps_goal = goals.get('steps', 0)
            
            if steps_goal > 0:
                progress = (steps / steps_goal) * 100
                response += f"- **Pasos**: {steps}/{steps_goal} ({progress:.1f}%)\n"
            else:
                response += f"- **Pasos**: {steps}\n"
        
        # Calorías
        if 'caloriesOut' in summary:
            response += f"- **Calorías quemadas**: {summary['caloriesOut']} kcal\n"
        
        # Distancia
        if 'distances' in summary:
            for dist in summary['distances']:
                if dist.get('activity') == 'total':
                    distance = dist.get('distance', 0)
                    response += f"- **Distancia**: {distance:.2f} km\n"
        
        response += "\n"
    
    # Ritmo cardíaco (si está disponible y hay datos interesantes)
    if 'heart_rate_intraday' in data and 'activities-heart' in data['heart_rate_intraday'] and data['heart_rate_intraday']['activities-heart']:
        heart_summary = data['heart_rate_intraday']['activities-heart'][0]
        
        if 'value' in heart_summary and 'restingHeartRate' in heart_summary['value']:
            resting_rate = heart_summary['value']['restingHeartRate']
            response += f"**Ritmo cardíaco en reposo**: {resting_rate} bpm\n\n"
    
    return response.strip()