# back_end/gym/services/nutrition/meal_plans_service.py
import logging
from typing import Optional, List, Dict, Any
import decimal
import datetime

# Usar ruta absoluta
from back_end.gym.services.db_utils import execute_db_query
# Importar modelos para type hints si es necesario (opcional pero bueno)
from back_end.gym.models.nutrition_schemas import MealPlanItemInput

# Configurar logger
logger = logging.getLogger(__name__)

def create_meal_plan(user_id: str, plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Crea un nuevo plan de comida y sus items asociados en una transacción.
    Espera que plan_data['items'] sea una lista de dicts que coincidan
    con el modelo MealPlanItemInput.
    """
    conn = None
    cur = None
    plan_id = None # Inicializar plan_id

    try:
        # Importar DB_CONFIG aquí o pasarlo como argumento si es necesario
        from back_end.gym.config import DB_CONFIG
        import psycopg2

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Asegurarse de que estamos en el esquema correcto (si aplica)
        cur.execute("SET search_path TO nutrition, gym, public") # Incluir gym por si acaso

        # --- 1. Insertar el plan principal ---
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
            str(user_id),  # Convertir user_id a string
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
            raise ValueError("Error al crear el registro principal del plan")

        plan_id = plan_result[0]
        created_plan = {
            "id": plan_result[0], "user_id": plan_result[1], "plan_name": plan_result[2],
            "start_date": plan_result[3], "end_date": plan_result[4], "description": plan_result[5],
            "is_active": plan_result[6], "target_calories": plan_result[7],
            "target_protein_g": plan_result[8], "target_carbs_g": plan_result[9],
            "target_fat_g": plan_result[10], "goal": plan_result[11],
            "created_at": plan_result[12], "updated_at": plan_result[13]
        }
        logger.info(f"Plan principal ID {plan_id} insertado para usuario {user_id}.")

        # --- 2. Procesar y guardar cada item asociado ---
        items_data = plan_data.get('items', [])

        if items_data:
            logger.info(f"Plan ID {plan_id}: Procesando {len(items_data)} items.")
            # Usar columnas de init-db.sql: plan_date, day_of_week, meal_type, quantity, unit, notes
            item_query = """
            INSERT INTO nutrition.meal_plan_items
                (meal_plan_id, meal_id, plan_date, day_of_week, meal_type, quantity, unit, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            items_to_insert = []
            for item in items_data:
                 # Pydantic ya validó 'item' contra MealPlanItemInput (o similar)
                 meal_id = item.get('meal_id')
                 plan_date = item.get('plan_date')
                 day_of_week = item.get('day_of_week')
                 meal_type = item.get('meal_type') # Este es el Enum de Pydantic
                 quantity = item.get('quantity', 100.0)
                 unit = item.get('unit', 'g')
                 notes = item.get('notes')

                 # Requiere al menos meal_id y plan_date O day_of_week/meal_type? Definir lógica
                 if not meal_id:
                      logger.warning(f"Plan ID {plan_id}: Item sin meal_id, omitiendo: {item}")
                      continue

                 # Crear tupla - Convertir meal_type a string
                 item_params = (
                      plan_id, meal_id, plan_date, day_of_week,
                      str(meal_type) if meal_type else None, # Convertir Enum a str
                      quantity, unit, notes
                 )
                 items_to_insert.append(item_params)

            if items_to_insert:
                cur.executemany(item_query, items_to_insert)
                logger.info(f"Plan ID {plan_id}: Insertados {len(items_to_insert)} items en meal_plan_items.")
            else:
                 logger.warning(f"Plan ID {plan_id}: No se insertaron items (lista vacía o todos inválidos).")

        # --- 3. Confirmar la transacción ---
        conn.commit()
        logger.info(f"Plan de comida ID {plan_id} y sus items asociados creados con éxito para usuario {user_id}.")

        # --- 4. Formatear respuesta ---
        for key, value in created_plan.items():
            if isinstance(value, datetime.date):
                created_plan[key] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                 created_plan[key] = float(value)

        # Opcional: Obtener el plan recién creado con sus items para devolverlo completo
        # return get_meal_plan(plan_id, user_id, with_items=True)
        return created_plan # Devolver solo el plan base por ahora

    except psycopg2.Error as db_error:
        if conn: conn.rollback()
        logger.error(f"Error de base de datos al crear plan de comida para usuario {user_id}: {db_error}")
        raise ValueError(f"Error de base de datos: {db_error}")
    except Exception as e:
        if conn: conn.rollback()
        logger.exception(f"Error inesperado al crear plan de comida para usuario {user_id}: {e}")
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()


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

        meal_plans = []
        for row in results:
            meal_plan = {
                "id": row[0], "user_id": row[1], "plan_name": row[2],
                "start_date": row[3].isoformat() if isinstance(row[3], datetime.date) else row[3],
                "end_date": row[4].isoformat() if isinstance(row[4], datetime.date) else row[4],
                "description": row[5], "is_active": row[6],
                "target_calories": row[7],
                "target_protein_g": float(row[8]) if isinstance(row[8], decimal.Decimal) else row[8],
                "target_carbs_g": float(row[9]) if isinstance(row[9], decimal.Decimal) else row[9],
                "target_fat_g": float(row[10]) if isinstance(row[10], decimal.Decimal) else row[10],
                "goal": row[11],
                "created_at": row[12].isoformat() if isinstance(row[12], datetime.datetime) else row[12],
                "updated_at": row[13].isoformat() if isinstance(row[13], datetime.datetime) else row[13]
            }
            meal_plans.append(meal_plan)
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
        meal_plan = {
                "id": plan_result[0], "user_id": plan_result[1], "plan_name": plan_result[2],
                "start_date": plan_result[3].isoformat() if isinstance(plan_result[3], datetime.date) else plan_result[3],
                "end_date": plan_result[4].isoformat() if isinstance(plan_result[4], datetime.date) else plan_result[4],
                "description": plan_result[5], "is_active": plan_result[6],
                "target_calories": plan_result[7],
                "target_protein_g": float(plan_result[8]) if isinstance(plan_result[8], decimal.Decimal) else plan_result[8],
                "target_carbs_g": float(plan_result[9]) if isinstance(plan_result[9], decimal.Decimal) else plan_result[9],
                "target_fat_g": float(plan_result[10]) if isinstance(plan_result[10], decimal.Decimal) else plan_result[10],
                "goal": plan_result[11],
                "created_at": plan_result[12].isoformat() if isinstance(plan_result[12], datetime.datetime) else plan_result[12],
                "updated_at": plan_result[13].isoformat() if isinstance(plan_result[13], datetime.datetime) else plan_result[13],
                "items": [] # Inicializar lista de items
        }

        if with_items:
            # Importar y llamar a la función corregida del servicio de items
            from back_end.gym.services.nutrition.meal_plan_items_service import get_meal_plan_items
            items = get_meal_plan_items(meal_plan_id) # Ya devuelve List[Dict] formateada
            logger.info(f"Plan {meal_plan_id}: Obtenidos {len(items)} items.")
            meal_plan["items"] = items # Asignar la lista directamente

        return meal_plan
    except Exception as e:
        logger.exception(f"Error al obtener plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise ValueError(f"Error al obtener plan de comida: {e}")


def update_meal_plan(meal_plan_id: int, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza un plan de comida existente y reemplaza sus items si se proporcionan.
    """
    conn = None
    cur = None
    try:
        from back_end.gym.config import DB_CONFIG
        import psycopg2

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, gym, public")

        # --- 1. Actualizar el plan principal (si hay datos para ello) ---
        plan_update_fields = []
        plan_params = []
        plan_keys = ['plan_name', 'start_date', 'end_date', 'description', 'is_active',
                     'target_calories', 'target_protein_g', 'target_carbs_g', 'target_fat_g', 'goal']

        for key in plan_keys:
            if key in update_data and update_data[key] is not None:
                plan_update_fields.append(f"{key} = %s")
                plan_params.append(update_data[key])

        updated_plan_data = None
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
                logger.warning(f"Plan {meal_plan_id} no encontrado o no pertenece al usuario {user_id} para actualizar.")
                conn.rollback()
                return None

            updated_plan_data = { # Mapeo del resultado
                "id": plan_result[0], "user_id": plan_result[1], "plan_name": plan_result[2],
                "start_date": plan_result[3], "end_date": plan_result[4], "description": plan_result[5],
                "is_active": plan_result[6], "target_calories": plan_result[7],
                "target_protein_g": plan_result[8], "target_carbs_g": plan_result[9],
                "target_fat_g": plan_result[10], "goal": plan_result[11],
                "created_at": plan_result[12], "updated_at": plan_result[13]
            }
            logger.info(f"Plan principal ID {meal_plan_id} actualizado.")
        else:
             logger.debug(f"No se proporcionaron campos para actualizar el plan principal {meal_plan_id}.")


        # --- 2. Reemplazar items si se proporcionan en update_data ---
        if 'items' in update_data and update_data['items'] is not None:
            items_data = update_data['items']
            logger.info(f"Plan ID {meal_plan_id}: Reemplazando items. Eliminando antiguos...")

            cur.execute("DELETE FROM nutrition.meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
            deleted_count = cur.rowcount
            logger.info(f"Plan ID {meal_plan_id}: Eliminados {deleted_count} items antiguos.")

            if items_data:
                # Usar columnas correctas y convertir meal_type a str
                item_query = """
                INSERT INTO nutrition.meal_plan_items
                    (meal_plan_id, meal_id, plan_date, day_of_week, meal_type, quantity, unit, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                items_to_insert = []
                for item in items_data:
                    meal_id = item.get('meal_id')
                    plan_date = item.get('plan_date')
                    day_of_week = item.get('day_of_week')
                    meal_type = item.get('meal_type') # Enum
                    quantity = item.get('quantity', 100.0)
                    unit = item.get('unit', 'g')
                    notes = item.get('notes')

                    if not meal_id: # Validar mínimo necesario
                        logger.warning(f"Plan ID {meal_plan_id} (update): Item sin meal_id, omitiendo: {item}")
                        continue

                    item_params = ( meal_plan_id, meal_id, plan_date, day_of_week,
                                  str(meal_type) if meal_type else None, # Convertir Enum a str
                                  quantity, unit, notes )
                    items_to_insert.append(item_params)

                if items_to_insert:
                    cur.executemany(item_query, items_to_insert)
                    logger.info(f"Plan ID {meal_plan_id}: Insertados {len(items_to_insert)} nuevos items.")
                else:
                     logger.warning(f"Plan ID {meal_plan_id}: No se insertaron nuevos items (lista vacía o inválidos).")
            else:
                 logger.info(f"Plan ID {meal_plan_id}: Lista de items vacía proporcionada, no se insertaron nuevos.")

        # --- 3. Confirmar la transacción ---
        conn.commit()
        logger.info(f"Plan de comida ID {meal_plan_id} actualizado con éxito para usuario {user_id}.")

        # --- 4. Devolver datos actualizados del plan (solo el plan base) ---
        if updated_plan_data is None:
             # Si solo se actualizaron items, obtener datos actuales del plan
             current_plan_base = get_meal_plan(meal_plan_id, user_id, with_items=False)
             if current_plan_base is None:
                  raise ValueError(f"No se pudo recuperar el plan {meal_plan_id} después de actualizar items.")
             updated_plan_data = current_plan_base

        # Formatear respuesta (solo datos del plan)
        for key, value in updated_plan_data.items():
             if isinstance(value, datetime.date):
                  updated_plan_data[key] = value.isoformat()
             elif isinstance(value, decimal.Decimal):
                  updated_plan_data[key] = float(value)

        return updated_plan_data

    except psycopg2.Error as db_error:
        if conn: conn.rollback()
        logger.error(f"Error de base de datos al actualizar plan {meal_plan_id}: {db_error}")
        raise ValueError(f"Error de base de datos: {db_error}")
    except Exception as e:
        if conn: conn.rollback()
        logger.exception(f"Error inesperado al actualizar plan {meal_plan_id}: {e}")
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()


def delete_meal_plan(meal_plan_id: int, user_id: str) -> bool:
    """Elimina un plan de comida y sus items asociados en una transacción."""
    conn = None
    cur = None
    try:
        from back_end.gym.config import DB_CONFIG
        import psycopg2

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, gym, public")

        # Verificar pertenencia
        cur.execute("SELECT id FROM nutrition.meal_plans WHERE id = %s AND user_id = %s", (meal_plan_id, str(user_id)))
        if cur.fetchone() is None:
             logger.warning(f"Intento de eliminar plan {meal_plan_id} fallido: No encontrado o no pertenece al usuario {user_id}.")
             conn.rollback() # No olvidar rollback si no se hace nada
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
            # Esto no debería ocurrir si la verificación inicial funcionó
            logger.error(f"Error al eliminar plan {meal_plan_id} después de la verificación.")

        return deleted

    except psycopg2.Error as db_error:
        if conn: conn.rollback()
        logger.error(f"Error de base de datos al eliminar plan {meal_plan_id}: {db_error}")
        raise ValueError(f"Error de base de datos: {db_error}")
    except Exception as e:
        if conn: conn.rollback()
        logger.exception(f"Error inesperado al eliminar plan {meal_plan_id}: {e}")
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()