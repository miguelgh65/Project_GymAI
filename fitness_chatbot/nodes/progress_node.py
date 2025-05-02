# fitness_chatbot/nodes/progress_node.py
import logging
from typing import Tuple, Dict, Any, List, Optional
import json
import re

from fitness_chatbot.schemas.agent_state import AgentState, IntentType
from fitness_chatbot.schemas.memory_schemas import MemoryState
from fitness_chatbot.configs.llm_config import get_llm
from fitness_chatbot.utils.prompt_manager import PromptManager

# Importar servicios de base de datos si están disponibles
try:
    from back_end.gym.services.database import get_exercise_logs
    from back_end.gym.routes.dashboard import get_ejercicios_stats
    DB_SERVICES_AVAILABLE = True
    logger = logging.getLogger("fitness_chatbot")
    logger.info("✅ Servicios de DB para progreso disponibles")
except ImportError:
    # Definir stub para get_exercise_logs
    def get_exercise_logs(user_id, days=30):
        logger.warning(f"Usando stub para get_exercise_logs: user_id={user_id}, days={days}")
        return []
    
    # Stub para get_ejercicios_stats
    async def get_ejercicios_stats(*args, **kwargs):
        logger.warning("Usando stub para get_ejercicios_stats")
        return {"success": False, "message": "Servicio no disponible"}
    
    DB_SERVICES_AVAILABLE = False
    logger = logging.getLogger("fitness_chatbot")
    logger.warning("⚠️ Servicios de DB para progreso NO disponibles, usando stubs")

