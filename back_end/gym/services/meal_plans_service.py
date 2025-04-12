# back_end/gym/services/meal_plans_service.py
import logging
from typing import Optional, List, Dict

from .db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)

def create_meal_plan(user_id: str, plan_data: Dict) -> Optional[Dict]:
    """Crea un nuevo plan de comida."""
    try:
        query = """
        INSERT INTO meal_plans (user_id, plan_name, start_date, end_date, description, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, plan_name, start_date, end_date, description, is_active, created_at, updated_at
        """
        
        params = (
            user_id,
            plan_data.get('plan_name'),
            plan_data.get('start_date'),
            plan_data.get('end_date'),
            plan_data.get('description'),
            plan_data.get('is_active', True)
        )
        
        result = execute_db_query(query, params, fetch_one=True)
        
        if not result:
            return None
        
        return {
            "id": result[0],
            "user_id": result[1],
            "plan_name": result[2],
            "start_date": result[3],
            "end_date": result[4],
            "description": result[5],
            "is_active": result[6],
            "created_at": result[7],
            "updated_at": result[8]
        }
    except Exception as e:
        logger.error(f"Error al crear plan de comida para usuario {user_id}: {e}")
        raise

def list_meal_plans(user_id: str, is_active: Optional[bool] = None) -> List[Dict]:
    """Lista todos los planes de comida del usuario."""
    try:
        query = """
        SELECT id, user_id, plan_name, start_date, end_date, description, is_active, created_at, updated_at
        FROM meal_plans
        WHERE user_id = %s
        """
        
        params = [user_id]
        
        if is_active is not None:
            query += " AND is_active = %s"
            params.append(is_active)
        
        query += " ORDER BY created_at DESC"
        
        results = execute_db_query(query, params, fetch_all=True)
        
        meal_plans = []
        for row in results:
            meal_plans.append({
                "id": row[0],
                "user_id": row[1],
                "plan_name": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "description": row[5],
                "is_active": row[6],
                "created_at": row[7],
                "updated_at": row[8]
            })
        
        return meal_plans
    except Exception as e:
        logger.error(f"Error al listar planes de comida para usuario {user_id}: {e}")
        raise

def get_meal_plan(meal_plan_id: int, user_id: str, with_items: bool = True) -> Optional[Dict]:
    """Obtiene un plan de comida por su ID, opcionalmente incluyendo todos sus elementos/comidas."""
    try:
        # Obtener el plan de comida
        query = """
        SELECT id, user_id, plan_name, start_date, end_date, description, is_active, created_at, updated_at
        FROM meal_plans
        WHERE id = %s AND user_id = %s
        """
        
        result = execute_db_query(query, (meal_plan_id, user_id), fetch_one=True)
        
        if not result:
            return None
        
        meal_plan = {
            "id": result[0],
            "user_id": result[1],
            "plan_name": result[2],
            "start_date": result[3],
            "end_date": result[4],
            "description": result[5],
            "is_active": result[6],
            "created_at": result[7],
            "updated_at": result[8],
        }
        
        # Obtener los elementos del plan si se solicita
        if with_items:
            from .meal_plan_items_service import get_meal_plan_items
            meal_plan["items"] = get_meal_plan_items(meal_plan_id)
        
        return meal_plan
    except Exception as e:
        logger.error(f"Error al obtener plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise

def update_meal_plan(meal_plan_id: int, user_id: str, update_data: Dict) -> Optional[Dict]:
    """Actualiza un plan de comida existente."""
    try:
        # Construir consulta dinámica con los campos proporcionados
        update_fields = []
        params = []
        
        if 'plan_name' in update_data:
            update_fields.append("plan_name = %s")
            params.append(update_data['plan_name'])
        
        if 'start_date' in update_data:
            update_fields.append("start_date = %s")
            params.append(update_data['start_date'])
        
        if 'end_date' in update_data:
            update_fields.append("end_date = %s")
            params.append(update_data['end_date'])
        
        if 'description' in update_data:
            update_fields.append("description = %s")
            params.append(update_data['description'])
        
        if 'is_active' in update_data:
            update_fields.append("is_active = %s")
            params.append(update_data['is_active'])
        
        # Si no hay campos para actualizar
        if not update_fields:
            return get_meal_plan(meal_plan_id, user_id)
        
        # Añadir campo updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # Construir consulta
        update_query = f"""
        UPDATE meal_plans 
        SET {", ".join(update_fields)}
        WHERE id = %s AND user_id = %s
        RETURNING id, user_id, plan_name, start_date, end_date, description, is_active, created_at, updated_at
        """
        
        # Añadir id y user_id al final de los parámetros
        params.append(meal_plan_id)
        params.append(user_id)
        
        result = execute_db_query(update_query, params, fetch_one=True)
        
        if not result:
            return None
            
        return {
            "id": result[0],
            "user_id": result[1],
            "plan_name": result[2],
            "start_date": result[3],
            "end_date": result[4],
            "description": result[5],
            "is_active": result[6],
            "created_at": result[7],
            "updated_at": result[8]
        }
    except Exception as e:
        logger.error(f"Error al actualizar plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise

def delete_meal_plan(meal_plan_id: int, user_id: str) -> bool:
    """Elimina un plan de comida."""
    try:
        # Primero eliminar los elementos del plan
        delete_items_query = """
        DELETE FROM meal_plan_items 
        WHERE meal_plan_id = %s 
        AND meal_plan_id IN (SELECT id FROM meal_plans WHERE user_id = %s)
        """
        execute_db_query(delete_items_query, (meal_plan_id, user_id), commit=True)
        
        # Luego eliminar el plan
        delete_query = "DELETE FROM meal_plans WHERE id = %s AND user_id = %s"
        result = execute_db_query(delete_query, (meal_plan_id, user_id), commit=True)
        
        return bool(result)
    except Exception as e:
        logger.error(f"Error al eliminar plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise