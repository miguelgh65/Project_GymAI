# back_end/gym/services/nutrition/meal_plans_items.py
import logging
from typing import List, Dict, Any, Optional
import psycopg2

# Importaciones relativas
from back_end.gym.config import DB_CONFIG
from back_end.gym.services.db_utils import execute_db_query
from .meal_plans_utils import (
    format_meal_plan_item, 
    day_name_to_number,
    day_number_to_name,
    get_day_of_week_from_date
)

# Configurar logger
logger = logging.getLogger(__name__)

def get_meal_plan_items(meal_plan_id: int) -> List[Dict]:
    """Obtiene todos los items de un plan de comida en formato raw (como vienen de la BD)."""
    try:
        query = """
        SELECT mpi.id, mpi.meal_plan_id, mpi.meal_id, m.meal_name,
               mpi.plan_date, mpi.day_of_week, mpi.meal_type,
               mpi.quantity, mpi.unit, mpi.notes,
               mpi.created_at, mpi.updated_at,
               m.calories, m.proteins, m.carbohydrates, m.fats
        FROM nutrition.meal_plan_items mpi
        JOIN nutrition.meals m ON mpi.meal_id = m.id
        WHERE mpi.meal_plan_id = %s
        ORDER BY COALESCE(mpi.plan_date, mpi.created_at::date),
                 mpi.day_of_week,
                 CASE mpi.meal_type
                     WHEN 'Desayuno' THEN 1
                     WHEN 'Almuerzo' THEN 2
                     WHEN 'Comida' THEN 3
                     WHEN 'Merienda' THEN 4
                     WHEN 'Cena' THEN 5
                     WHEN 'Otro' THEN 6
                     ELSE 7
                 END,
                 mpi.created_at
        """
        results = execute_db_query(query, (meal_plan_id,), fetch_all=True)
        
        # Mapear los resultados a un formato diccionario
        items = []
        for row in results:
            # El day_of_week viene como INTEGER desde la BD
            items.append({
                "id": row[0],
                "meal_plan_id": row[1],
                "meal_id": row[2],
                "meal_name": row[3],
                "plan_date": row[4],
                "day_of_week": row[5],  # INTEGER en la BD
                "meal_type": row[6],
                "quantity": row[7],
                "unit": row[8],
                "notes": row[9],
                "created_at": row[10],
                "updated_at": row[11],
                "calories": row[12],
                "protein_g": row[13],  # Nombre normalizado para API
                "carbohydrates_g": row[14],
                "fat_g": row[15]  # Nombre normalizado para API
            })
        
        return items
    except Exception as e:
        logger.exception(f"Error al obtener items para plan {meal_plan_id}: {e}")
        raise

def get_meal_plan_items_formatted(meal_plan_id: int) -> List[Dict]:
    """
    Obtiene los items formateados para la API (day_of_week como texto).
    """
    raw_items = get_meal_plan_items(meal_plan_id)
    return [format_meal_plan_item(item) for item in raw_items]

def process_meal_plan_items(items_data: List[Dict], meal_plan_id: int) -> List[tuple]:
    """
    Procesa los datos de items para prepararlos para inserción/actualización.
    Convierte day_of_week de texto a número y configura días según las fechas.
    """
    items_to_insert = []
    
    for idx, item in enumerate(items_data):
        meal_id = item.get('meal_id')
        plan_date = item.get('plan_date')
        day_of_week_str = item.get('day_of_week')
        meal_type = item.get('meal_type')
        quantity = item.get('quantity')
        unit = item.get('unit', 'g')
        notes = item.get('notes')

        # Verificar datos mínimos requeridos
        if not meal_id:
            logger.warning(f"Item #{idx} sin meal_id, omitiendo: {item}")
            continue
        if quantity is None or quantity <= 0:
            logger.warning(f"Item #{idx} con quantity inválida ({quantity}), omitiendo: {item}")
            continue

        # Obtener day_of_week según prioridades:
        # 1. Usar day_of_week si existe como texto
        # 2. Calcular desde plan_date si existe
        # 3. Usar 1 (lunes) como valor por defecto
        day_of_week = None
        
        # 1. Primero intentar desde el nombre del día
        if day_of_week_str:
            try:
                day_of_week = day_name_to_number(day_of_week_str)
                logger.debug(f"Día obtenido desde nombre '{day_of_week_str}': {day_of_week}")
            except Exception as e:
                logger.error(f"Error convirtiendo día '{day_of_week_str}' a número: {e}")
        
        # 2. Si no hay día o falló, intentar calcular desde la fecha
        if day_of_week is None and plan_date:
            try:
                day_of_week = get_day_of_week_from_date(plan_date)
                logger.debug(f"Día calculado desde fecha {plan_date}: {day_of_week}")
            except Exception as e:
                logger.error(f"Error calculando día desde fecha {plan_date}: {e}")
        
        # 3. Si todo falló, usar lunes (1) como valor por defecto
        if day_of_week is None:
            day_of_week = 1
            logger.debug(f"Usando día por defecto (1: Lunes)")

        # Crear tupla con parámetros para SQL
        item_params = (
            meal_plan_id, 
            meal_id, 
            plan_date, 
            day_of_week,  # Guardamos como INTEGER
            str(meal_type) if meal_type else None, 
            quantity, 
            unit, 
            notes
        )
        
        logger.info(f"Item procesado: meal_id={meal_id}, plan_date={plan_date}, "
                   f"day_of_week={day_of_week} ({day_number_to_name(day_of_week)})")
        
        items_to_insert.append(item_params)
        
    return items_to_insert

def update_meal_plan_items(meal_plan_id: int, items_data: List[Dict]) -> bool:
    """
    Actualiza los items de un plan de comida (elimina existentes y crea nuevos).
    
    Args:
        meal_plan_id: ID del plan de comida
        items_data: Lista de diccionarios con datos de items
        
    Returns:
        bool: True si la operación fue exitosa
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, gym, public")

        # 1. Eliminar items antiguos
        cur.execute("DELETE FROM nutrition.meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
        deleted_count = cur.rowcount
        logger.info(f"Plan ID {meal_plan_id}: Eliminados {deleted_count} items antiguos.")

        # 2. Procesar nuevos items
        if items_data:
            # Preparar items para inserción
            items_to_insert = process_meal_plan_items(items_data, meal_plan_id)
            
            if items_to_insert:
                # Query para inserción
                item_query = """
                INSERT INTO nutrition.meal_plan_items
                    (meal_plan_id, meal_id, plan_date, day_of_week, meal_type, quantity, unit, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Ejecutar inserciones
                cur.executemany(item_query, items_to_insert)
                logger.info(f"Plan ID {meal_plan_id}: Insertados {len(items_to_insert)} nuevos items.")
            else:
                logger.warning(f"Plan ID {meal_plan_id}: No se insertaron items (todos inválidos).")

        # 3. Commit de los cambios
        conn.commit()
        return True

    except Exception as e:
        if conn: conn.rollback()
        logger.exception(f"Error al actualizar items para plan {meal_plan_id}: {e}")
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()