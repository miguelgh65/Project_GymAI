import logging
import json
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from typing import Tuple, List, Dict, Any
import re

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.core.db_connector import DatabaseConnector

logger = logging.getLogger("fitness_chatbot")

async def process_history_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas para ver el historial de ejercicios del usuario.
    Conecta directamente a la base de datos PostgreSQL.
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE HISTORIAL INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de historial: '{query}' para usuario {user_id}")
    
    # Detectar si es consulta sobre ejercicio específico
    ejercicio_especifico = detect_specific_exercise(query)
    if ejercicio_especifico:
        logger.info(f"Ejercicio específico detectado: {ejercicio_especifico}")
    
    # Detectar si busca el último ejercicio
    busca_ultimo = "último" in query.lower() or "ultimo" in query.lower() or "reciente" in query.lower()
    
    try:
        # Conectar a la base de datos
        conn = None
        try:
            db_config = DatabaseConnector.get_db_config()
            logger.info(f"Configuración DB: {db_config}")
            conn = psycopg2.connect(**db_config)
            
            # Si hay un ejercicio específico
            if ejercicio_especifico:
                # Consultar datos de ese ejercicio
                respuesta = get_specific_exercise_history(conn, user_id, ejercicio_especifico)
            elif busca_ultimo:
                # Consultar el último ejercicio
                respuesta = get_latest_exercise(conn, user_id)
            else:
                # Consultar resumen general
                respuesta = get_general_exercise_history(conn, user_id)
                
        except Exception as db_err:
            logger.error(f"Error de base de datos: {str(db_err)}")
            respuesta = f"Lo siento, tuve problemas al conectar con la base de datos: {str(db_err)}"
        finally:
            if conn:
                conn.close()
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de historial: {str(e)}")
        respuesta = "Lo siento, tuve un problema al procesar tu consulta sobre tu historial de ejercicios."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE HISTORIAL FINALIZADO ---")
    return agent_state, memory_state

def detect_specific_exercise(query: str) -> str:
    """
    Detecta si la consulta menciona un ejercicio específico.
    """
    query_lower = query.lower()
    
    # Mapeo de ejercicios comunes
    exercise_mapping = {
        "press banca": ["press banca", "press de banca", "bench press", "banca"],
        "sentadillas": ["sentadilla", "sentadillas", "squat", "squats"],
        "peso muerto": ["peso muerto", "deadlift"],
        "dominadas": ["dominada", "dominadas", "pull up", "pull-up", "chin up"],
        "curl de bíceps": ["curl", "bíceps", "biceps", "curl de biceps", "curl biceps"],
        "press militar": ["press militar", "military press", "press hombro", "press de hombro"],
        "fondos": ["fondos", "dips", "fondos de tríceps", "triceps dips"],
        "remo": ["remo", "row", "remo con barra"]
    }
    
    # Buscar coincidencias
    for standard_name, variations in exercise_mapping.items():
        for variation in variations:
            if variation in query_lower:
                return standard_name
    
    return ""

