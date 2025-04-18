# back_end/gym/services/nutrition/meal_plan_items_service.py
import logging
from typing import Optional, List, Dict
import datetime # Importar datetime para manejar fechas/horas
import decimal # Importar decimal para manejar números

# Corregir esta importación para usar una ruta absoluta
from back_end.gym.services.db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)

def add_meal_to_plan(meal_plan_item_data: Dict) -> Optional[Dict]:
    """Añade una comida a un plan de comida."""
    try:
        # Verificar que la comida existe (añadir schema nutrition)
        check_meal_query = "SELECT meal_name FROM nutrition.meals WHERE id = %s"
        meal_result = execute_db_query(check_meal_query, (meal_plan_item_data['meal_id'],), fetch_one=True)

        if not meal_result:
            raise ValueError(f"Comida con ID {meal_plan_item_data['meal_id']} no encontrada")

        # Insertar el elemento del plan - CORREGIDO: meal_type, añadir columnas tabla
        query = """
        INSERT INTO nutrition.meal_plan_items (meal_plan_id, meal_id, day_of_week, meal_type, quantity, notes, plan_date, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, meal_plan_id, meal_id, day_of_week, meal_type, quantity, notes, created_at, updated_at, plan_date, unit
        """

        # CORREGIDO: Convertir meal_type a str
        meal_type_value = meal_plan_item_data.get('meal_type')
        params = (
            meal_plan_item_data['meal_plan_id'],
            meal_plan_item_data['meal_id'],
            meal_plan_item_data.get('day_of_week'), # Permitir nulo
            str(meal_type_value) if meal_type_value else None, # Convertir Enum/valor a string
            meal_plan_item_data.get('quantity', 100.0),
            meal_plan_item_data.get('notes'),
            meal_plan_item_data.get('plan_date'), # Valor de plan_date
            meal_plan_item_data.get('unit', 'g')   # Valor de unit
        )

        result = execute_db_query(query, params, fetch_one=True, commit=True) # Asegurar commit

        if not result:
            return None

        # CORREGIDO: usar meal_type en el diccionario devuelto (índice 4)
        return {
            "id": result[0],
            "meal_plan_id": result[1],
            "meal_id": result[2],
            "day_of_week": result[3],
            "meal_type": result[4], # CORREGIDO
            "quantity": float(result[5]) if isinstance(result[5], decimal.Decimal) else result[5],
            "notes": result[6],
            "meal_name": meal_result[0], # Nombre obtenido de la verificación
            "created_at": result[7].isoformat() if isinstance(result[7], datetime.datetime) else result[7],
            "updated_at": result[8].isoformat() if isinstance(result[8], datetime.datetime) else result[8],
            "plan_date": result[9].isoformat() if isinstance(result[9], datetime.date) else result[9],
            "unit": result[10]
        }
    except Exception as e:
        logger.error(f"Error al añadir comida a plan: {e}")
        raise

def get_meal_plan_items(meal_plan_id: int) -> List[Dict]:
    """Obtiene todos los elementos/comidas de un plan de comida."""
    try:
        # CORREGIDO: seleccionar meal_type, usar meal_type en ORDER BY
        # Seleccionar columnas según init-db.sql: plan_date, day_of_week, meal_type, quantity, unit, notes
        query = """
        SELECT mpi.id, mpi.meal_plan_id, mpi.meal_id, m.meal_name,
               mpi.plan_date, mpi.day_of_week, mpi.meal_type, -- Columnas correctas
               mpi.quantity, mpi.unit, mpi.notes, -- Columnas correctas
               mpi.created_at, mpi.updated_at,
               m.calories, m.proteins, m.carbohydrates, m.fats
        FROM nutrition.meal_plan_items mpi
        JOIN nutrition.meals m ON mpi.meal_id = m.id
        WHERE mpi.meal_plan_id = %s
        ORDER BY COALESCE(mpi.plan_date, mpi.created_at::date), -- Ordenar por fecha
                 mpi.day_of_week, -- Luego día semana
            CASE mpi.meal_type -- CORREGIDO
                WHEN 'breakfast' THEN 1
                WHEN 'lunch' THEN 2
                WHEN 'dinner' THEN 3
                WHEN 'snack' THEN 4
                ELSE 5
            END,
            mpi.created_at -- Desempate final
        """

        results = execute_db_query(query, (meal_plan_id,), fetch_all=True)

        items = []
        # Ajustar índices según nuevo SELECT
        for row in results:
            items.append({
                "id": row[0],
                "meal_plan_id": row[1],
                "meal_id": row[2],
                "meal_name": row[3],
                "plan_date": row[4].isoformat() if isinstance(row[4], datetime.date) else row[4],       # Índice 4
                "day_of_week": row[5],                                                                   # Índice 5
                "meal_type": row[6],    # CORREGIDO                                                      # Índice 6
                "quantity": float(row[7]) if isinstance(row[7], decimal.Decimal) else row[7],          # Índice 7
                "unit": row[8],                                                                          # Índice 8
                "notes": row[9],                                                                         # Índice 9
                "created_at": row[10].isoformat() if isinstance(row[10], datetime.datetime) else row[10],# Índice 10
                "updated_at": row[11].isoformat() if isinstance(row[11], datetime.datetime) else row[11],# Índice 11
                "meal_info": {
                    "calories": float(row[12]) if isinstance(row[12], decimal.Decimal) else row[12],    # Índice 12
                    "proteins": float(row[13]) if isinstance(row[13], decimal.Decimal) else row[13],    # Índice 13
                    "carbohydrates": float(row[14]) if isinstance(row[14], decimal.Decimal) else row[14],# Índice 14
                    "fats": float(row[15]) if isinstance(row[15], decimal.Decimal) else row[15]         # Índice 15
                } if row[12] is not None else None
            })

        return items
    except Exception as e:
        logger.error(f"Error al obtener elementos de plan de comida {meal_plan_id}: {e}")
        raise

