# fitness_chatbot/nodes/nutrition_node.py
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

async def process_nutrition_query(states: Tuple[AgentState, MemoryState]) -> Tuple[AgentState, MemoryState]:
    """
    Procesa consultas sobre nutrición y muestra la dieta para el día actual.
    
    Args:
        states: Tupla con (AgentState, MemoryState)
        
    Returns:
        Tupla actualizada con (AgentState, MemoryState)
    """
    logger.info("--- CONSULTA DE DIETA DIARIA INICIADA ---")
    
    # Desempaquetar estados
    agent_state, memory_state = states
    
    # Obtener consulta y usuario
    query = agent_state["query"]
    user_id = agent_state["user_id"]
    
    logger.info(f"Procesando consulta de nutrición para usuario {user_id}: '{query}'")
    
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
                # Consulta SQL para obtener las comidas del día actual
                query_sql = """
                SELECT mpi.meal_type, m.meal_name
                FROM nutrition.meal_plan_items mpi
                JOIN nutrition.meals m ON mpi.meal_id = m.id
                WHERE mpi.day_of_week = %s
                """
                cursor.execute(query_sql, (current_day,))
                
                # Obtener los resultados
                meal_items = cursor.fetchall()
                
                if meal_items:
                    # Formatear la respuesta con los datos encontrados
                    day_names = {
                        1: "Lunes", 2: "Martes", 3: "Miércoles", 
                        4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"
                    }
                    dia_nombre = day_names.get(current_day, f"Día {current_day}")
                    
                    respuesta = f"## 🍽️ Tu menú para {dia_nombre}\n\n"
                    
                    # Agrupar por tipo de comida
                    meals_by_type = {}
                    for item in meal_items:
                        meal_type = item['meal_type'].replace('MealTime.', '')
                        if meal_type not in meals_by_type:
                            meals_by_type[meal_type] = []
                        meals_by_type[meal_type].append(item['meal_name'])
                    
                    # Mostrar cada tipo de comida
                    for meal_type, meals in meals_by_type.items():
                        respuesta += f"### {meal_type}\n\n"
                        for meal in meals:
                            respuesta += f"- {meal}\n"
                        respuesta += "\n"
                    
                    respuesta += "¿Necesitas información sobre alguna comida en particular?"
                else:
                    # No hay comidas para este día, mostrar plan predeterminado
                    respuesta = f"## 🍽️ No encontré tu plan nutricional para hoy\n\n{get_default_meal_plan(current_day)}\n\n¿Te gustaría que configuremos un plan personalizado?"
    
    except Exception as e:
        logger.exception(f"Error procesando consulta de nutrición: {str(e)}")
        # Si hay algún error, mostrar plan predeterminado
        current_day = datetime.now().isoweekday()
        respuesta = f"## 🍽️ Plan nutricional recomendado para hoy\n\n{get_default_meal_plan(current_day)}"
    
    # Actualizar estado y memoria
    agent_state["generation"] = respuesta
    memory_state["messages"].append({"role": "assistant", "content": respuesta})
    
    logger.info("--- CONSULTA DE DIETA DIARIA FINALIZADA ---")
    return agent_state, memory_state

def get_default_meal_plan(day_number: int) -> str:
    """
    Proporciona un plan nutricional predeterminado según el día de la semana.
    
    Args:
        day_number: Número del día (1-7, donde 1 es lunes)
        
    Returns:
        Plan nutricional predeterminado
    """
    # Planes predefinidos según el día de la semana
    plans = {
        1: {  # Lunes
            "enfoque": "proteínas para recuperación",
            "desayuno": "Tortilla de claras (3) con espinacas y champiñones",
            "media_mañana": "Yogur griego con frutos rojos",
            "almuerzo": "Pechuga de pollo a la plancha con ensalada verde",
            "merienda": "Batido de proteínas con plátano",
            "cena": "Salmón al horno con espárragos"
        },
        2: {  # Martes
            "enfoque": "energía y carbohidratos complejos",
            "desayuno": "Avena con leche, plátano y canela",
            "media_mañana": "Tostada integral con aguacate",
            "almuerzo": "Arroz integral con pavo y verduras salteadas",
            "merienda": "Manzana y un puñado de almendras",
            "cena": "Tortilla de patata con ensalada mixta"
        },
        3: {  # Miércoles
            "enfoque": "balance de macronutrientes",
            "desayuno": "Tostadas integrales con huevo revuelto y aguacate",
            "media_mañana": "Batido verde con espinacas, plátano y proteína",
            "almuerzo": "Ensalada de quinoa con pollo, nueces y vegetales",
            "merienda": "Queso fresco con tomate cherry",
            "cena": "Merluza al vapor con calabacín y patata al horno"
        },
        4: {  # Jueves
            "enfoque": "recuperación muscular",
            "desayuno": "Yogur griego con granola y frutas del bosque",
            "media_mañana": "Barrita de proteínas casera",
            "almuerzo": "Lentejas con verduras y pechuga de pavo",
            "merienda": "Batido de proteínas con avena",
            "cena": "Pechuga de pollo a la plancha con brócoli y boniato"
        },
        5: {  # Viernes
            "enfoque": "preparación para el fin de semana",
            "desayuno": "Batido proteico con plátano, avena y canela",
            "media_mañana": "Puñado de nueces mixtas",
            "almuerzo": "Pasta integral con atún y tomate",
            "merienda": "Yogur griego con miel",
            "cena": "Pizza casera con base integral, pollo y verduras"
        },
        6: {  # Sábado
            "enfoque": "energía para actividades",
            "desayuno": "Pancakes de avena con frutas y miel",
            "media_mañana": "Smoothie de frutas con proteína",
            "almuerzo": "Hamburguesa casera con patatas al horno",
            "merienda": "Hummus con crudités",
            "cena": "Pasta con salsa de tomate y albóndigas caseras"
        },
        7: {  # Domingo
            "enfoque": "recuperación y preparación",
            "desayuno": "Huevos benedictine con salmón ahumado",
            "media_mañana": "Pieza de fruta de temporada",
            "almuerzo": "Paella de marisco",
            "merienda": "Yogur con frutos secos",
            "cena": "Crema de verduras con pollo a la plancha"
        }
    }
    
    # Obtener plan para el día actual o lunes como fallback
    plan = plans.get(day_number, plans[1])
    
    # Formatear respuesta
    respuesta = f"**Enfoque del día**: {plan['enfoque'].capitalize()}\n\n"
    respuesta += f"**Desayuno**: {plan['desayuno']}\n"
    respuesta += f"**Media mañana**: {plan['media_mañana']}\n"
    respuesta += f"**Almuerzo**: {plan['almuerzo']}\n"
    respuesta += f"**Merienda**: {plan['merienda']}\n"
    respuesta += f"**Cena**: {plan['cena']}\n"
    
    return respuesta