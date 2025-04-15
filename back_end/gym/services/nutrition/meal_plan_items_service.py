# back_end/gym/services/nutrition/meal_plan_items_service.py
import logging
from typing import Optional, List, Dict

# Corregir esta importación para usar una ruta absoluta
from back_end.gym.services.db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)

def add_meal_to_plan(meal_plan_item_data: Dict) -> Optional[Dict]:
    """Añade una comida a un plan de comida."""
    try:
        # Verificar que la comida existe
        check_meal_query = "SELECT meal_name FROM meals WHERE id = %s"
        meal_result = execute_db_query(check_meal_query, (meal_plan_item_data['meal_id'],), fetch_one=True)
        
        if not meal_result:
            raise ValueError(f"Comida con ID {meal_plan_item_data['meal_id']} no encontrada")
        
        # Insertar el elemento del plan
        query = """
        INSERT INTO meal_plan_items (meal_plan_id, meal_id, day_of_week, meal_time, quantity, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, meal_plan_id, meal_id, day_of_week, meal_time, quantity, notes, created_at, updated_at
        """
        
        params = (
            meal_plan_item_data['meal_plan_id'],
            meal_plan_item_data['meal_id'],
            meal_plan_item_data['day_of_week'],
            meal_plan_item_data['meal_time'],
            meal_plan_item_data.get('quantity', 1.0),
            meal_plan_item_data.get('notes')
        )
        
        result = execute_db_query(query, params, fetch_one=True)
        
        if not result:
            return None
        
        return {
            "id": result[0],
            "meal_plan_id": result[1],
            "meal_id": result[2],
            "day_of_week": result[3],
            "meal_time": result[4],
            "quantity": result[5],
            "notes": result[6],
            "meal_name": meal_result[0],
            "created_at": result[7],
            "updated_at": result[8]
        }
    except Exception as e:
        logger.error(f"Error al añadir comida a plan: {e}")
        raise

def get_meal_plan_items(meal_plan_id: int) -> List[Dict]:
    """Obtiene todos los elementos/comidas de un plan de comida."""
    try:
        query = """
        SELECT mpi.id, mpi.meal_plan_id, mpi.meal_id, m.meal_name, mpi.day_of_week, mpi.meal_time, 
               mpi.quantity, mpi.notes, mpi.created_at, mpi.updated_at,
               m.calories, m.proteins, m.carbohydrates, m.fats
        FROM meal_plan_items mpi
        JOIN meals m ON mpi.meal_id = m.id
        WHERE mpi.meal_plan_id = %s
        ORDER BY mpi.day_of_week, 
            CASE mpi.meal_time 
                WHEN 'breakfast' THEN 1 
                WHEN 'lunch' THEN 2 
                WHEN 'dinner' THEN 3 
                WHEN 'snack' THEN 4 
                ELSE 5 
            END
        """
        
        results = execute_db_query(query, (meal_plan_id,), fetch_all=True)
        
        items = []
        for row in results:
            items.append({
                "id": row[0],
                "meal_plan_id": row[1],
                "meal_id": row[2],
                "meal_name": row[3],
                "day_of_week": row[4],
                "meal_time": row[5],
                "quantity": row[6],
                "notes": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "meal_info": {
                    "calories": row[10],
                    "proteins": row[11],
                    "carbohydrates": row[12],
                    "fats": row[13]
                } if row[10] is not None else None
            })
        
        return items
    except Exception as e:
        logger.error(f"Error al obtener elementos de plan de comida {meal_plan_id}: {e}")
        raise

def get_meal_plan_item(item_id: int) -> Optional[Dict]:
    """Obtiene un elemento/comida específico de un plan de comida."""
    try:
        query = """
        SELECT mpi.id, mpi.meal_plan_id, mpi.meal_id, m.meal_name, mpi.day_of_week, mpi.meal_time, 
               mpi.quantity, mpi.notes, mpi.created_at, mpi.updated_at,
               m.calories, m.proteins, m.carbohydrates, m.fats
        FROM meal_plan_items mpi
        JOIN meals m ON mpi.meal_id = m.id
        WHERE mpi.id = %s
        """
        
        result = execute_db_query(query, (item_id,), fetch_one=True)
        
        if not result:
            return None
        
        return {
            "id": result[0],
            "meal_plan_id": result[1],
            "meal_id": result[2],
            "meal_name": result[3],
            "day_of_week": result[4],
            "meal_time": result[5],
            "quantity": result[6],
            "notes": result[7],
            "created_at": result[8],
            "updated_at": result[9],
            "meal_info": {
                "calories": result[10],
                "proteins": result[11],
                "carbohydrates": result[12],
                "fats": result[13]
            } if result[10] is not None else None
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
            raise ValueError(f"Elemento de plan de comida con ID {item_id} no encontrado")
        
        # Verificar que la comida existe si se cambió
        if 'meal_id' in update_data and update_data['meal_id'] != current_item['meal_id']:
            check_meal_query = "SELECT meal_name FROM meals WHERE id = %s"
            meal_result = execute_db_query(check_meal_query, (update_data['meal_id'],), fetch_one=True)
            
            if not meal_result:
                raise ValueError(f"Comida con ID {update_data['meal_id']} no encontrada")
        
        # Construir consulta dinámica con los campos proporcionados
        update_fields = []
        params = []
        
        if 'meal_plan_id' in update_data:
            update_fields.append("meal_plan_id = %s")
            params.append(update_data['meal_plan_id'])
        
        if 'meal_id' in update_data:
            update_fields.append("meal_id = %s")
            params.append(update_data['meal_id'])
        
        if 'day_of_week' in update_data:
            update_fields.append("day_of_week = %s")
            params.append(update_data['day_of_week'])
        
        if 'meal_time' in update_data:
            update_fields.append("meal_time = %s")
            params.append(update_data['meal_time'])
        
        if 'quantity' in update_data:
            update_fields.append("quantity = %s")
            params.append(update_data['quantity'])
        
        if 'notes' in update_data:
            update_fields.append("notes = %s")
            params.append(update_data['notes'])
        
        # Si no hay campos para actualizar
        if not update_fields:
            return current_item
        
        # Añadir campo updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # Construir consulta
        update_query = f"""
        UPDATE meal_plan_items 
        SET {", ".join(update_fields)}
        WHERE id = %s
        RETURNING id
        """
        
        # Añadir id al final de los parámetros
        params.append(item_id)
        
        result = execute_db_query(update_query, params, fetch_one=True)
        
        if not result:
            return None
            
        # Obtener el elemento actualizado
        return get_meal_plan_item(item_id)
    except Exception as e:
        logger.error(f"Error al actualizar elemento de plan de comida {item_id}: {e}")
        raise

def delete_meal_plan_item(item_id: int) -> bool:
    """Elimina un elemento/comida de un plan de comida."""
    try:
        delete_query = "DELETE FROM meal_plan_items WHERE id = %s"
        result = execute_db_query(delete_query, (item_id,), commit=True)
        
        return bool(result)
    except Exception as e:
        logger.error(f"Error al eliminar elemento de plan de comida {item_id}: {e}")
        raise