async def process_progress_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas relacionadas con progreso y estadísticas.
    Obtiene datos crudos y deja que el LLM los analice directamente.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
    
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO INICIADO ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de progreso: '{query}' para usuario {user_id}")
    
    # Inicializar contexto de usuario si no existe
    if "user_context" not in agent_state:
        agent_state["user_context"] = {}
    
    # Extraer ejercicio específico si lo hay
    exercise_name = extract_exercise_name(query)
    if exercise_name:
        logger.info(f"Ejercicio específico detectado: {exercise_name}")
    
    # Obtener datos históricos CRUDOS para análisis de progreso
    # La idea es simplemente recolectar los datos y dejar que el LLM haga todo el análisis
    try:
        if DB_SERVICES_AVAILABLE:
            # 1. Obtener logs de ejercicios para análisis general
            exercise_logs = get_exercise_logs(user_id, days=90)
            
            # Construir un objeto simple para almacenar los datos crudos
            raw_exercise_data = []
            
            # Procesar minimamente los datos (solo para JSON correcto)
            for exercise in exercise_logs:
                try:
                    # Convertir 'repeticiones' de JSON a objeto si es necesario
                    repetitions = exercise.get('repeticiones')
                    if repetitions and isinstance(repetitions, str):
                        try:
                            repetitions = json.loads(repetitions)
                        except json.JSONDecodeError:
                            repetitions = []
                    
                    # Guardar datos crudos con formato mínimo
                    raw_exercise_data.append({
                        "fecha": str(exercise.get('fecha')),
                        "ejercicio": exercise.get('ejercicio'),
                        "repeticiones": repetitions
                    })
                except Exception as e:
                    logger.error(f"Error procesando ejercicio: {e}")
            
            # Almacenar todos los datos crudos
            agent_state["user_context"]["raw_exercise_data"] = raw_exercise_data
            logger.info(f"Obtenidos {len(raw_exercise_data)} registros de ejercicios para análisis")
            
            # 2. Intentar obtener estadísticas específicas a través del endpoint de dashboard
            if exercise_name:
                try:
                    # Simular una request para el endpoint de estadísticas
                    class MockRequest:
                        pass
                    
                    mock_request = MockRequest()
                    
                    # Crear objeto user simulado con google_id
                    user_for_stats = {"google_id": user_id}
                    
                    # Llamar a la función de estadísticas con el ejercicio específico
                    stats_response = await get_ejercicios_stats(
                        request=mock_request,
                        ejercicio=exercise_name,
                        desde=None,  # últimos 90 días por defecto
                        hasta=None,
                        user=user_for_stats
                    )
                    
                    # Almacenar las estadísticas crudas
                    if stats_response and stats_response.get("success", False):
                        agent_state["user_context"]["exercise_stats"] = stats_response
                        logger.info(f"Obtenidas estadísticas del ejercicio {exercise_name}")
                except Exception as stats_err:
                    logger.error(f"Error obteniendo estadísticas: {stats_err}")
        
        else:
            # Usar datos simulados para testing
            logger.warning("Usando datos simulados para testing")
            
            # Datos simulados según el ejercicio
            if exercise_name == "press banca":
                agent_state["user_context"]["raw_exercise_data"] = [
                    {
                        "fecha": "2024-03-15",
                        "ejercicio": "press banca",
                        "repeticiones": [
                            {"repeticiones": 10, "peso": 60},
                            {"repeticiones": 10, "peso": 60},
                            {"repeticiones": 8, "peso": 65}
                        ]
                    },
                    {
                        "fecha": "2024-04-01",
                        "ejercicio": "press banca",
                        "repeticiones": [
                            {"repeticiones": 10, "peso": 65},
                            {"repeticiones": 8, "peso": 70},
                            {"repeticiones": 6, "peso": 75}
                        ]
                    },
                    {
                        "fecha": "2024-04-15",
                        "ejercicio": "press banca",
                        "repeticiones": [
                            {"repeticiones": 8, "peso": 70},
                            {"repeticiones": 8, "peso": 70},
                            {"repeticiones": 6, "peso": 80}
                        ]
                    }
                ]
            elif exercise_name == "sentadillas":
                agent_state["user_context"]["raw_exercise_data"] = [
                    {
                        "fecha": "2024-03-10",
                        "ejercicio": "sentadillas",
                        "repeticiones": [
                            {"repeticiones": 10, "peso": 80},
                            {"repeticiones": 10, "peso": 80},
                            {"repeticiones": 8, "peso": 90}
                        ]
                    },
                    {
                        "fecha": "2024-03-25",
                        "ejercicio": "sentadillas",
                        "repeticiones": [
                            {"repeticiones": 10, "peso": 90},
                            {"repeticiones": 8, "peso": 100},
                            {"repeticiones": 6, "peso": 100}
                        ]
                    },
                    {
                        "fecha": "2024-04-10",
                        "ejercicio": "sentadillas",
                        "repeticiones": [
                            {"repeticiones": 8, "peso": 100},
                            {"repeticiones": 8, "peso": 100},
                            {"repeticiones": 6, "peso": 110}
                        ]
                    }
                ]
            else:
                # Datos generales si no hay ejercicio específico
                agent_state["user_context"]["raw_exercise_data"] = [
                    {
                        "fecha": "2024-03-15",
                        "ejercicio": "press banca",
                        "repeticiones": [{"repeticiones": 10, "peso": 60}]
                    },
                    {
                        "fecha": "2024-03-18",
                        "ejercicio": "sentadillas",
                        "repeticiones": [{"repeticiones": 10, "peso": 80}]
                    },
                    {
                        "fecha": "2024-04-01",
                        "ejercicio": "press banca",
                        "repeticiones": [{"repeticiones": 10, "peso": 65}]
                    },
                    {
                        "fecha": "2024-04-10",
                        "ejercicio": "sentadillas",
                        "repeticiones": [{"repeticiones": 8, "peso": 100}]
                    }
                ]
    
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos: {e}")
        # Crear contexto básico en caso de error
        agent_state["user_context"]["raw_exercise_data"] = []
        agent_state["user_context"]["error"] = str(e)
    
    # Formatear los datos para el LLM
    # Solo formateamos para mejor legibilidad, pero mantenemos los datos crudos
    # para que el LLM pueda hacer su propio análisis
    context = format_raw_data_for_llm(agent_state["user_context"], exercise_name)
    
    # Obtener mensajes de prompt para análisis de progreso
    messages = PromptManager.get_prompt_messages("progress", query=query, user_context=context)
    
    # Obtener LLM
    llm = get_llm()
    
    # Invocar LLM - Le dejamos todo el análisis
    try:
        response = await llm.ainvoke(messages)
        generation = response.content.strip()
        
        # Actualizar estado
        agent_state["generation"] = generation
        
        # Actualizar historial de mensajes
        memory_state["messages"].append({"role": "assistant", "content": generation})
        
        logger.info(f"Generado análisis de progreso de {len(generation)} caracteres")
        
    except Exception as e:
        logger.error(f"Error generando análisis de progreso: {str(e)}")
        agent_state["generation"] = "Lo siento, hubo un error analizando tu progreso."
        memory_state["messages"].append({"role": "assistant", "content": agent_state["generation"]})
    
    logger.info("--- PROCESAMIENTO DE CONSULTA DE PROGRESO FINALIZADO ---")
    
    return agent_state, memory_state

