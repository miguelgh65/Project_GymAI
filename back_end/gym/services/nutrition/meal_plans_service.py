# back_end/gym/services/nutrition/meal_plans_service.py
import logging
from typing import Optional, List, Dict, Any

# Importaciones locales
from .meal_plans_base import (
    list_meal_plans,
    get_meal_plan,
    delete_meal_plan
)
from .meal_plans_items import (
    get_meal_plan_items,
    get_meal_plan_items_formatted,
    update_meal_plan_items,
    process_meal_plan_items
)
from .meal_plans_utils import (
    format_plan_result,
    format_meal_plan_item
)

# Configurar logger
logger = logging.getLogger(__name__)

# Importar bibliotecas estándar y de terceros
import psycopg2
from back_end.gym.config import DB_CONFIG

def create_meal_plan(user_id: str, plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Crea un nuevo plan de comida y sus items asociados en una transacción.
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, gym, public")

        # 1. Insertar el plan principal
        plan_query = """
        INSERT INTO nutrition.meal_plans
            (user_id, plan_name, start_date, end_date, description, is_active,
             target_calories, target_protein_g, target_carbs_g, target_fat_g, goal)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, plan_name, start_date, end_date, description, is_active,
                  target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
                  created_at, updated_at
        """

        plan_params = (
            str(user_id),
            plan_data.get('plan_name'),
            plan_data.get('start_date'),
            plan_data.get('end_date'),
            plan_data.get('description'),
            plan_data.get('is_active', True),
            plan_data.get('target_calories'),
            plan_data.get('target_protein_g'),
            plan_data.get('target_carbs_g'),
            plan_data.get('target_fat_g'),
            plan_data.get('goal')
        )

        cur.execute(plan_query, plan_params)
        plan_result = cur.fetchone()

        if not plan_result:
            logger.error(f"Fallo al insertar el registro principal del plan para usuario {user_id}")
            raise ValueError("Error crítico al crear el registro principal del plan")

        plan_id = plan_result[0]
        created_plan = format_plan_result(plan_result)
        logger.info(f"Plan principal ID {plan_id} insertado para usuario {user_id}.")

        # 2. Procesar y guardar items si existen
        items_data = plan_data.get('items', [])
        if items_data:
            # Formatear items para inserción
            items_to_insert = process_meal_plan_items(items_data, plan_id)
            
            if items_to_insert:
                item_query = """
                INSERT INTO nutrition.meal_plan_items
                    (meal_plan_id, meal_id, plan_date, day_of_week, meal_type, quantity, unit, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cur.executemany(item_query, items_to_insert)
                logger.info(f"Plan ID {plan_id}: Insertados {len(items_to_insert)} items.")
            else:
                logger.warning(f"Plan ID {plan_id}: No se insertaron items (todos inválidos).")

        # 3. Commit de la transacción
        conn.commit()
        logger.info(f"Plan de comida ID {plan_id} creado con éxito para usuario {user_id}.")
        
        # 4. Devolver plan creado
        return created_plan

    except Exception as e:
        if conn: conn.rollback()
        logger.exception(f"Error al crear plan de comida para usuario {user_id}: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()


def update_meal_plan(meal_plan_id: int, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza un plan de comida existente y opcionalmente sus items.
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, gym, public")

        # 1. Actualizar campos del plan principal si se proporcionan
        plan_update_fields = []
        plan_params = []
        plan_keys = ['plan_name', 'start_date', 'end_date', 'description', 'is_active',
                     'target_calories', 'target_protein_g', 'target_carbs_g', 'target_fat_g', 'goal']

        for key in plan_keys:
            if key in update_data and update_data[key] is not None:
                plan_update_fields.append(f"{key} = %s")
                plan_params.append(update_data[key])

        if plan_update_fields:
            plan_update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_plan_query = f"""
            UPDATE nutrition.meal_plans
            SET {", ".join(plan_update_fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, plan_name, start_date, end_date, description, is_active,
                      target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
                      created_at, updated_at
            """
            plan_params.extend([meal_plan_id, str(user_id)])

            cur.execute(update_plan_query, tuple(plan_params))
            plan_result = cur.fetchone()

            if not plan_result:
                logger.warning(f"Plan {meal_plan_id} no encontrado o no pertenece al usuario {user_id}")
                conn.rollback()
                return None

            updated_plan = format_plan_result(plan_result)
            logger.info(f"Plan principal ID {meal_plan_id} actualizado.")
        else:
            # Si no se actualizó el plan, obtenemos los datos actuales
            check_query = """
            SELECT id, user_id, plan_name, start_date, end_date, description, is_active,
                   target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
                   created_at, updated_at
            FROM nutrition.meal_plans
            WHERE id = %s AND user_id = %s
            """
            cur.execute(check_query, (meal_plan_id, str(user_id)))
            plan_result = cur.fetchone()
            
            if not plan_result:
                logger.warning(f"Plan {meal_plan_id} no encontrado o no pertenece al usuario {user_id}")
                conn.rollback()
                return None
                
            updated_plan = format_plan_result(plan_result)

        # 2. Actualizar items si se proporcionan en update_data
        if 'items' in update_data:
            items_data = update_data['items'] or []
            
            # Eliminar ítems existentes y crear nuevos
            cur.execute("DELETE FROM nutrition.meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
            deleted_count = cur.rowcount
            logger.info(f"Plan ID {meal_plan_id}: Eliminados {deleted_count} items antiguos.")
            
            # Insertar nuevos items si hay
            if items_data:
                items_to_insert = process_meal_plan_items(items_data, meal_plan_id)
                
                if items_to_insert:
                    item_query = """
                    INSERT INTO nutrition.meal_plan_items
                        (meal_plan_id, meal_id, plan_date, day_of_week, meal_type, quantity, unit, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cur.executemany(item_query, items_to_insert)
                    logger.info(f"Plan ID {meal_plan_id}: Insertados {len(items_to_insert)} nuevos items.")
                else:
                    logger.warning(f"Plan ID {meal_plan_id}: No se insertaron items (todos inválidos).")

        # 3. Commit de la transacción
        conn.commit()
        logger.info(f"Plan de comida ID {meal_plan_id} actualizado con éxito.")
        
        # 4. Devolver plan actualizado (sin items)
        return updated_plan

    except Exception as e:
        if conn: conn.rollback()
        logger.exception(f"Error al actualizar plan {meal_plan_id}: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()