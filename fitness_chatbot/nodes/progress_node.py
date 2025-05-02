# fitness_chatbot/nodes/progress_node.py - VERSIÓN USANDO API DIRECTA
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List

from fitness_chatbot.schemas.agent_state import AgentState
from fitness_chatbot.schemas.memory_schemas import MemoryState

logger = logging.getLogger("fitness_chatbot")

# URL base para la API
API_BASE_URL = "http://localhost"

async def process_progress_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas de progreso consultando directamente la API del backend.
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de progreso: '{query}' para usuario {user_id}")
    
    # Detectar ejercicio (simplificado)
    ejercicio = None
    if "press" in query.lower() or "banca" in query.lower():
        ejercicio = "press banca"
        logger.info("Ejercicio 'press banca' detectado en la consulta")
    
    # Fechas para filtrado (último mes)
    fecha_hasta = datetime.now().strftime("%Y-%m-%d")
    fecha_desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    try:
        # Llamar directamente a la API de ejercicios_stats
        url = f"{API_BASE_URL}/api/ejercicios_stats"
        
        params = {
            "desde": fecha_desde,
            "hasta": fecha_hasta
        }
        
        # Añadir ejercicio si se ha detectado
        if ejercicio:
            params["ejercicio"] = ejercicio
        
        logger.info(f"Consultando API: {url} con params: {params}")
        
        # Hacer la solicitud a la API
        response = requests.get(
            url,
            params=params,
            headers={
                "Accept": "application/json",
                # No incluimos Authorization ya que el middleware se encarga de la autenticación
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Datos recibidos de la API: {data.keys() if isinstance(data, dict) else 'no es un dict'}")
            
            # Generar respuesta basada en los datos
            respuesta = generar_respuesta(data, ejercicio)
        else:
            logger.error(f"Error al llamar a la API: {response.status_code} - {response.text}")
            respuesta = "Lo siento, no pude obtener información sobre tus ejercicios en este momento."
    
    except Exception as e:
        logger.error(f"Error consultando la API: {e}")
        respuesta = "Tuve un problema al consultar tu historial de ejercicios. Por favor, intenta de nuevo más tarde."
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO ---")
    return agent_state, memory_state

def generar_respuesta(data: Dict[str, Any], ejercicio: Optional[str] = None) -> str:
    """Genera respuesta basada en los datos de la API"""
    try:
        if not data.get("success", False):
            return "No pude obtener datos de tus ejercicios. Por favor, intenta más tarde."
        
        # Obtener datos de ejercicios
        ejercicios_disponibles = data.get("ejercicios_disponibles", [])
        datos = data.get("datos", [])
        
        if ejercicio:
            titulo = f"## Historial de {ejercicio.title()}"
        else:
            titulo = "## Historial de Ejercicios"
        
        # Si no hay datos pero hay ejercicios disponibles
        if not datos and ejercicios_disponibles:
            return f"{titulo}\n\nNo encontré datos para el período consultado, pero tienes los siguientes ejercicios registrados: " + ", ".join(ejercicios_disponibles) + "."
        
        # Si no hay datos ni ejercicios
        if not datos and not ejercicios_disponibles:
            return f"{titulo}\n\nNo encontré ejercicios registrados. Puedes empezar registrando tus entrenamientos diciéndome algo como 'Registra press banca 3 series de 10 repeticiones con 60kg'."
        
        # Formatear datos de ejercicios
        ejercicios_texto = []
        for entry in datos:
            fecha = entry.get("fecha", "")
            if isinstance(fecha, str) and len(fecha) > 10:
                fecha = fecha[:10]
            
            max_peso = entry.get("max_peso", 0)
            total_reps = entry.get("total_reps", 0)
            volumen = entry.get("volumen", 0)
            
            ejercicios_texto.append(f"• {fecha}")
            ejercicios_texto.append(f"  - Peso máximo: {max_peso}kg")
            ejercicios_texto.append(f"  - Repeticiones totales: {total_reps}")
            ejercicios_texto.append(f"  - Volumen total: {volumen}kg")
        
        # Incluir resumen si está disponible
        resumen = data.get("resumen", {})
        resumen_texto = []
        if resumen:
            if "total_sesiones" in resumen:
                resumen_texto.append(f"• Total de sesiones: {resumen['total_sesiones']}")
            if "max_weight_ever" in resumen:
                resumen_texto.append(f"• Peso máximo histórico: {resumen['max_weight_ever']}kg")
            if "max_volume_session" in resumen:
                resumen_texto.append(f"• Volumen máximo en una sesión: {resumen['max_volume_session']}kg")
            if "progress_percent" in resumen:
                resumen_texto.append(f"• Progreso: {resumen['progress_percent']}%")
        
        # Armar la respuesta completa
        if ejercicios_texto:
            respuesta = f"{titulo}\n\nAquí está tu historial reciente:\n\n" + "\n".join(ejercicios_texto)
            
            if resumen_texto:
                respuesta += "\n\n### Resumen de Progreso\n\n" + "\n".join(resumen_texto)
            
            respuesta += "\n\n¿Quieres analizar algún otro ejercicio o registrar un nuevo entrenamiento?"
            return respuesta
        else:
            return f"{titulo}\n\nNo encontré datos detallados para este ejercicio en el período consultado."
    
    except Exception as e:
        logger.error(f"Error generando respuesta: {e}")
        return "Encontré tus datos, pero tuve problemas al analizarlos. Por favor, intenta de nuevo."