# back_end/gym/services/nutrition/meal_plan_items_service.py
import logging
from typing import Optional, List, Dict, Any
import datetime # Importar datetime para manejar fechas/horas
import decimal # Importar decimal para manejar números

# Corregir esta importación para usar una ruta absoluta
from back_end.gym.services.db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)

# Helper para formatear resultados de item
def format_item_result(row: tuple) -> Dict[str, Any]:
    """Formatea una fila de resultado de la BD a un diccionario de item."""
    item = {
        "id": row[0],
        "meal_plan_id": row[1],
        "meal_id": row[2],
        "meal_name": row[3], # Nombre ya viene del JOIN
        "plan_date": row[4].isoformat() if isinstance(row[4], datetime.date) else row[4],  # Índice 4
        "day_of_week": row[5],                                                              # Índice 5
        "meal_type": row[6],                                                                # Índice 6
        "quantity": float(row[7]) if isinstance(row[7], decimal.Decimal) else row[7],      # Índice 7
        "unit": row[8],                                                                     # Índice 8
        "notes": row[9],                                                                    # Índice 9
        "created_at": row[10].isoformat() if isinstance(row[10], datetime.datetime) else row[10], # Índice 10
        "updated_at": row[11].isoformat() if isinstance(row[11], datetime.datetime) else row[11], # Índice 11
        "meal_info": { # Si se incluyó info de la comida
             "calories": float(row[12]) if isinstance(row[12], decimal.Decimal) else row[12],    # Índice 12
             "proteins": float(row[13]) if isinstance(row[13], decimal.Decimal) else row[13],    # Índice 13
             "carbohydrates": float(row[14]) if isinstance(row[14], decimal.Decimal) else row[14],# Índice 14
             "fats": float(row[15]) if isinstance(row[15], decimal.Decimal) else row[15]         # Índice 15
        } if len(row) > 12 and row[12] is not None else None # Verificar longitud y no nulidad
    }
    return item

# NOTA: La función `create_meal_plan` del otro servicio ahora maneja la creación de items
# en una transacción. `add_meal_to_plan` podría ser redundante o usarse para añadir
# items a un plan *existente* fuera de la creación inicial.
# Si se usa, necesita su propia gestión de conexión/transacción o reutilizar `execute_db_query`.