def get_meal_plan_item(item_id: int) -> Optional[Dict]:
    """Obtiene un elemento/comida específico de un plan de comida."""
    try:
        # CORREGIDO: seleccionar meal_type y otras columnas correctas
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

        result = execute_db_query(query, (item_id,), fetch_one=True)

        if not result:
            return None

        # CORREGIDO: usar meal_type y ajustar índices
        return {
            "id": result[0],
            "meal_plan_id": result[1],
            "meal_id": result[2],
            "meal_name": result[3],
            "plan_date": result[4].isoformat() if isinstance(result[4], datetime.date) else result[4],       # Índice 4
            "day_of_week": result[5],                                                                   # Índice 5
            "meal_type": result[6],    # CORREGIDO                                                      # Índice 6
            "quantity": float(result[7]) if isinstance(result[7], decimal.Decimal) else result[7],          # Índice 7
            "unit": result[8],                                                                          # Índice 8
            "notes": result[9],                                                                         # Índice 9
            "created_at": result[10].isoformat() if isinstance(result[10], datetime.datetime) else result[10],# Índice 10
            "updated_at": result[11].isoformat() if isinstance(result[11], datetime.datetime) else result[11],# Índice 11
            "meal_info": {
                 "calories": float(result[12]) if isinstance(result[12], decimal.Decimal) else result[12],    # Índice 12
                 "proteins": float(result[13]) if isinstance(result[13], decimal.Decimal) else result[13],    # Índice 13
                 "carbohydrates": float(result[14]) if isinstance(result[14], decimal.Decimal) else result[14],# Índice 14
                 "fats": float(result[15]) if isinstance(result[15], decimal.Decimal) else result[15]         # Índice 15
            } if result[12] is not None else None
        }
    except Exception as e:
        logger.error(f"Error al obtener elemento de plan de comida {item_id}: {e}")
        raise

def update_meal_plan_item(item_id: int, update_data: Dict) -> Optional[Dict]:
    """Actualiza un elemento/comida en un plan de comida."""
    try:
        # Verificar si el elemento existe
        current_item = get_meal_plan_item(item_id)
        if not current_item:
            # Podríamos lanzar un error 404 desde la ruta si esto devuelve None
            logger.warning(f"Elemento de plan de comida con ID {item_id} no encontrado para actualizar.")
            return None

        # Verificar que la comida existe si se cambió
        if 'meal_id' in update_data and update_data['meal_id'] != current_item['meal_id']:
            check_meal_query = "SELECT meal_name FROM nutrition.meals WHERE id = %s"
            meal_result = execute_db_query(check_meal_query, (update_data['meal_id'],), fetch_one=True)
            if not meal_result:
                raise ValueError(f"Comida con ID {update_data['meal_id']} no encontrada")

        # Construir consulta dinámica con los campos proporcionados
        update_fields = []
        params = []
        # Usar los nombres correctos de columnas de init-db.sql
        allowed_keys = ['meal_plan_id', 'meal_id', 'plan_date', 'day_of_week', 'meal_type', 'quantity', 'unit', 'notes']

        for key in allowed_keys:
            if key in update_data: # Comprobar si la clave está en los datos a actualizar
                 update_fields.append(f"{key} = %s")
                 # CORREGIDO: Convertir meal_type a str
                 if key == 'meal_type':
                     meal_type_value = update_data.get(key)
                     params.append(str(meal_type_value) if meal_type_value else None)
                 else:
                     params.append(update_data[key])

        # Si no hay campos para actualizar
        if not update_fields:
            logger.info(f"No se proporcionaron campos válidos para actualizar el item {item_id}.")
            return current_item # Devolver el item actual sin cambios

        # Añadir campo updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        # Construir consulta SQL UPDATE
        update_query = f"""
        UPDATE nutrition.meal_plan_items
        SET {", ".join(update_fields)}
        WHERE id = %s
        RETURNING id
        """
        # Añadir id al final de los parámetros
        params.append(item_id)

        # Ejecutar la actualización
        result = execute_db_query(update_query, tuple(params), fetch_one=True, commit=True) # Asegurar commit

        if not result:
            logger.error(f"Falló la actualización en BD para el item {item_id}, se hizo rollback.")
            # execute_db_query debería haber hecho rollback si fetch_one falló después de SET
            return None # Indicar que la actualización falló

        logger.info(f"Item {item_id} actualizado con éxito.")
        # Devolver el elemento actualizado llamando a get_meal_plan_item
        return get_meal_plan_item(item_id)
    except Exception as e:
        # execute_db_query debería manejar rollback en excepción
        logger.error(f"Error al actualizar elemento de plan de comida {item_id}: {e}")
        raise # Relanzar para que la ruta devuelva 500

def delete_meal_plan_item(item_id: int) -> bool:
    """Elimina un elemento/comida de un plan de comida."""
    try:
        # Verificar si existe antes de borrar? Opcional.
        delete_query = "DELETE FROM nutrition.meal_plan_items WHERE id = %s RETURNING id"
        result = execute_db_query(delete_query, (item_id,), fetch_one=True, commit=True) # Usar fetch_one con RETURNING

        deleted = bool(result) # True si se devolvió un ID, False si no
        if deleted:
             logger.info(f"Item {item_id} eliminado con éxito.")
        else:
             logger.warning(f"Intento de eliminar item {item_id} fallido (no encontrado).")
        return deleted
    except Exception as e:
        logger.error(f"Error al eliminar elemento de plan de comida {item_id}: {e}")
        raise