def get_specific_exercise_history(conn, user_id: str, ejercicio: str) -> str:
    """
    Obtiene y formatea el historial de un ejercicio específico.
    """
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Consulta SQL para obtener los datos del ejercicio
    query = """
    SELECT fecha, ejercicio, repeticiones
    FROM gym.ejercicios
    WHERE user_id = %s AND ejercicio ILIKE %s
    ORDER BY fecha DESC
    LIMIT 10
    """
    
    cursor.execute(query, (user_id, f"%{ejercicio}%"))
    ejercicios = cursor.fetchall()
    
    if not ejercicios:
        return f"No encontré registros de **{ejercicio}** en tu historial. ¿Quieres registrar este ejercicio?"
    
    # Formatear la respuesta
    respuesta = f"## 📊 Historial de {ejercicio}\n\n"
    
    # Obtener el último ejercicio
    ultimo_ejercicio = ejercicios[0]
    ultima_fecha = ultimo_ejercicio["fecha"].strftime("%Y-%m-%d %H:%M")
    
    # Parsear el JSON de repeticiones
    try:
        if isinstance(ultimo_ejercicio["repeticiones"], str):
            series = json.loads(ultimo_ejercicio["repeticiones"])
        else:
            series = ultimo_ejercicio["repeticiones"]
        
        # Calcular máximos
        peso_maximo = 0
        total_reps = 0
        volumen_total = 0
        
        for serie in series:
            peso = float(serie.get("peso", 0))
            reps = int(serie.get("repeticiones", 0))
            
            if peso > peso_maximo:
                peso_maximo = peso
                
            total_reps += reps
            volumen_total += peso * reps
        
        # Añadir resumen del último ejercicio
        respuesta += f"### 💪 Tu último entrenamiento ({ultima_fecha})\n\n"
        respuesta += f"• **Peso máximo usado:** {peso_maximo} kg\n"
        respuesta += f"• **Repeticiones totales:** {total_reps}\n"
        respuesta += f"• **Volumen total:** {volumen_total} kg\n\n"
        
        # Mostrar las series del último entrenamiento
        respuesta += "**Series:**\n"
        for i, serie in enumerate(series, 1):
            peso = float(serie.get("peso", 0))
            reps = int(serie.get("repeticiones", 0))
            respuesta += f"• Serie {i}: {reps} repeticiones × {peso} kg\n"
        
        respuesta += "\n"
        
        # Mostrar los últimos entrenamientos (sin el primero que ya mostramos)
        if len(ejercicios) > 1:
            respuesta += "### 🏋️ Entrenamientos anteriores\n\n"
            for i, ej in enumerate(ejercicios[1:5], 1):  # Mostrar solo los siguientes 4
                fecha = ej["fecha"].strftime("%Y-%m-%d")
                
                # Calcular peso máximo de este entrenamiento
                try:
                    if isinstance(ej["repeticiones"], str):
                        series_ant = json.loads(ej["repeticiones"])
                    else:
                        series_ant = ej["repeticiones"]
                        
                    peso_max_ant = max([float(s.get("peso", 0)) for s in series_ant])
                    reps_total_ant = sum([int(s.get("repeticiones", 0)) for s in series_ant])
                    
                    respuesta += f"**{fecha}**: {peso_max_ant} kg (máximo), {reps_total_ant} repeticiones totales\n"
                except:
                    respuesta += f"**{fecha}**: Datos no disponibles\n"
            
        respuesta += "\n¿Quieres registrar una nueva sesión de este ejercicio?"
        
    except Exception as e:
        # Si hay error procesando el JSON
        respuesta += f"Encontré registros de {ejercicio}, pero tuve problemas al procesarlos: {str(e)}\n"
        respuesta += "\n¿Quieres registrar una nueva sesión de este ejercicio?"
    
    cursor.close()
    return respuesta

def get_latest_exercise(conn, user_id: str) -> str:
    """
    Obtiene y formatea el último ejercicio registrado.
    """
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Consulta SQL para obtener el último ejercicio
    query = """
    SELECT fecha, ejercicio, repeticiones
    FROM gym.ejercicios
    WHERE user_id = %s
    ORDER BY fecha DESC
    LIMIT 1
    """
    
    cursor.execute(query, (user_id,))
    ultimo = cursor.fetchone()
    
    if not ultimo:
        return "No encontré ningún ejercicio en tu historial. ¿Quieres empezar a registrar tus entrenamientos?"
    
    # Formatear la respuesta
    ejercicio = ultimo["ejercicio"]
    fecha = ultimo["fecha"].strftime("%Y-%m-%d %H:%M")
    
    respuesta = f"## 🏋️ Tu último ejercicio\n\n"
    respuesta += f"**Ejercicio:** {ejercicio}\n"
    respuesta += f"**Fecha:** {fecha}\n\n"
    
    # Parsear el JSON de repeticiones
    try:
        if isinstance(ultimo["repeticiones"], str):
            series = json.loads(ultimo["repeticiones"])
        else:
            series = ultimo["repeticiones"]
        
        # Calcular máximos
        peso_maximo = 0
        total_reps = 0
        volumen_total = 0
        
        for serie in series:
            peso = float(serie.get("peso", 0))
            reps = int(serie.get("repeticiones", 0))
            
            if peso > peso_maximo:
                peso_maximo = peso
                
            total_reps += reps
            volumen_total += peso * reps
        
        # Añadir detalles
        respuesta += f"**Peso máximo:** {peso_maximo} kg\n"
        respuesta += f"**Repeticiones totales:** {total_reps}\n"
        respuesta += f"**Volumen total:** {volumen_total} kg\n\n"
        
        # Mostrar las series
        respuesta += "**Series:**\n"
        for i, serie in enumerate(series, 1):
            peso = float(serie.get("peso", 0))
            reps = int(serie.get("repeticiones", 0))
            respuesta += f"• Serie {i}: {reps} repeticiones × {peso} kg\n"
        
    except Exception as e:
        # Si hay error procesando el JSON
        respuesta += f"No pude procesar los detalles de las series: {str(e)}\n"
    
    respuesta += "\n¿Quieres ver más detalles de este ejercicio o registrar uno nuevo?"
    
    cursor.close()
    return respuesta

def get_general_exercise_history(conn, user_id: str) -> str:
    """
    Obtiene y formatea un resumen general del historial de ejercicios.
    """
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Consulta SQL para obtener ejercicios únicos
    query_ejercicios = """
    SELECT DISTINCT ejercicio
    FROM gym.ejercicios
    WHERE user_id = %s
    """
    
    cursor.execute(query_ejercicios, (user_id,))
    ejercicios_unicos = [row["ejercicio"] for row in cursor.fetchall()]
    
    if not ejercicios_unicos:
        return "No encontré registros de ejercicios en tu historial. ¿Quieres empezar a registrar tus entrenamientos?"
    
    # Formatear la respuesta
    respuesta = "## 📊 Tu Historial de Ejercicios\n\n"
    
    # Obtener información de cada ejercicio
    ejercicios_info = []
    for ejercicio in ejercicios_unicos:
        # Consultar último registro y total
        query_info = """
        SELECT COUNT(*) as total, MAX(fecha) as ultima_fecha
        FROM gym.ejercicios
        WHERE user_id = %s AND ejercicio = %s
        """
        
        cursor.execute(query_info, (user_id, ejercicio))
        info = cursor.fetchone()
        
        ejercicios_info.append({
            "nombre": ejercicio,
            "total": info["total"],
            "ultima_fecha": info["ultima_fecha"]
        })
    
    # Ordenar por fecha más reciente
    ejercicios_info.sort(key=lambda x: x["ultima_fecha"], reverse=True)
    
    # Añadir lista de ejercicios
    respuesta += f"Has realizado **{len(ejercicios_unicos)} ejercicios diferentes** en tu historial:\n\n"
    
    # Mostrar ejercicios en forma de lista
    for info in ejercicios_info:
        fecha_str = info["ultima_fecha"].strftime("%Y-%m-%d") if info["ultima_fecha"] else "fecha desconocida"
        respuesta += f"• **{info['nombre']}** - {info['total']} sesiones (última: {fecha_str})\n"
    
    # Añadir información sobre el último ejercicio
    if ejercicios_info:
        ultimo = ejercicios_info[0]
        respuesta += f"\nTu ejercicio más reciente fue **{ultimo['nombre']}** el {ultimo['ultima_fecha'].strftime('%Y-%m-%d')}.\n\n"
    
    respuesta += "Para ver detalles sobre un ejercicio específico, pregúntame por él. Por ejemplo:\n"
    respuesta += "- \"¿Cómo va mi progreso en sentadillas?\"\n"
    respuesta += "- \"Muéstrame mi historial de press banca\"\n"
    respuesta += "- \"¿Cuál es mi mejor marca en peso muerto?\"\n\n"
    
    respuesta += "¿Sobre qué ejercicio te gustaría ver más detalles?"
    
    cursor.close()
    return respuesta