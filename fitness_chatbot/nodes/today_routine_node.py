# fitness_chatbot/nodes/today_routine_node.py
import logging
import json
from datetime import datetime
from typing import Tuple, Dict, Any, List
import psycopg2
import psycopg2.extras
import os

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState

logger = logging.getLogger("fitness_chatbot")

async def process_today_routine(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Obtiene la rutina de ejercicios del día actual consultando directamente la base de datos.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- CONSULTA DE RUTINA DIARIA INICIADA ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de rutina para usuario {user_id}: '{query}'")
    
    try:
        # Configuración de conexión a la BD
        db_config = {
            'dbname': os.getenv('DB_NAME', 'gymdb'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'host': "gym-postgres",  # Usar el nombre del servicio Docker
            'port': "5432"           # Puerto interno de PostgreSQL
        }
        
        logger.info(f"Conectando a PostgreSQL en {db_config['host']}:{db_config['port']}")
        
        # Obtener el día de la semana actual (1-7, donde 1 es lunes)
        current_day = datetime.now().isoweekday()
        logger.info(f"Día actual de la semana: {current_day}")
        
        # Conectar a la base de datos
        with psycopg2.connect(**db_config) as conn:
            # Configurar para devolver resultados como diccionarios
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Consulta SQL para obtener la rutina del día actual para este usuario
                query_sql = """
                SELECT id, dia_semana, ejercicios 
                FROM gym.rutinas 
                WHERE user_id = %s AND dia_semana = %s
                """
                cursor.execute(query_sql, (user_id, current_day))
                
                # Obtener el resultado
                routine_row = cursor.fetchone()
                
                if routine_row:
                    # Convertir el resultado a diccionario
                    routine_data = dict(routine_row)
                    
                    # Obtener la lista de ejercicios (JSON)
                    exercises_json = routine_data.get('ejercicios', '[]')
                    
                    # Si exercises_json no es una cadena, convertirlo a cadena primero
                    if not isinstance(exercises_json, str):
                        exercises_json = json.dumps(exercises_json)
                    
                    # Convertir la cadena JSON a objeto Python
                    exercises = json.loads(exercises_json)
                    
                    # Mapear día de la semana a nombre
                    day_names = {
                        1: "Lunes", 2: "Martes", 3: "Miércoles", 
                        4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"
                    }
                    dia_nombre = day_names.get(current_day, f"Día {current_day}")
                    
                    # Crear lista de ejercicios con formato para mostrar
                    rutina = []
                    for ejercicio in exercises:
                        if isinstance(ejercicio, str):
                            rutina.append({"ejercicio": ejercicio, "realizado": False})
                        elif isinstance(ejercicio, dict):
                            rutina.append(ejercicio)
                    
                    # Formatear la respuesta
                    respuesta = f"## 📅 Tu rutina para {dia_nombre}\n\n"
                    
                    if not rutina:
                        respuesta += "No tienes ejercicios programados para hoy. ¿Quieres que te ayude a crear una rutina?\n"
                    else:
                        for idx, ejercicio in enumerate(rutina, 1):
                            # Mostrar nombre del ejercicio
                            nombre_ejercicio = ejercicio.get('ejercicio', 'No especificado')
                            respuesta += f"### {idx}. {nombre_ejercicio}\n"
                            
                            # Mostrar otros campos disponibles si existen
                            for key, value in ejercicio.items():
                                if key != 'ejercicio':
                                    respuesta += f"- **{key.capitalize()}:** {value}\n"
                            respuesta += "\n"
                    
                    respuesta += "¿Necesitas más detalles sobre estos ejercicios?"
                else:
                    # No se encontró rutina para este día
                    logger.warning(f"No se encontró rutina para user_id={user_id}, día={current_day}")
                    
                    # Verificar si el usuario tiene alguna rutina
                    cursor.execute("SELECT COUNT(*) FROM gym.rutinas WHERE user_id = %s", (user_id,))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        respuesta = f"No tienes ejercicios programados para hoy. ¿Quieres que te ayude a crear una rutina para este día?"
                    else:
                        respuesta = "No encontré ninguna rutina configurada. ¿Quieres que te ayude a crear tu plan de entrenamiento semanal?"
    
    except psycopg2.Error as e:
        logger.exception(f"Error de base de datos: {str(e)}")
        respuesta = "Lo siento, tuve un problema al conectar con la base de datos. Por favor, intenta de nuevo más tarde."
    except json.JSONDecodeError as e:
        logger.exception(f"Error decodificando JSON: {str(e)}")
        respuesta = "Tuve un problema al procesar tu rutina. Por favor, contacta con soporte técnico."
    except Exception as e:
        logger.exception(f"Error procesando consulta de rutina: {str(e)}")
        respuesta = "Tuve un problema al obtener tu rutina. ¿Quieres planificar tu entrenamiento?"
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- CONSULTA DE RUTINA DIARIA FINALIZADA ---")
    return agent_state, memory_state