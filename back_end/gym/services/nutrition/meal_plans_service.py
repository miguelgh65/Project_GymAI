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
        # Considera añadir CREATE SCHEMA IF NOT EXISTS nutrition; en tu init-db.sql
        cur.execute("SET search_path TO nutrition, public")

        # --- 1. Insertar el plan principal ---
        plan_query = """
        INSERT INTO meal_plans
            (user_id, plan_name, start_date, end_date, description, is_active,
             target_calories, target_protein_g, target_carbs_g, target_fat_g, goal)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, plan_name, start_date, end_date, description, is_active,
                  target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
                  created_at, updated_at
        """

        plan_params = (
            str(user_id),  # Convertir user_id a string si es necesario
            plan_data.get('plan_name'), # Pydantic ya validó que existe
            plan_data.get('start_date'),
            plan_data.get('end_date'),
            plan_data.get('description'),
            plan_data.get('is_active', True), # Default si no viene
            # Obtener targets y goal, Pydantic ya validó tipos o puso None
            plan_data.get('target_calories'),
            plan_data.get('target_protein_g'),
            plan_data.get('target_carbs_g'),
            plan_data.get('target_fat_g'),
            plan_data.get('goal')
        )

        cur.execute(plan_query, plan_params)
        plan_result = cur.fetchone()

        if not plan_result:
            # Si falla aquí, no se creó el plan, la transacción hará rollback
            logger.error(f"Fallo al insertar el registro principal del plan para usuario {user_id}")
            raise ValueError("Error al crear el registro principal del plan")

        # Extraer ID y mapear resultado a un diccionario inicial
        plan_id = plan_result[0]
        created_plan = {
            "id": plan_result[0],
            "user_id": plan_result[1],
            "plan_name": plan_result[2],
            "start_date": plan_result[3],
            "end_date": plan_result[4],
            "description": plan_result[5],
            "is_active": plan_result[6],
            "target_calories": plan_result[7],
            "target_protein_g": plan_result[8],
            "target_carbs_g": plan_result[9],
            "target_fat_g": plan_result[10],
            "goal": plan_result[11],
            "created_at": plan_result[12],
            "updated_at": plan_result[13]
        }
        logger.info(f"Plan principal ID {plan_id} insertado para usuario {user_id}.")


        # --- 2. Procesar y guardar cada item asociado ---
        items_data = plan_data.get('items', []) # Obtener items (lista vacía si no viene)

        if items_data: # Solo procesar si la lista no está vacía
            logger.info(f"Plan ID {plan_id}: Procesando {len(items_data)} items.")

            # Preparar la query de inserción de items una sola vez
            # *** ASEGÚRATE QUE LAS COLUMNAS COINCIDAN CON TU TABLA meal_plan_items ***
            item_query = """
            INSERT INTO meal_plan_items
                (meal_plan_id, meal_id, plan_date, meal_type, quantity, unit, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            # Adaptar si usas day_of_week en lugar de plan_date, o si unit no existe, etc.

            items_to_insert = []
            for item in items_data:
                 # Pydantic ya validó la estructura de cada 'item' como MealPlanItemInput
                 # Extraemos los valores necesarios. Usamos .get por seguridad extra.

                 meal_id = item.get('meal_id')
                 plan_date = item.get('plan_date') # Asumiendo que envías plan_date
                 meal_type = item.get('meal_type') # Asumiendo que envías meal_type
                 quantity = item.get('quantity', 100.0) # Default si falta
                 unit = item.get('unit', 'g') # Default si falta
                 notes = item.get('notes')

                 # Doble check (aunque Pydantic ya lo hizo)
                 if not all([meal_id is not None, plan_date is not None, meal_type is not None]):
                      logger.warning(f"Plan ID {plan_id}: Item incompleto (meal_id, plan_date, meal_type requeridos), omitiendo: {item}")
                      continue # Saltar este item

                 # Crear tupla de parámetros para este item
                 # *** ASEGÚRATE QUE EL ORDEN COINCIDA CON item_query ***
                 item_params = (
                      plan_id,
                      meal_id,
                      plan_date, # Objeto date de Pydantic
                      str(meal_type), # Convertir Enum a string si es necesario para DB
                      quantity,
                      unit,
                      notes
                 )
                 items_to_insert.append(item_params)

            # Insertar todos los items válidos de una vez (más eficiente) si hay alguno
            if items_to_insert:
                cur.executemany(item_query, items_to_insert)
                logger.info(f"Plan ID {plan_id}: Insertados {len(items_to_insert)} items en meal_plan_items.")
            else:
                 logger.warning(f"Plan ID {plan_id}: No se insertaron items (lista vacía o todos inválidos).")


        # --- 3. Confirmar la transacción ---
        conn.commit()
        logger.info(f"Plan de comida ID {plan_id} y sus items asociados creados con éxito para usuario {user_id}.")

        # --- 4. Formatear respuesta ---
        # Convertir tipos de datos para serialización JSON si es necesario
        for key, value in created_plan.items():
            if isinstance(value, datetime.date):
                created_plan[key] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                 created_plan[key] = float(value)

        return created_plan

    except psycopg2.Error as db_error:
        if conn:
            conn.rollback() # Deshacer cambios en caso de error DB
        logger.error(f"Error de base de datos al crear plan de comida para usuario {user_id}: {db_error}")
        # Podrías querer lanzar un error más específico o devolver None/dict vacío
        raise ValueError(f"Error de base de datos: {db_error}") # Relanzar para que la ruta lo maneje
    except Exception as e:
        if conn:
            conn.rollback() # Deshacer cambios en caso de cualquier otro error
        logger.error(f"Error inesperado al crear plan de comida para usuario {user_id}: {e}")
        raise # Relanzar para que la ruta lo maneje
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# --- Funciones list_meal_plans, get_meal_plan, update_meal_plan, delete_meal_plan ---
# --- Deberían permanecer mayormente igual, pero asegúrate de que manejen ---
# --- correctamente la conversión de tipos para JSON y la lógica de items ---
# --- en get_meal_plan (con JOINs) y update_meal_plan (reemplazo de items) ---
# ---------------------------------------------------------------------------

# Ejemplo de cómo podría ser list_meal_plans con formateo
def list_meal_plans(user_id: str, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Lista todos los planes de comida del usuario."""
    try:
        query = """
        SELECT id, user_id, plan_name, start_date, end_date, description, is_active,
               target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
               created_at, updated_at
        FROM meal_plans
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
                "id": row[0],
                "user_id": row[1],
                "plan_name": row[2],
                "start_date": row[3].isoformat() if isinstance(row[3], datetime.date) else row[3],
                "end_date": row[4].isoformat() if isinstance(row[4], datetime.date) else row[4],
                "description": row[5],
                "is_active": row[6],
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
        # Obtener el plan de comida principal
        plan_query = """
        SELECT id, user_id, plan_name, start_date, end_date, description, is_active,
               target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
               created_at, updated_at
        FROM meal_plans
        WHERE id = %s AND user_id = %s
        """
        logger.debug(f"Obteniendo plan {meal_plan_id} para usuario {user_id}")
        plan_result = execute_db_query(plan_query, (meal_plan_id, str(user_id)), fetch_one=True)

        if not plan_result:
            logger.warning(f"Plan {meal_plan_id} no encontrado para usuario {user_id}")
            return None

        meal_plan = {
                "id": plan_result[0],
                "user_id": plan_result[1],
                "plan_name": plan_result[2],
                "start_date": plan_result[3].isoformat() if isinstance(plan_result[3], datetime.date) else plan_result[3],
                "end_date": plan_result[4].isoformat() if isinstance(plan_result[4], datetime.date) else plan_result[4],
                "description": plan_result[5],
                "is_active": plan_result[6],
                "target_calories": plan_result[7],
                "target_protein_g": float(plan_result[8]) if isinstance(plan_result[8], decimal.Decimal) else plan_result[8],
                "target_carbs_g": float(plan_result[9]) if isinstance(plan_result[9], decimal.Decimal) else plan_result[9],
                "target_fat_g": float(plan_result[10]) if isinstance(plan_result[10], decimal.Decimal) else plan_result[10],
                "goal": plan_result[11],
                "created_at": plan_result[12].isoformat() if isinstance(plan_result[12], datetime.datetime) else plan_result[12],
                "updated_at": plan_result[13].isoformat() if isinstance(plan_result[13], datetime.datetime) else plan_result[13],
                "items": [] # Inicializar lista de items
        }

        # Obtener los elementos del plan si se solicita
        if with_items:
            # Usar una importación local para evitar dependencia circular si es necesario
            from back_end.gym.services.nutrition.meal_plan_items_service import get_meal_plan_items_with_details
            # Asumir que existe una función que hace JOIN con meals para obtener detalles
            items = get_meal_plan_items_with_details(meal_plan_id)
            logger.info(f"Plan {meal_plan_id}: Encontrados {len(items)} items con detalles.")

            # Formatear items para la respuesta
            formatted_items = []
            for item_row in items:
                 # Asumiendo que get_meal_plan_items_with_details devuelve diccionarios
                 # con claves que coinciden con MealPlanItemResponse
                 formatted_item = {
                      "id": item_row.get('id'),
                      "meal_plan_id": item_row.get('meal_plan_id'),
                      "meal_id": item_row.get('meal_id'),
                      "plan_date": item_row.get('plan_date').isoformat() if isinstance(item_row.get('plan_date'), datetime.date) else item_row.get('plan_date'),
                      "day_of_week": item_row.get('day_of_week'), # Si existe
                      "meal_type": item_row.get('meal_type'),
                      "quantity": float(item_row.get('quantity')) if isinstance(item_row.get('quantity'), decimal.Decimal) else item_row.get('quantity'),
                      "unit": item_row.get('unit'),
                      "notes": item_row.get('notes'),
                      "meal_name": item_row.get('meal_name'), # Del JOIN
                      # Macros calculados (si el JOIN los calcula o la función los añade)
                      "calories": float(item_row.get('calories')) if isinstance(item_row.get('calories'), decimal.Decimal) else item_row.get('calories'),
                      "protein_g": float(item_row.get('protein_g')) if isinstance(item_row.get('protein_g'), decimal.Decimal) else item_row.get('protein_g'),
                      "carbohydrates_g": float(item_row.get('carbohydrates_g')) if isinstance(item_row.get('carbohydrates_g'), decimal.Decimal) else item_row.get('carbohydrates_g'),
                      "fat_g": float(item_row.get('fat_g')) if isinstance(item_row.get('fat_g'), decimal.Decimal) else item_row.get('fat_g'),
                      "created_at": item_row.get('created_at').isoformat() if isinstance(item_row.get('created_at'), datetime.datetime) else item_row.get('created_at'),
                      "updated_at": item_row.get('updated_at').isoformat() if isinstance(item_row.get('updated_at'), datetime.datetime) else item_row.get('updated_at'),
                 }
                 formatted_items.append(formatted_item)

            meal_plan["items"] = formatted_items

        return meal_plan
    except Exception as e:
        logger.error(f"Error al obtener plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise


def update_meal_plan(meal_plan_id: int, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza un plan de comida existente y reemplaza sus items si se proporcionan.
    Espera que update_data['items'] (si existe) sea una lista de dicts
    que coincidan con el modelo MealPlanItemInput.
    """
    conn = None
    cur = None
    try:
        from back_end.gym.config import DB_CONFIG
        import psycopg2

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, public")

        # --- 1. Actualizar el plan principal (si hay datos para ello) ---
        plan_update_fields = []
        plan_params = []
        plan_keys = ['plan_name', 'start_date', 'end_date', 'description', 'is_active',
                     'target_calories', 'target_protein_g', 'target_carbs_g', 'target_fat_g', 'goal']

        for key in plan_keys:
            if key in update_data and update_data[key] is not None: # Solo incluir si está presente y no es None explícito
                plan_update_fields.append(f"{key} = %s")
                plan_params.append(update_data[key])

        updated_plan_data = None
        if plan_update_fields:
            plan_update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_plan_query = f"""
            UPDATE meal_plans
            SET {", ".join(plan_update_fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, plan_name, start_date, end_date, description, is_active,
                      target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
                      created_at, updated_at
            """
            plan_params.extend([meal_plan_id, str(user_id)])

            logger.debug(f"Actualizando plan principal {meal_plan_id}")
            cur.execute(update_plan_query, tuple(plan_params))
            plan_result = cur.fetchone()

            if not plan_result:
                logger.warning(f"Plan {meal_plan_id} no encontrado o no pertenece al usuario {user_id} para actualizar.")
                conn.rollback()
                return None # O lanzar un error apropiado

            # Guardar datos actualizados del plan para la respuesta final
            updated_plan_data = {
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
        if 'items' in update_data and update_data['items'] is not None: # Solo si 'items' existe y no es None
            items_data = update_data['items']
            logger.info(f"Plan ID {meal_plan_id}: Reemplazando items. Eliminando antiguos...")

            # Eliminar items existentes
            cur.execute("DELETE FROM meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
            deleted_count = cur.rowcount
            logger.info(f"Plan ID {meal_plan_id}: Eliminados {deleted_count} items antiguos.")

            # Insertar los nuevos items (similar a create_meal_plan)
            if items_data: # Solo insertar si la nueva lista no está vacía
                item_query = """
                INSERT INTO meal_plan_items
                    (meal_plan_id, meal_id, plan_date, meal_type, quantity, unit, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                items_to_insert = []
                for item in items_data:
                    meal_id = item.get('meal_id')
                    plan_date = item.get('plan_date')
                    meal_type = item.get('meal_type')
                    quantity = item.get('quantity', 100.0)
                    unit = item.get('unit', 'g')
                    notes = item.get('notes')

                    if not all([meal_id is not None, plan_date is not None, meal_type is not None]):
                        logger.warning(f"Plan ID {meal_plan_id} (update): Item incompleto, omitiendo: {item}")
                        continue

                    item_params = ( plan_id, meal_id, plan_date, str(meal_type), quantity, unit, notes )
                    items_to_insert.append(item_params)

                if items_to_insert:
                    cur.executemany(item_query, items_to_insert)
                    logger.info(f"Plan ID {meal_plan_id}: Insertados {len(items_to_insert)} nuevos items.")
                else:
                     logger.warning(f"Plan ID {meal_plan_id}: No se insertaron nuevos items (lista vacía o todos inválidos).")
            else:
                 logger.info(f"Plan ID {meal_plan_id}: Se proporcionó una lista de items vacía, no se insertaron nuevos items.")


        # --- 3. Confirmar la transacción ---
        conn.commit()
        logger.info(f"Plan de comida ID {meal_plan_id} actualizado con éxito para usuario {user_id}.")

        # --- 4. Devolver datos actualizados del plan ---
        # Si no se actualizó el plan principal pero sí los items, obtener los datos actuales del plan
        if updated_plan_data is None:
             current_plan = get_meal_plan(meal_plan_id, user_id, with_items=False) # Obtener solo el plan base
             if current_plan is None:
                  # Esto no debería pasar si la verificación inicial funcionó, pero por si acaso
                  raise ValueError(f"No se pudo recuperar el plan {meal_plan_id} después de actualizar items.")
             updated_plan_data = current_plan

        # Formatear respuesta
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
        logger.error(f"Error inesperado al actualizar plan {meal_plan_id}: {e}")
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
        cur.execute("SET search_path TO nutrition, public")

        # Verificar que el plan pertenece al usuario antes de borrar
        cur.execute("SELECT id FROM meal_plans WHERE id = %s AND user_id = %s", (meal_plan_id, str(user_id)))
        if cur.fetchone() is None:
             logger.warning(f"Intento de eliminar plan {meal_plan_id} fallido: No encontrado o no pertenece al usuario {user_id}.")
             return False # Indicar que no se encontró/autorizó

        # Primero eliminar los elementos del plan (CASCADE podría hacer esto automáticamente si está configurado)
        logger.debug(f"Eliminando items para plan {meal_plan_id}")
        cur.execute("DELETE FROM meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
        deleted_items_count = cur.rowcount
        logger.info(f"Eliminados {deleted_items_count} items para plan {meal_plan_id}")

        # Luego eliminar el plan
        logger.debug(f"Eliminando plan principal {meal_plan_id}")
        cur.execute("DELETE FROM meal_plans WHERE id = %s AND user_id = %s", (meal_plan_id, str(user_id)))
        deleted_plan_count = cur.rowcount

        conn.commit()
        logger.info(f"Plan ID {meal_plan_id} eliminado con éxito.")

        return deleted_plan_count > 0 # Devuelve True si se eliminó el plan

    except psycopg2.Error as db_error:
        if conn: conn.rollback()
        logger.error(f"Error de base de datos al eliminar plan {meal_plan_id}: {db_error}")
        raise ValueError(f"Error de base de datos: {db_error}")
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error inesperado al eliminar plan {meal_plan_id}: {e}")
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()