# back_end/gym/services/nutrition/meal_plans_base.py
import logging
from typing import Optional, List, Dict, Any
import psycopg2

# Importaciones relativas
from back_end.gym.services.db_utils import execute_db_query
from back_end.gym.config import DB_CONFIG
from .meal_plans_utils import format_plan_result

# Configurar logger
logger = logging.getLogger(__name__)

def list_meal_plans(user_id: str, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Lista todos los planes de comida del usuario."""
    try:
        query = """
        SELECT id, user_id, plan_name, start_date, end_date, description, is_active,
               target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
               created_at, updated_at
        FROM nutrition.meal_plans
        WHERE user_id = %s
        """
        params = [str(user_id)]
        if is_active is not None:
            query += " AND is_active = %s"
            params.append(is_active)
        query += " ORDER BY created_at DESC"

        logger.debug(f"Listando planes para usuario {user_id}, activo: {is_active}")
        results = execute_db_query(query, tuple(params), fetch_all=True)
        logger.info(f"Encontrados {len(results)} planes para usuario {user_id}")

        meal_plans = [format_plan_result(row) for row in results]
        return meal_plans
    except Exception as e:
        logger.error(f"Error al listar planes de comida para usuario {user_id}: {e}")
        raise

def get_meal_plan(meal_plan_id: int, user_id: str, with_items: bool = True) -> Optional[Dict[str, Any]]:
    """Obtiene un plan de comida por su ID, opcionalmente incluyendo todos sus elementos/comidas."""
    try:
        plan_query = """
        SELECT id, user_id, plan_name, start_date, end_date, description, is_active,
               target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
               created_at, updated_at
        FROM nutrition.meal_plans
        WHERE id = %s AND user_id = %s
        """
        logger.debug(f"Obteniendo plan {meal_plan_id} para usuario {user_id}")
        plan_result = execute_db_query(plan_query, (meal_plan_id, str(user_id)), fetch_one=True)

        if not plan_result:
            logger.warning(f"Plan {meal_plan_id} no encontrado para usuario {user_id}")
            return None

        # Mapeo inicial del plan base
        meal_plan = format_plan_result(plan_result)
        meal_plan["items"] = [] # Inicializar lista de items

        if with_items:
            try:
                from .meal_plans_items import get_meal_plan_items_formatted
                items = get_meal_plan_items_formatted(meal_plan_id)
                logger.info(f"Plan {meal_plan_id}: Obtenidos {len(items)} items.")
                meal_plan["items"] = items
            except Exception as item_error:
                 logger.exception(f"Error al obtener items para plan {meal_plan_id}: {item_error}")

        return meal_plan
    except Exception as e:
        logger.exception(f"Error al obtener plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise

def delete_meal_plan(meal_plan_id: int, user_id: str) -> bool:
    """Elimina un plan de comida y sus items asociados en una transacción."""
    conn = None
    cur = None
    deleted = False
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, gym, public")

        # Verificar pertenencia
        cur.execute("SELECT id FROM nutrition.meal_plans WHERE id = %s AND user_id = %s", (meal_plan_id, str(user_id)))
        if cur.fetchone() is None:
            logger.warning(f"Intento de eliminar plan {meal_plan_id} fallido: No encontrado o no pertenece al usuario {user_id}.")
            return False

        # Eliminar items (CASCADE debería funcionar, pero explícito es más seguro)
        cur.execute("DELETE FROM nutrition.meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
        deleted_items_count = cur.rowcount
        logger.info(f"Eliminados {deleted_items_count} items para plan {meal_plan_id}")

        # Eliminar plan
        cur.execute("DELETE FROM nutrition.meal_plans WHERE id = %s", (meal_plan_id,))
        deleted_plan_count = cur.rowcount

        conn.commit()
        deleted = deleted_plan_count > 0
        if deleted:
            logger.info(f"Plan ID {meal_plan_id} eliminado con éxito.")
        else:
            logger.error(f"Error al eliminar plan {meal_plan_id} después de la verificación.")

        return deleted

    except Exception as e:
        if conn: conn.rollback()
        logger.exception(f"Error al eliminar plan {meal_plan_id}: {e}")
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()