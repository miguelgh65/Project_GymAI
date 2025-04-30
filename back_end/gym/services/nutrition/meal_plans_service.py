# back_end/gym/services/nutrition/meal_plans_service.py
import logging
from typing import Optional, List, Dict, Any
import decimal
import datetime

# Usar ruta absoluta
from back_end.gym.services.db_utils import execute_db_query
# Importar modelos para type hints si es necesario (opcional pero bueno)
# from back_end.gym.models.nutrition_schemas import MealPlanItemInput # Ya no parece usarse aquí directamente

# Configurar logger
logger = logging.getLogger(__name__)

# Helper para formatear resultados de forma segura
def format_plan_result(row: tuple) -> Dict[str, Any]:
    """Formatea una fila de resultado de la BD a un diccionario de plan."""
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
    # Eliminar claves con valor None para limpieza si se desea
    # return {k: v for k, v in meal_plan.items() if v is not None}
    return meal_plan


def create_meal_plan(user_id: str, plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Crea un nuevo plan de comida y sus items asociados en una transacción.
    """
    # DEBUG LOG INICIO FUNCIÓN
    print(">>>>>>>>>>>>>>> [DEBUG] Entrando en SERVICIO MealPlansService.create_meal_plan")
    logger.info(f"[SERVICE create_meal_plan] Intentando crear plan para user_id: {user_id}. Datos recibidos: {plan_data}")

    conn = None
    cur = None
    plan_id = None # Inicializar plan_id

    try:
        # Importar DB_CONFIG aquí o pasarlo como argumento si es necesario
        from back_end.gym.config import DB_CONFIG
        import psycopg2

        # DEBUG LOG ANTES DE CONECTAR
        print("[DEBUG] MealPlansService: Conectando a la BD...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("[DEBUG] MealPlansService: Conexión BD establecida.")

        # Asegurarse de que estamos en el esquema correcto (si aplica)
        print("[DEBUG] MealPlansService: Estableciendo search_path...")
        cur.execute("SET search_path TO nutrition, gym, public") # Incluir gym por si acaso
        print("[DEBUG] MealPlansService: search_path establecido.")

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

        # DEBUG LOG ANTES DE INSERTAR PLAN
        print(f"[DEBUG] MealPlansService: Intentando ejecutar INSERT plan principal. Params: {plan_params}")
        try:
            cur.execute(plan_query, plan_params)
            plan_result = cur.fetchone()
            print(f"[DEBUG] MealPlansService: INSERT plan principal ejecutado. Resultado fetchone(): {plan_result}")
        except Exception as insert_plan_error:
            print(f"!!!!!!!!!!!!!!! ERROR AL EJECUTAR INSERT PLAN: {insert_plan_error}")
            logger.exception("Error detallado al ejecutar insert de plan principal:")
            raise # Relanzar para que el bloque principal haga rollback

        if not plan_result:
            logger.error(f"Fallo al insertar el registro principal del plan para usuario {user_id} (plan_result vacío)")
            # Considerar si esto debería ser un error o no. Si RETURNING no devuelve nada, es un error.
            raise ValueError("Error crítico al crear el registro principal del plan (RETURNING vacío)")

        plan_id = plan_result[0]
        created_plan = format_plan_result(plan_result)
        print(f"[DEBUG] MealPlansService: Plan principal ID {plan_id} insertado y formateado.")
        logger.info(f"Plan principal ID {plan_id} insertado para usuario {user_id}.")


        # --- 2. Procesar y guardar cada item asociado ---
        items_data = plan_data.get('items', [])
        print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: Procesando {len(items_data)} items recibidos.")

        if items_data:
            # Usar columnas de init-db.sql: plan_date, day_of_week, meal_type, quantity, unit, notes
            item_query = """
            INSERT INTO nutrition.meal_plan_items
                (meal_plan_id, meal_id, plan_date, day_of_week, meal_type, quantity, unit, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            items_to_insert = []
            for idx, item in enumerate(items_data):
                print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: Procesando item #{idx}: {item}")
                # Pydantic ya validó 'item' contra MealPlanItemInput (o similar en la ruta)
                meal_id = item.get('meal_id')
                plan_date = item.get('plan_date')
                day_of_week = item.get('day_of_week') # Podría ser None
                meal_type = item.get('meal_type') # Este es el Enum/str de Pydantic
                quantity = item.get('quantity') # Dejar que la BD use default si es None? O validar?
                unit = item.get('unit')         # Dejar que la BD use default si es None? O validar?
                notes = item.get('notes')       # Podría ser None

                # Requiere al menos meal_id y ¿algo más?
                if not meal_id:
                    print(f"[WARN] MealPlansService: Plan ID {plan_id}: Item #{idx} sin meal_id, omitiendo: {item}")
                    logger.warning(f"Plan ID {plan_id}: Item sin meal_id, omitiendo: {item}")
                    continue
                # Validación adicional si es necesaria (ej: quantity > 0)
                if quantity is None or quantity <= 0:
                     print(f"[WARN] MealPlansService: Plan ID {plan_id}: Item #{idx} con quantity inválida ({quantity}), omitiendo: {item}")
                     logger.warning(f"Plan ID {plan_id}: Item con quantity inválida ({quantity}), omitiendo: {item}")
                     continue


                # Crear tupla - Convertir meal_type a string si no es None
                item_params = (
                    plan_id, meal_id, plan_date, day_of_week,
                    str(meal_type) if meal_type else None, # Convertir Enum/valor a str
                    quantity, unit, notes
                )
                items_to_insert.append(item_params)
                print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: Item #{idx} preparado para insertar: {item_params}")

            if items_to_insert:
                print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: Intentando ejecutar INSERT MANY para {len(items_to_insert)} items.")
                try:
                    cur.executemany(item_query, items_to_insert)
                    print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: INSERT MANY items ejecutado.")
                    logger.info(f"Plan ID {plan_id}: Insertados {len(items_to_insert)} items en meal_plan_items.")
                except Exception as insert_items_error:
                     print(f"!!!!!!!!!!!!!!! ERROR AL EJECUTAR INSERT MANY ITEMS: {insert_items_error}")
                     logger.exception(f"Error detallado al ejecutar insert many items para plan {plan_id}:")
                     raise # Relanzar para que el bloque principal haga rollback
            else:
                 print(f"[WARN] MealPlansService: Plan ID {plan_id}: No se prepararon items válidos para insertar.")
                 logger.warning(f"Plan ID {plan_id}: No se insertaron items (lista vacía o todos inválidos).")
        else:
             print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: No se proporcionaron items en la petición.")


        # --- 3. Confirmar la transacción ---
        print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: Intentando hacer commit de la transacción.")
        try:
            conn.commit()
            print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: Commit realizado con éxito.")
            logger.info(f"Plan de comida ID {plan_id} y sus items asociados creados con éxito para usuario {user_id}.")
        except Exception as commit_error:
            print(f"!!!!!!!!!!!!!!! ERROR AL HACER COMMIT: {commit_error}")
            logger.exception(f"Error detallado al hacer commit para plan {plan_id}:")
            # El rollback se hará en el bloque finally general si falla aquí
            raise # Relanzar para que el bloque finally haga rollback y se reporte el error

        # --- 4. Devolver respuesta (ya formateada antes) ---
        print(f"[DEBUG] MealPlansService: Plan ID {plan_id}: Devolviendo plan creado.")
        return created_plan # Devolver el plan base formateado

    except psycopg2.Error as db_error:
        print(f"!!!!!!!!!!!!!!! ERROR DE BASE DE DATOS (psycopg2.Error): {db_error}")
        if conn:
            print("[DEBUG] MealPlansService: Realizando rollback por psycopg2.Error...")
            conn.rollback()
            print("[DEBUG] MealPlansService: Rollback completado.")
        logger.error(f"Error de base de datos al crear plan de comida para usuario {user_id}: {db_error}")
        # Devolvemos None o relanzamos una excepción específica de la app si queremos
        # raise ValueError(f"Error de base de datos: {db_error}")
        return None # Opcional: devolver None en lugar de error 500
    except ValueError as val_error: # Capturar ValueError específicos si los lanzamos
        print(f"!!!!!!!!!!!!!!! ERROR DE VALIDACIÓN O LÓGICA (ValueError): {val_error}")
        if conn:
            print("[DEBUG] MealPlansService: Realizando rollback por ValueError...")
            conn.rollback()
            print("[DEBUG] MealPlansService: Rollback completado.")
        logger.error(f"Error de valor al crear plan de comida para usuario {user_id}: {val_error}")
        # raise # Relanzar si queremos que la ruta devuelva 4xx o 500
        return None
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR INESPERADO (Exception): {e}")
        if conn:
            print("[DEBUG] MealPlansService: Realizando rollback por Exception general...")
            conn.rollback()
            print("[DEBUG] MealPlansService: Rollback completado.")
        logger.exception(f"Error inesperado al crear plan de comida para usuario {user_id}: {e}")
        raise # Relanzar para que la ruta devuelva 500
    finally:
        # DEBUG LOG ANTES DE CERRAR CURSOR Y CONEXIÓN
        print("[DEBUG] MealPlansService: Bloque finally - cerrando cursor y conexión si existen.")
        if cur:
            cur.close()
            print("[DEBUG] MealPlansService: Cursor cerrado.")
        if conn:
            conn.close()
            print("[DEBUG] MealPlansService: Conexión BD cerrada.")
        print(">>>>>>>>>>>>>>> [DEBUG] Saliendo de SERVICIO MealPlansService.create_meal_plan")


def list_meal_plans(user_id: str, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Lista todos los planes de comida del usuario."""
    print(f">>> [DEBUG] list_meal_plans para user_id: {user_id}, is_active: {is_active}")
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
        print(f"[DEBUG] list_meal_plans: Query: {query}, Params: {tuple(params)}")
        results = execute_db_query(query, tuple(params), fetch_all=True)
        print(f"[DEBUG] list_meal_plans: Obtenidos {len(results)} resultados de BD.")
        logger.info(f"Encontrados {len(results)} planes para usuario {user_id}")

        meal_plans = [format_plan_result(row) for row in results]
        print(f"[DEBUG] list_meal_plans: Devolviendo {len(meal_plans)} planes formateados.")
        return meal_plans
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR en list_meal_plans para user {user_id}: {e}")
        logger.error(f"Error al listar planes de comida para usuario {user_id}: {e}")
        raise


def get_meal_plan(meal_plan_id: int, user_id: str, with_items: bool = True) -> Optional[Dict[str, Any]]:
    """Obtiene un plan de comida por su ID, opcionalmente incluyendo todos sus elementos/comidas."""
    print(f">>> [DEBUG] get_meal_plan ID: {meal_plan_id} para user_id: {user_id}, with_items: {with_items}")
    try:
        plan_query = """
        SELECT id, user_id, plan_name, start_date, end_date, description, is_active,
               target_calories, target_protein_g, target_carbs_g, target_fat_g, goal,
               created_at, updated_at
        FROM nutrition.meal_plans
        WHERE id = %s AND user_id = %s
        """
        logger.debug(f"Obteniendo plan {meal_plan_id} para usuario {user_id}")
        print(f"[DEBUG] get_meal_plan: Query: {plan_query}, Params: {(meal_plan_id, str(user_id))}")
        plan_result = execute_db_query(plan_query, (meal_plan_id, str(user_id)), fetch_one=True)
        print(f"[DEBUG] get_meal_plan: Resultado BD: {plan_result}")

        if not plan_result:
            logger.warning(f"Plan {meal_plan_id} no encontrado para usuario {user_id}")
            print(f"[DEBUG] get_meal_plan: Plan {meal_plan_id} no encontrado para usuario {user_id}.")
            return None

        # Mapeo inicial del plan base
        meal_plan = format_plan_result(plan_result)
        meal_plan["items"] = [] # Inicializar lista de items
        print(f"[DEBUG] get_meal_plan: Plan base formateado: {meal_plan}")

        if with_items:
            print(f"[DEBUG] get_meal_plan: Obteniendo items para plan {meal_plan_id}...")
            # Importar y llamar a la función corregida del servicio de items
            try:
                from back_end.gym.services.nutrition.meal_plan_items_service import get_meal_plan_items
                items = get_meal_plan_items(meal_plan_id) # Ya devuelve List[Dict] formateada
                print(f"[DEBUG] get_meal_plan: Obtenidos {len(items)} items.")
                logger.info(f"Plan {meal_plan_id}: Obtenidos {len(items)} items.")
                meal_plan["items"] = items # Asignar la lista directamente
            except Exception as item_error:
                 print(f"!!!!!!!!!!!!!!! ERROR al obtener items para plan {meal_plan_id}: {item_error}")
                 logger.exception(f"Error al obtener items para plan {meal_plan_id}: {item_error}")
                 # Decidir si devolver el plan sin items o relanzar el error
                 # raise ValueError(f"Error al obtener items: {item_error}")
        else:
             print(f"[DEBUG] get_meal_plan: No se solicitó obtener items (with_items=False).")

        print(f"[DEBUG] get_meal_plan: Devolviendo plan completo.")
        return meal_plan
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR en get_meal_plan para plan {meal_plan_id}, user {user_id}: {e}")
        logger.exception(f"Error al obtener plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise # O devolver None


def update_meal_plan(meal_plan_id: int, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza un plan de comida existente y reemplaza sus items si se proporcionan.
    """
    # DEBUG LOG INICIO FUNCIÓN
    print(">>>>>>>>>>>>>>> [DEBUG] Entrando en SERVICIO MealPlansService.update_meal_plan")
    logger.info(f"[SERVICE update_meal_plan] Intentando actualizar plan ID: {meal_plan_id} para user_id: {user_id}. Datos: {update_data}")

    conn = None
    cur = None
    updated_plan_data = None # Para almacenar el plan actualizado si la base se modifica

    try:
        from back_end.gym.config import DB_CONFIG
        import psycopg2

        # DEBUG LOG ANTES DE CONECTAR
        print("[DEBUG] MealPlansService (Update): Conectando a la BD...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("[DEBUG] MealPlansService (Update): Conexión BD establecida.")
        print("[DEBUG] MealPlansService (Update): Estableciendo search_path...")
        cur.execute("SET search_path TO nutrition, gym, public")
        print("[DEBUG] MealPlansService (Update): search_path establecido.")

        # --- 1. Actualizar el plan principal (si hay datos para ello) ---
        plan_update_fields = []
        plan_params = []
        plan_keys = ['plan_name', 'start_date', 'end_date', 'description', 'is_active',
                     'target_calories', 'target_protein_g', 'target_carbs_g', 'target_fat_g', 'goal']

        for key in plan_keys:
            if key in update_data and update_data[key] is not None: # Solo actualizar si se proporciona y no es None explícito
                plan_update_fields.append(f"{key} = %s")
                plan_params.append(update_data[key])

        if plan_update_fields:
            print(f"[DEBUG] MealPlansService (Update): Campos a actualizar en plan principal: {plan_update_fields}")
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
            print(f"[DEBUG] MealPlansService (Update): Ejecutando UPDATE plan principal. Query: {update_plan_query[:200]}..., Params: {tuple(plan_params)}")

            try:
                cur.execute(update_plan_query, tuple(plan_params))
                plan_result = cur.fetchone()
                print(f"[DEBUG] MealPlansService (Update): UPDATE plan ejecutado. Resultado: {plan_result}")
            except Exception as update_plan_error:
                print(f"!!!!!!!!!!!!!!! ERROR AL EJECUTAR UPDATE PLAN: {update_plan_error}")
                logger.exception(f"Error detallado al ejecutar update de plan principal {meal_plan_id}:")
                raise # Relanzar para que el bloque principal haga rollback

            if not plan_result:
                logger.warning(f"Plan {meal_plan_id} no encontrado o no pertenece al usuario {user_id} para actualizar.")
                print(f"[WARN] MealPlansService (Update): Plan {meal_plan_id} no encontrado o no pertenece al usuario {user_id}.")
                conn.rollback() # Hacer rollback aquí porque no se puede continuar
                return None

            updated_plan_data = format_plan_result(plan_result)
            print(f"[DEBUG] MealPlansService (Update): Plan principal ID {meal_plan_id} actualizado y formateado.")
            logger.info(f"Plan principal ID {meal_plan_id} actualizado.")
        else:
            print(f"[DEBUG] MealPlansService (Update): No se proporcionaron campos para actualizar el plan principal {meal_plan_id}.")


        # --- 2. Reemplazar items si se proporcionan en update_data ---
        # Comprobar si 'items' está en update_data (incluso si es lista vacía [])
        if 'items' in update_data:
            items_data = update_data['items'] # Puede ser None o []
            print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Clave 'items' encontrada. Reemplazando items. Nuevos items: {items_data}")
            logger.info(f"Plan ID {meal_plan_id}: Reemplazando items.")

            print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Eliminando items antiguos...")
            try:
                cur.execute("DELETE FROM nutrition.meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
                deleted_count = cur.rowcount
                print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: DELETE items ejecutado. Eliminados {deleted_count} items antiguos.")
                logger.info(f"Plan ID {meal_plan_id}: Eliminados {deleted_count} items antiguos.")
            except Exception as delete_items_error:
                 print(f"!!!!!!!!!!!!!!! ERROR AL EJECUTAR DELETE ITEMS ANTIGUOS: {delete_items_error}")
                 logger.exception(f"Error detallado al eliminar items antiguos para plan {meal_plan_id}:")
                 raise # Relanzar para rollback

            # Solo intentar insertar si items_data no es None y no está vacío
            if items_data:
                item_query = """
                INSERT INTO nutrition.meal_plan_items
                    (meal_plan_id, meal_id, plan_date, day_of_week, meal_type, quantity, unit, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                items_to_insert = []
                for idx, item in enumerate(items_data):
                    print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Procesando nuevo item #{idx}: {item}")
                    meal_id = item.get('meal_id')
                    plan_date = item.get('plan_date')
                    day_of_week = item.get('day_of_week')
                    meal_type = item.get('meal_type') # Enum/str
                    quantity = item.get('quantity')
                    unit = item.get('unit')
                    notes = item.get('notes')

                    if not meal_id: # Validar mínimo necesario
                        print(f"[WARN] MealPlansService (Update): Plan ID {meal_plan_id} (update): Item #{idx} sin meal_id, omitiendo: {item}")
                        logger.warning(f"Plan ID {meal_plan_id} (update): Item sin meal_id, omitiendo: {item}")
                        continue
                    if quantity is None or quantity <= 0:
                        print(f"[WARN] MealPlansService (Update): Plan ID {meal_plan_id} (update): Item #{idx} con quantity inválida ({quantity}), omitiendo: {item}")
                        logger.warning(f"Plan ID {meal_plan_id} (update): Item con quantity inválida ({quantity}), omitiendo: {item}")
                        continue

                    item_params = ( meal_plan_id, meal_id, plan_date, day_of_week,
                                    str(meal_type) if meal_type else None, # Convertir Enum/str a str
                                    quantity, unit, notes )
                    items_to_insert.append(item_params)
                    print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Nuevo item #{idx} preparado para insertar: {item_params}")


                if items_to_insert:
                    print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Intentando ejecutar INSERT MANY para {len(items_to_insert)} nuevos items.")
                    try:
                        cur.executemany(item_query, items_to_insert)
                        print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: INSERT MANY nuevos items ejecutado.")
                        logger.info(f"Plan ID {meal_plan_id}: Insertados {len(items_to_insert)} nuevos items.")
                    except Exception as insert_new_items_error:
                        print(f"!!!!!!!!!!!!!!! ERROR AL EJECUTAR INSERT MANY NUEVOS ITEMS: {insert_new_items_error}")
                        logger.exception(f"Error detallado al insertar nuevos items para plan {meal_plan_id}:")
                        raise # Relanzar para rollback
                else:
                    print(f"[WARN] MealPlansService (Update): Plan ID {meal_plan_id}: No se prepararon nuevos items válidos para insertar.")
                    logger.warning(f"Plan ID {meal_plan_id}: No se insertaron nuevos items (lista vacía o inválidos).")
            else:
                 print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Lista de items vacía o None proporcionada, no se insertaron nuevos.")
        else:
             print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Clave 'items' no encontrada en update_data. No se modifican items.")


        # --- 3. Confirmar la transacción ---
        print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Intentando hacer commit de la transacción.")
        try:
            conn.commit()
            print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Commit realizado con éxito.")
            logger.info(f"Plan de comida ID {meal_plan_id} actualizado con éxito para usuario {user_id}.")
        except Exception as commit_error:
            print(f"!!!!!!!!!!!!!!! ERROR AL HACER COMMIT (Update): {commit_error}")
            logger.exception(f"Error detallado al hacer commit para update plan {meal_plan_id}:")
            # Rollback se hará en finally
            raise

        # --- 4. Devolver datos actualizados del plan (solo el plan base) ---
        print(f"[DEBUG] MealPlansService (Update): Plan ID {meal_plan_id}: Preparando datos de respuesta.")
        if updated_plan_data is None:
            # Si solo se actualizaron items (o no se actualizó nada), obtener datos actuales del plan base
            print(f"[DEBUG] MealPlansService (Update): Plan base no actualizado, obteniendo datos actuales...")
            current_plan_base = get_meal_plan(meal_plan_id, user_id, with_items=False) # Usa la función get ya existente
            if current_plan_base is None:
                 print(f"!!!!!!!!!!!!!!! ERROR CRÍTICO: No se pudo recuperar el plan {meal_plan_id} después de actualizar items.")
                 # Esto indica un problema grave si llegamos aquí
                 raise ValueError(f"No se pudo recuperar el plan {meal_plan_id} después de actualizar items.")
            updated_plan_data = current_plan_base # Usar los datos actuales formateados
            print(f"[DEBUG] MealPlansService (Update): Datos actuales del plan obtenidos: {updated_plan_data}")

        # Devolvemos el plan base (actualizado o no) formateado
        print(f"[DEBUG] MealPlansService (Update): Devolviendo datos del plan base: {updated_plan_data}")
        return updated_plan_data

    except psycopg2.Error as db_error:
        print(f"!!!!!!!!!!!!!!! ERROR DE BASE DE DATOS (psycopg2.Error) (Update): {db_error}")
        if conn: conn.rollback(); print("[DEBUG] Rollback (Update) por psycopg2.Error.")
        logger.error(f"Error de base de datos al actualizar plan {meal_plan_id}: {db_error}")
        return None # Opcional: devolver None
    except ValueError as val_error: # Capturar ValueError específicos
        print(f"!!!!!!!!!!!!!!! ERROR DE VALIDACIÓN O LÓGICA (ValueError) (Update): {val_error}")
        if conn: conn.rollback(); print("[DEBUG] Rollback (Update) por ValueError.")
        logger.error(f"Error de valor al actualizar plan {meal_plan_id}: {val_error}")
        return None # Opcional: devolver None
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR INESPERADO (Exception) (Update): {e}")
        if conn: conn.rollback(); print("[DEBUG] Rollback (Update) por Exception.")
        logger.exception(f"Error inesperado al actualizar plan {meal_plan_id}: {e}")
        raise # Dejar que la ruta devuelva 500
    finally:
        print("[DEBUG] MealPlansService (Update): Bloque finally - cerrando cursor y conexión.")
        if cur: cur.close()
        if conn: conn.close()
        print(">>>>>>>>>>>>>>> [DEBUG] Saliendo de SERVICIO MealPlansService.update_meal_plan")


def delete_meal_plan(meal_plan_id: int, user_id: str) -> bool:
    """Elimina un plan de comida y sus items asociados en una transacción."""
    print(f">>> [DEBUG] delete_meal_plan ID: {meal_plan_id} para user_id: {user_id}")
    conn = None
    cur = None
    deleted = False
    try:
        from back_end.gym.config import DB_CONFIG
        import psycopg2

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, gym, public")
        print(f"[DEBUG] delete_meal_plan: Conectado y search_path establecido.")

        # Verificar pertenencia
        print(f"[DEBUG] delete_meal_plan: Verificando si plan {meal_plan_id} pertenece a user {user_id}.")
        cur.execute("SELECT id FROM nutrition.meal_plans WHERE id = %s AND user_id = %s", (meal_plan_id, str(user_id)))
        if cur.fetchone() is None:
            logger.warning(f"Intento de eliminar plan {meal_plan_id} fallido: No encontrado o no pertenece al usuario {user_id}.")
            print(f"[WARN] delete_meal_plan: Plan {meal_plan_id} no encontrado o no pertenece a user {user_id}.")
            # conn.rollback() # No es necesario si no se hizo nada aún
            return False # Devolver False directamente

        print(f"[DEBUG] delete_meal_plan: Plan {meal_plan_id} pertenece a user {user_id}. Procediendo a eliminar.")

        # Eliminar items (CASCADE debería funcionar, pero explícito es más seguro)
        print(f"[DEBUG] delete_meal_plan: Eliminando items asociados al plan {meal_plan_id}...")
        cur.execute("DELETE FROM nutrition.meal_plan_items WHERE meal_plan_id = %s", (meal_plan_id,))
        deleted_items_count = cur.rowcount
        print(f"[DEBUG] delete_meal_plan: {deleted_items_count} items eliminados.")
        logger.info(f"Eliminados {deleted_items_count} items para plan {meal_plan_id}")

        # Eliminar plan
        print(f"[DEBUG] delete_meal_plan: Eliminando registro principal del plan {meal_plan_id}...")
        cur.execute("DELETE FROM nutrition.meal_plans WHERE id = %s", (meal_plan_id,))
        deleted_plan_count = cur.rowcount
        print(f"[DEBUG] delete_meal_plan: {deleted_plan_count} plan(es) eliminados.")

        print(f"[DEBUG] delete_meal_plan: Intentando commit...")
        conn.commit()
        deleted = deleted_plan_count > 0
        if deleted:
            print(f"[DEBUG] delete_meal_plan: Commit exitoso. Plan {meal_plan_id} eliminado.")
            logger.info(f"Plan ID {meal_plan_id} eliminado con éxito.")
        else:
            # Esto no debería ocurrir si la verificación inicial funcionó y el delete fue exitoso
            print(f"!!!!!!!!!!!!!!! ERROR LÓGICO en delete_meal_plan: Plan {meal_plan_id} verificado pero delete count fue 0.")
            logger.error(f"Error al eliminar plan {meal_plan_id} después de la verificación.")

        return deleted

    except psycopg2.Error as db_error:
        print(f"!!!!!!!!!!!!!!! ERROR DE BASE DE DATOS (psycopg2.Error) (Delete): {db_error}")
        if conn: conn.rollback(); print("[DEBUG] Rollback (Delete) por psycopg2.Error.")
        logger.error(f"Error de base de datos al eliminar plan {meal_plan_id}: {db_error}")
        raise ValueError(f"Error de base de datos: {db_error}") # Relanzar como error genérico o específico
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR INESPERADO (Exception) (Delete): {e}")
        if conn: conn.rollback(); print("[DEBUG] Rollback (Delete) por Exception.")
        logger.exception(f"Error inesperado al eliminar plan {meal_plan_id}: {e}")
        raise
    finally:
        print("[DEBUG] delete_meal_plan: Bloque finally - cerrando cursor y conexión.")
        if cur: cur.close()
        if conn: conn.close()
        print(f">>> [DEBUG] Saliendo de delete_meal_plan para ID: {meal_plan_id}")