# back_end/gym/services/nutrition/meal_plans_service.py
import logging
from typing import Optional, List, Dict
import decimal
import datetime

# Corregir esta importación para usar una ruta absoluta
from back_end.gym.services.db_utils import execute_db_query

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
            str(user_id),  # Convertir user_id a string
            plan_data.get('plan_name', ''),
            plan_data.get('start_date'),
            plan_data.get('end_date'),
            plan_data.get('description', ''),
            plan_data.get('is_active', True)
        )
        
        result = execute_db_query(query, params, fetch_one=True)
        
        if not result:
            return None
        
        # Log para depuración
        logger.info(f"Plan de comida creado: {result}")
        
        # Convertir tipos de datos para serialización JSON
        return {
            "id": result[0],
            "user_id": result[1],
            "plan_name": result[2] or "",
            "start_date": result[3].isoformat() if isinstance(result[3], (datetime.date, datetime.datetime)) else result[3],
            "end_date": result[4].isoformat() if isinstance(result[4], (datetime.date, datetime.datetime)) else result[4],
            "description": result[5] or "",
            "is_active": result[6],
            "created_at": result[7].isoformat() if isinstance(result[7], (datetime.date, datetime.datetime)) else result[7],
            "updated_at": result[8].isoformat() if isinstance(result[8], (datetime.date, datetime.datetime)) else result[8]
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
        
        params = [str(user_id)]  # Convertir user_id a string
        
        if is_active is not None:
            query += " AND is_active = %s"
            params.append(is_active)
        
        query += " ORDER BY created_at DESC"
        
        # Log para depuración
        logger.info(f"Ejecutando query para planes de comida del usuario {user_id}: {query}")
        logger.info(f"Parámetros: {params}")
        
        results = execute_db_query(query, params, fetch_all=True)
        
        # Log de resultados
        logger.info(f"Número de planes de comida encontrados: {len(results)}")
        
        meal_plans = []
        for row in results:
            # Convertir los tipos de datos para serialización JSON
            meal_plan = {
                "id": row[0],
                "user_id": row[1],
                "plan_name": row[2] or "",
                "start_date": row[3].isoformat() if isinstance(row[3], (datetime.date, datetime.datetime)) else row[3],
                "end_date": row[4].isoformat() if isinstance(row[4], (datetime.date, datetime.datetime)) else row[4],
                "description": row[5] or "",
                "is_active": row[6],
                "created_at": row[7].isoformat() if isinstance(row[7], (datetime.date, datetime.datetime)) else row[7],
                "updated_at": row[8].isoformat() if isinstance(row[8], (datetime.date, datetime.datetime)) else row[8]
            }
            meal_plans.append(meal_plan)
            
        # Verificar lista vacía
        if not meal_plans:
            logger.warning(f"No se encontraron planes de comida para el usuario {user_id}")
        
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
        
        # Log para depuración
        logger.info(f"Buscando plan {meal_plan_id} para usuario {user_id}")
        
        result = execute_db_query(query, (meal_plan_id, str(user_id)), fetch_one=True)  # Convertir user_id a string
        
        if not result:
            logger.warning(f"No se encontró el plan {meal_plan_id} para el usuario {user_id}")
            return None
        
        # Log para depuración
        logger.info(f"Plan de comida encontrado: {result}")
        
        # Convertir para serialización JSON
        meal_plan = {
            "id": result[0],
            "user_id": result[1],
            "plan_name": result[2] or "",
            "start_date": result[3].isoformat() if isinstance(result[3], (datetime.date, datetime.datetime)) else result[3],
            "end_date": result[4].isoformat() if isinstance(result[4], (datetime.date, datetime.datetime)) else result[4],
            "description": result[5] or "",
            "is_active": result[6],
            "created_at": result[7].isoformat() if isinstance(result[7], (datetime.date, datetime.datetime)) else result[7],
            "updated_at": result[8].isoformat() if isinstance(result[8], (datetime.date, datetime.datetime)) else result[8]
        }
        
        # Obtener los elementos del plan si se solicita
        if with_items:
            # Corregir esta importación
            from back_end.gym.services.nutrition.meal_plan_items_service import get_meal_plan_items
            items = get_meal_plan_items(meal_plan_id)
            
            # Log para depuración
            logger.info(f"Elementos encontrados para el plan {meal_plan_id}: {len(items)}")
            
            # Convertir tipos de datos en los items si es necesario
            for item in items:
                for key, value in item.items():
                    if isinstance(value, decimal.Decimal):
                        item[key] = float(value)
                    elif isinstance(value, (datetime.datetime, datetime.date)):
                        item[key] = value.isoformat()
            
            meal_plan["items"] = items
        
        return meal_plan
    except Exception as e:
        logger.error(f"Error al obtener plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise

# El resto del código permanece igual...
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
        params.append(str(user_id))  # Convertir user_id a string
        
        result = execute_db_query(update_query, params, fetch_one=True)
        
        if not result:
            return None
        
        # Convertir para serialización JSON
        return {
            "id": result[0],
            "user_id": result[1],
            "plan_name": result[2],
            "start_date": result[3].isoformat() if isinstance(result[3], (datetime.date, datetime.datetime)) else result[3],
            "end_date": result[4].isoformat() if isinstance(result[4], (datetime.date, datetime.datetime)) else result[4],
            "description": result[5],
            "is_active": result[6],
            "created_at": result[7].isoformat() if isinstance(result[7], (datetime.date, datetime.datetime)) else result[7],
            "updated_at": result[8].isoformat() if isinstance(result[8], (datetime.date, datetime.datetime)) else result[8]
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
        execute_db_query(delete_items_query, (meal_plan_id, str(user_id)), commit=True)  # Convertir user_id a string
        
        # Luego eliminar el plan
        delete_query = "DELETE FROM meal_plans WHERE id = %s AND user_id = %s"
        result = execute_db_query(delete_query, (meal_plan_id, str(user_id)), commit=True)  # Convertir user_id a string
        
        return bool(result)
    except Exception as e:
        logger.error(f"Error al eliminar plan de comida {meal_plan_id} para usuario {user_id}: {e}")
        raise