def extract_exercise_name(query: str) -> Optional[str]:
    """Extrae el nombre del ejercicio de la consulta."""
    # Lista de ejercicios comunes para detectar
    common_exercises = [
        "press banca", "sentadilla", "sentadillas", "peso muerto", "dominadas", 
        "press militar", "curl biceps", "fondos", "elevaciones laterales",
        "remo", "extensiones", "triceps"
    ]
    
    query_lower = query.lower()
    for exercise in common_exercises:
        if exercise in query_lower:
            return exercise
    
    return None

def format_raw_data_for_llm(user_context: Dict[str, Any], exercise_name: Optional[str] = None) -> str:
    """
    Formatea los datos crudos para presentarlos al LLM.
    Solo organiza los datos para mejor legibilidad, pero mantiene toda la información
    para que el LLM haga su propio análisis.
    
    Args:
        user_context: Contexto del usuario con datos crudos
        exercise_name: Nombre del ejercicio específico (opcional)
        
    Returns:
        Texto formateado para el contexto del LLM
    """
    context_lines = []
    
    # Indicar el análisis requerido
    if exercise_name:
        context_lines.append(f"ANÁLISIS DE PROGRESO PARA: {exercise_name}")
    else:
        context_lines.append("ANÁLISIS DE PROGRESO GENERAL DE ENTRENAMIENTO")
        
    context_lines.append("\n=== DATOS DE EJERCICIOS ===\n")
    
    # Si tenemos datos crudos de ejercicios
    if "raw_exercise_data" in user_context and user_context["raw_exercise_data"]:
        data = user_context["raw_exercise_data"]
        
        # Si hay un ejercicio específico, filtrar los datos
        if exercise_name:
            filtered_data = [
                entry for entry in data 
                if entry.get("ejercicio") and exercise_name.lower() in entry.get("ejercicio", "").lower()
            ]
            
            if filtered_data:
                # Ordenar por fecha
                sorted_data = sorted(filtered_data, key=lambda x: x.get("fecha", ""))
                
                context_lines.append(f"Historial de {exercise_name} (ordenado por fecha):")
                for i, entry in enumerate(sorted_data, 1):
                    fecha = entry.get("fecha", "fecha desconocida")
                    context_lines.append(f"\n[Sesión {i}] - Fecha: {fecha}")
                    
                    # Mostrar series/repeticiones
                    reps_data = entry.get("repeticiones", [])
                    if reps_data:
                        if isinstance(reps_data, list):
                            context_lines.append("  Series:")
                            for j, serie in enumerate(reps_data, 1):
                                reps = serie.get("repeticiones", "?")
                                peso = serie.get("peso", "?")
                                context_lines.append(f"  - Serie {j}: {reps} repeticiones x {peso}kg")
                        else:
                            # Si es un solo objeto
                            reps = reps_data.get("repeticiones", "?") 
                            peso = reps_data.get("peso", "?")
                            context_lines.append(f"  - {reps} repeticiones x {peso}kg")
            else:
                context_lines.append(f"No se encontraron registros para {exercise_name}")
        else:
            # Para análisis general, agrupar por ejercicio
            exercises_by_name = {}
            for entry in data:
                ex_name = entry.get("ejercicio", "desconocido")
                if ex_name not in exercises_by_name:
                    exercises_by_name[ex_name] = []
                exercises_by_name[ex_name].append(entry)
            
            # Mostrar resumen por cada tipo de ejercicio
            context_lines.append("Resumen de actividad por ejercicio:\n")
            for ex_name, entries in exercises_by_name.items():
                # Ordenar por fecha
                sorted_entries = sorted(entries, key=lambda x: x.get("fecha", ""))
                first_date = sorted_entries[0].get("fecha", "?") if sorted_entries else "?"
                last_date = sorted_entries[-1].get("fecha", "?") if sorted_entries else "?"
                
                # Encontrar peso máximo
                max_weight = 0
                for entry in entries:
                    reps_data = entry.get("repeticiones", [])
                    if isinstance(reps_data, list):
                        for serie in reps_data:
                            peso = serie.get("peso", 0)
                            if peso > max_weight:
                                max_weight = peso
                    elif isinstance(reps_data, dict):
                        peso = reps_data.get("peso", 0)
                        if peso > max_weight:
                            max_weight = peso
                
                context_lines.append(f"- {ex_name}:")
                context_lines.append(f"  - Número de sesiones: {len(entries)}")
                context_lines.append(f"  - Primera sesión: {first_date}")
                context_lines.append(f"  - Última sesión: {last_date}")
                context_lines.append(f"  - Peso máximo registrado: {max_weight}kg\n")
    else:
        context_lines.append("No hay datos de ejercicios disponibles")
    
    # Si tenemos estadísticas específicas del dashboard
    if "exercise_stats" in user_context and user_context["exercise_stats"]:
        stats = user_context["exercise_stats"]
        context_lines.append("\n=== ESTADÍSTICAS ADICIONALES ===\n")
        
        # Añadir el resumen si está disponible
        if "resumen" in stats and stats["resumen"]:
            resumen = stats["resumen"]
            context_lines.append("Resumen estadístico:")
            
            if "total_sesiones" in resumen:
                context_lines.append(f"- Total de sesiones: {resumen['total_sesiones']}")
            
            if "max_weight_ever" in resumen:
                context_lines.append(f"- Peso máximo histórico: {resumen['max_weight_ever']}kg")
            
            if "max_volume_session" in resumen:
                context_lines.append(f"- Volumen máximo en una sesión: {resumen['max_volume_session']}")
            
            if "max_reps_session" in resumen:
                context_lines.append(f"- Repeticiones máximas en una sesión: {resumen['max_reps_session']}")
            
            if "progress_percent" in resumen:
                context_lines.append(f"- Porcentaje de progreso: {resumen['progress_percent']}%")
        
        # Añadir datos de sesiones si están disponibles
        if "datos" in stats and stats["datos"]:
            datos = stats["datos"]
            context_lines.append("\nDatos de sesiones (formato JSON para análisis):")
            try:
                # Convertir a formato JSON legible para el LLM
                context_lines.append(json.dumps(datos, indent=2))
            except:
                # En caso de error, añadir datos en formato simple
                context_lines.append(str(datos))
    
    # Mensaje de error si existe
    if "error" in user_context and user_context["error"]:
        context_lines.append(f"\nERROR: {user_context['error']}")
    
    # Instrucciones al final para el análisis
    context_lines.append("\n=== INSTRUCCIONES PARA ANÁLISIS ===")
    context_lines.append("1. Analiza los datos anteriores para determinar el progreso")
    context_lines.append("2. Busca tendencias en pesos, repeticiones y volumen a lo largo del tiempo")
    context_lines.append("3. Indica si el progreso es positivo, negativo o mixto")
    context_lines.append("4. Proporciona recomendaciones basadas en los datos")
    
    return "\n".join(context_lines)