def add_meal_to_plan(meal_plan_item_data: Dict) -> Optional[Dict]:
    """Añade UNA SOLA comida a un plan de comida EXISTENTE."""
    print(f">>> [DEBUG] add_meal_to_plan: Intentando añadir item: {meal_plan_item_data}")
    logger.info(f"[SERVICE add_meal_to_plan] Datos recibidos: {meal_plan_item_data}")

    # Validaciones básicas de entrada
    meal_plan_id = meal_plan_item_data.get('meal_plan_id')
    meal_id = meal_plan_item_data.get('meal_id')
    if not meal_plan_id or not meal_id:
         print(f"!!!!!!!!!!!!!!! ERROR en add_meal_to_plan: Falta meal_plan_id o meal_id.")
         logger.error(f"add_meal_to_plan: Falta meal_plan_id ({meal_plan_id}) o meal_id ({meal_id}).")
         raise ValueError("Falta meal_plan_id o meal_id")

    try:
        # Verificar que la comida existe
        print(f"[DEBUG] add_meal_to_plan: Verificando existencia de meal_id: {meal_id}")
        check_meal_query = "SELECT meal_name FROM nutrition.meals WHERE id = %s"
        meal_result = execute_db_query(check_meal_query, (meal_id,), fetch_one=True)
        print(f"[DEBUG] add_meal_to_plan: Resultado verificación meal_id: {meal_result}")

        if not meal_result:
            print(f"!!!!!!!!!!!!!!! ERROR en add_meal_to_plan: Comida con ID {meal_id} no encontrada.")
            raise ValueError(f"Comida con ID {meal_id} no encontrada")

        meal_name = meal_result[0] # Guardar nombre para la respuesta

        # Verificar que el plan existe y pertenece al usuario (IMPORTANTE si viene de ruta separada)
        # Esta verificación debería hacerse en la RUTA antes de llamar al servicio,
        # pasando el user_id validado. Asumimos que la ruta ya lo hizo.
        # print(f"[DEBUG] add_meal_to_plan: Verificando existencia de meal_plan_id: {meal_plan_id}")
        # check_plan_query = "SELECT id FROM nutrition.meal_plans WHERE id = %s" # AND user_id = %s <- Necesitaríamos user_id
        # plan_exists = execute_db_query(check_plan_query, (meal_plan_id,), fetch_one=True)
        # if not plan_exists:
        #     print(f"!!!!!!!!!!!!!!! ERROR en add_meal_to_plan: Plan con ID {meal_plan_id} no encontrado.")
        #     raise ValueError(f"Plan de comida con ID {meal_plan_id} no encontrado")
        # print(f"[DEBUG] add_meal_to_plan: Plan {meal_plan_id} existe.")


        # Insertar el elemento del plan
        query = """
        INSERT INTO nutrition.meal_plan_items (meal_plan_id, meal_id, day_of_week, meal_type, quantity, notes, plan_date, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, meal_plan_id, meal_id, day_of_week, meal_type, quantity, notes, created_at, updated_at, plan_date, unit
        """

        meal_type_value = meal_plan_item_data.get('meal_type')
        quantity_value = meal_plan_item_data.get('quantity', 100.0) # Default si no se provee
        unit_value = meal_plan_item_data.get('unit', 'g') # Default si no se provee

        # Validación adicional simple
        if quantity_value is None or quantity_value <= 0:
             print(f"!!!!!!!!!!!!!!! ERROR en add_meal_to_plan: Quantity inválida ({quantity_value}) para meal_id {meal_id}.")
             raise ValueError(f"Quantity inválida ({quantity_value})")


        params = (
            meal_plan_id,
            meal_id,
            meal_plan_item_data.get('day_of_week'), # Permitir nulo
            str(meal_type_value) if meal_type_value else None, # Convertir Enum/valor a string
            quantity_value,
            meal_plan_item_data.get('notes'),
            meal_plan_item_data.get('plan_date'), # Permitir nulo si day_of_week se usa? O requerir uno?
            unit_value
        )

        print(f"[DEBUG] add_meal_to_plan: Intentando ejecutar INSERT item. Params: {params}")
        # execute_db_query maneja la conexión, cursor, ejecución, commit y cierre
        result = execute_db_query(query, params, fetch_one=True, commit=True)
        print(f"[DEBUG] add_meal_to_plan: INSERT item ejecutado. Resultado: {result}")

        if not result:
            # Esto indicaría un error en execute_db_query o un problema inesperado
            print(f"!!!!!!!!!!!!!!! ERROR en add_meal_to_plan: execute_db_query no devolvió resultado para INSERT.")
            logger.error(f"add_meal_to_plan: Fallo al insertar item para plan {meal_plan_id}, meal {meal_id}. execute_db_query devolvió None.")
            return None

        # Formatear usando solo los índices del RETURNING de este INSERT
        # (No tenemos info de la comida aquí, solo el nombre)
        created_item = {
             "id": result[0],
             "meal_plan_id": result[1],
             "meal_id": result[2],
             "day_of_week": result[3],
             "meal_type": result[4],
             "quantity": float(result[5]) if isinstance(result[5], decimal.Decimal) else result[5],
             "notes": result[6],
             "meal_name": meal_name, # Nombre obtenido antes
             "created_at": result[7].isoformat() if isinstance(result[7], datetime.datetime) else result[7],
             "updated_at": result[8].isoformat() if isinstance(result[8], datetime.datetime) else result[8],
             "plan_date": result[9].isoformat() if isinstance(result[9], datetime.date) else result[9],
             "unit": result[10]
         }
        print(f"[DEBUG] add_meal_to_plan: Item creado y formateado: {created_item}")
        logger.info(f"Item {created_item['id']} añadido a plan {meal_plan_id}.")
        return created_item

    except ValueError as ve: # Capturar errores de validación propios
        print(f"!!!!!!!!!!!!!!! ERROR DE VALOR en add_meal_to_plan: {ve}")
        logger.error(f"Error de validación al añadir comida a plan: {ve}")
        raise # Relanzar para que la ruta maneje el error (ej. 400 Bad Request)
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR INESPERADO en add_meal_to_plan: {e}")
        logger.exception(f"Error inesperado al añadir comida a plan {meal_plan_item_data.get('meal_plan_id')}: {e}")
        # execute_db_query debería haber manejado rollback si falló durante la query
        raise # Relanzar para que la ruta devuelva 500

def get_meal_plan_items(meal_plan_id: int) -> List[Dict]:
    """Obtiene todos los elementos/comidas de un plan de comida."""
    print(f">>> [DEBUG] get_meal_plan_items para plan_id: {meal_plan_id}")
    try:
        # Seleccionar columnas según init-db.sql y añadir macros de la comida
        query = """
        SELECT mpi.id, mpi.meal_plan_id, mpi.meal_id, m.meal_name,
               mpi.plan_date, mpi.day_of_week, mpi.meal_type, -- Columnas correctas
               mpi.quantity, mpi.unit, mpi.notes, -- Columnas correctas
               mpi.created_at, mpi.updated_at,
               m.calories, m.proteins, m.carbohydrates, m.fats -- Macros de la comida
        FROM nutrition.meal_plan_items mpi
        JOIN nutrition.meals m ON mpi.meal_id = m.id
        WHERE mpi.meal_plan_id = %s
        ORDER BY COALESCE(mpi.plan_date, mpi.created_at::date), -- Ordenar por fecha
                 mpi.day_of_week, -- Luego día semana
             CASE mpi.meal_type -- Orden específico para tipos de comida
                 WHEN 'Desayuno' THEN 1 -- Asegúrate que estos strings coincidan con los de tu Enum/BD
                 WHEN 'Almuerzo' THEN 2
                 WHEN 'Comida' THEN 3
                 WHEN 'Merienda' THEN 4
                 WHEN 'Cena' THEN 5
                 WHEN 'Otro' THEN 6
                 ELSE 7
             END,
             mpi.created_at -- Desempate final
        """
        print(f"[DEBUG] get_meal_plan_items: Query: {query[:200]}..., Params: {(meal_plan_id,)}")
        results = execute_db_query(query, (meal_plan_id,), fetch_all=True)
        print(f"[DEBUG] get_meal_plan_items: Obtenidos {len(results)} resultados de BD.")

        # Usar el helper para formatear
        items = [format_item_result(row) for row in results]

        print(f"[DEBUG] get_meal_plan_items: Devolviendo {len(items)} items formateados.")
        return items
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR en get_meal_plan_items para plan {meal_plan_id}: {e}")
        logger.exception(f"Error al obtener elementos de plan de comida {meal_plan_id}: {e}")
        raise # O devolver lista vacía? Depende de cómo quiera manejarlo la ruta

def get_meal_plan_item(item_id: int) -> Optional[Dict]:
    """Obtiene un elemento/comida específico de un plan de comida."""
    print(f">>> [DEBUG] get_meal_plan_item para item_id: {item_id}")
    try:
        query = """
        SELECT mpi.id, mpi.meal_plan_id, mpi.meal_id, m.meal_name,
               mpi.plan_date, mpi.day_of_week, mpi.meal_type, -- Columnas correctas
               mpi.quantity, mpi.unit, mpi.notes, -- Columnas correctas
               mpi.created_at, mpi.updated_at,
               m.calories, m.proteins, m.carbohydrates, m.fats
        FROM nutrition.meal_plan_items mpi
        JOIN nutrition.meals m ON mpi.meal_id = m.id
        WHERE mpi.id = %s
        """
        print(f"[DEBUG] get_meal_plan_item: Query: {query[:200]}..., Params: {(item_id,)}")
        result = execute_db_query(query, (item_id,), fetch_one=True)
        print(f"[DEBUG] get_meal_plan_item: Resultado BD: {result}")

        if not result:
            print(f"[DEBUG] get_meal_plan_item: Item {item_id} no encontrado.")
            return None

        # Usar el helper para formatear
        item = format_item_result(result)
        print(f"[DEBUG] get_meal_plan_item: Devolviendo item formateado: {item}")
        return item
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR en get_meal_plan_item para item {item_id}: {e}")
        logger.exception(f"Error al obtener elemento de plan de comida {item_id}: {e}")
        raise # O devolver None

def update_meal_plan_item(item_id: int, update_data: Dict) -> Optional[Dict]:
    """Actualiza un elemento/comida en un plan de comida."""
    print(f">>> [DEBUG] update_meal_plan_item para item_id: {item_id}. Datos: {update_data}")
    logger.info(f"[SERVICE update_meal_plan_item] Datos recibidos para item {item_id}: {update_data}")

    try:
        # Verificar si el elemento existe PRIMERO
        print(f"[DEBUG] update_meal_plan_item: Verificando si item {item_id} existe...")
        current_item = get_meal_plan_item(item_id) # Reutiliza la función get
        if not current_item:
            # Esto debería ser manejado por la ruta como 404 Not Found
            print(f"[WARN] update_meal_plan_item: Item {item_id} no encontrado para actualizar.")
            logger.warning(f"Elemento de plan de comida con ID {item_id} no encontrado para actualizar.")
            return None

        print(f"[DEBUG] update_meal_plan_item: Item {item_id} encontrado. Datos actuales: {current_item}")

        # Verificar que la comida existe si se cambió meal_id
        new_meal_id = update_data.get('meal_id')
        if new_meal_id is not None and new_meal_id != current_item['meal_id']:
            print(f"[DEBUG] update_meal_plan_item: Se cambió meal_id a {new_meal_id}. Verificando existencia...")
            check_meal_query = "SELECT meal_name FROM nutrition.meals WHERE id = %s"
            meal_result = execute_db_query(check_meal_query, (new_meal_id,), fetch_one=True)
            print(f"[DEBUG] update_meal_plan_item: Resultado verificación nuevo meal_id: {meal_result}")
            if not meal_result:
                print(f"!!!!!!!!!!!!!!! ERROR en update_meal_plan_item: Nueva comida con ID {new_meal_id} no encontrada.")
                raise ValueError(f"Comida con ID {new_meal_id} no encontrada")
        else:
             print(f"[DEBUG] update_meal_plan_item: No se cambió meal_id o no se proporcionó.")


        # Construir consulta dinámica con los campos proporcionados
        update_fields = []
        params = []
        # Usar los nombres correctos de columnas de init-db.sql que se pueden modificar
        allowed_keys = ['meal_id', 'plan_date', 'day_of_week', 'meal_type', 'quantity', 'unit', 'notes']
        # 'meal_plan_id' NO debería cambiarse aquí

        for key in allowed_keys:
            if key in update_data: # Comprobar si la clave está en los datos a actualizar
                value = update_data[key]
                print(f"[DEBUG] update_meal_plan_item: Campo '{key}' encontrado en update_data con valor: {value}")
                update_fields.append(f"{key} = %s")
                # Convertir meal_type a str si es necesario
                if key == 'meal_type':
                    params.append(str(value) if value else None)
                else:
                    params.append(value)

        # Si no hay campos válidos para actualizar
        if not update_fields:
            print(f"[INFO] update_meal_plan_item: No se proporcionaron campos válidos para actualizar el item {item_id}.")
            logger.info(f"No se proporcionaron campos válidos para actualizar el item {item_id}.")
            return current_item # Devolver el item actual sin cambios

        # Añadir campo updated_at automáticamente
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        print(f"[DEBUG] update_meal_plan_item: Campos para SET: {update_fields}")

        # Construir consulta SQL UPDATE completa
        update_query = f"""
        UPDATE nutrition.meal_plan_items
        SET {", ".join(update_fields)}
        WHERE id = %s
        RETURNING id # Solo necesitamos saber si se actualizó
        """
        # Añadir id al final de los parámetros para el WHERE
        params.append(item_id)
        print(f"[DEBUG] update_meal_plan_item: Query: {update_query[:200]}..., Params: {tuple(params)}")

        # Ejecutar la actualización
        result = execute_db_query(update_query, tuple(params), fetch_one=True, commit=True)
        print(f"[DEBUG] update_meal_plan_item: UPDATE ejecutado. Resultado: {result}")


        if not result:
            # Esto podría pasar si el ID es incorrecto, aunque ya lo validamos antes... raro.
            print(f"!!!!!!!!!!!!!!! ERROR en update_meal_plan_item: Falló la actualización en BD para el item {item_id} (no se retornó ID).")
            logger.error(f"Falló la actualización en BD para el item {item_id}, posible rollback en execute_db_query.")
            # execute_db_query debería haber hecho rollback si fetch_one falló después de SET
            return None # Indicar que la actualización falló

        print(f"[DEBUG] update_meal_plan_item: Item {item_id} actualizado en BD.")
        logger.info(f"Item {item_id} actualizado con éxito.")

        # Devolver el elemento actualizado llamando a get_meal_plan_item CON LOS NUEVOS DATOS
        print(f"[DEBUG] update_meal_plan_item: Obteniendo item actualizado de la BD...")
        updated_item = get_meal_plan_item(item_id)
        print(f"[DEBUG] update_meal_plan_item: Devolviendo item actualizado: {updated_item}")
        return updated_item

    except ValueError as ve: # Capturar errores de validación propios
        print(f"!!!!!!!!!!!!!!! ERROR DE VALOR en update_meal_plan_item: {ve}")
        logger.error(f"Error de validación al actualizar item {item_id}: {ve}")
        # execute_db_query debería haber manejado rollback si falló durante la query
        raise # Relanzar para que la ruta maneje el error (ej. 400 o 404)
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR INESPERADO en update_meal_plan_item para item {item_id}: {e}")
        # execute_db_query debería manejar rollback en excepción
        logger.exception(f"Error inesperado al actualizar elemento de plan de comida {item_id}: {e}")
        raise # Relanzar para que la ruta devuelva 500

def delete_meal_plan_item(item_id: int) -> bool:
    """Elimina un elemento/comida de un plan de comida."""
    print(f">>> [DEBUG] delete_meal_plan_item para item_id: {item_id}")
    try:
        # Verificar si existe antes de borrar? Opcional, DELETE es idempotente.
        # Si queremos asegurar que existía, podríamos hacer un SELECT primero.
        delete_query = "DELETE FROM nutrition.meal_plan_items WHERE id = %s RETURNING id"
        print(f"[DEBUG] delete_meal_plan_item: Query: {delete_query}, Params: {(item_id,)}")

        # Usar fetch_one con RETURNING para saber si se borró algo
        result = execute_db_query(delete_query, (item_id,), fetch_one=True, commit=True)
        print(f"[DEBUG] delete_meal_plan_item: DELETE ejecutado. Resultado: {result}")


        deleted = bool(result) # True si se devolvió un ID (se borró una fila), False si no
        if deleted:
              print(f"[DEBUG] delete_meal_plan_item: Item {item_id} eliminado con éxito.")
              logger.info(f"Item {item_id} eliminado con éxito.")
        else:
              print(f"[WARN] delete_meal_plan_item: Intento de eliminar item {item_id} fallido (no encontrado).")
              logger.warning(f"Intento de eliminar item {item_id} fallido (no encontrado).")
        return deleted
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERROR en delete_meal_plan_item para item {item_id}: {e}")
        logger.exception(f"Error al eliminar elemento de plan de comida {item_id}: {e}")
        # execute_db_query debería haber manejado rollback si falló durante la query
        raise # Relanzar para que la ruta devuelva 500