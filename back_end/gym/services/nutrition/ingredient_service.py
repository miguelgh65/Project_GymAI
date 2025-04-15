# back_end/gym/services/nutrition/ingredient_service.py
import logging
from typing import Optional, List, Dict

# Corregir esta importación para usar una ruta absoluta o la ruta relativa correcta
from back_end.gym.services.db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)

def get_ingredient(ingredient_id: int) -> Optional[Dict]:
    """Obtiene un ingrediente por su ID."""
    try:
        query = """
        SELECT id, ingredient_name, calories, proteins, carbohydrates, fats, created_at, updated_at
        FROM ingredients
        WHERE id = %s
        """
        
        result = execute_db_query(query, (ingredient_id,), fetch_one=True)
        
        if not result:
            return None
        
        return {
            "id": result[0],
            "ingredient_name": result[1],
            "calories": result[2],
            "proteins": result[3],
            "carbohydrates": result[4],
            "fats": result[5],
            "created_at": result[6],
            "updated_at": result[7]
        }
    except Exception as e:
        logger.error(f"Error al obtener ingrediente {ingredient_id}: {e}")
        raise

def create_ingredient(ingredient_data: Dict) -> Optional[Dict]:
    """Crea un nuevo ingrediente."""
    try:
        query = """
        INSERT INTO ingredients (ingredient_name, calories, proteins, carbohydrates, fats)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, ingredient_name, calories, proteins, carbohydrates, fats, created_at, updated_at
        """
        
        params = (
            ingredient_data.get('ingredient_name'),
            ingredient_data.get('calories'),
            ingredient_data.get('proteins'),
            ingredient_data.get('carbohydrates'),
            ingredient_data.get('fats')
        )
        
        result = execute_db_query(query, params, fetch_one=True)
        
        if not result:
            return None
        
        return {
            "id": result[0],
            "ingredient_name": result[1],
            "calories": result[2],
            "proteins": result[3],
            "carbohydrates": result[4],
            "fats": result[5],
            "created_at": result[6],
            "updated_at": result[7]
        }
    except Exception as e:
        logger.error(f"Error al crear ingrediente: {e}")
        raise

def list_ingredients(search: Optional[str] = None) -> List[Dict]:
    """Lista todos los ingredientes, con opción de búsqueda."""
    try:
        query = """
        SELECT id, ingredient_name, calories, proteins, carbohydrates, fats, created_at, updated_at
        FROM ingredients
        """
        
        params = []
        
        if search:
            query += " WHERE ingredient_name ILIKE %s"
            params.append(f"%{search}%")
        
        query += " ORDER BY ingredient_name"
        
        results = execute_db_query(query, params, fetch_all=True)
        
        ingredients = []
        for row in results:
            ingredients.append({
                "id": row[0],
                "ingredient_name": row[1],
                "calories": row[2],
                "proteins": row[3],
                "carbohydrates": row[4],
                "fats": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            })
        
        return ingredients
    except Exception as e:
        logger.error(f"Error al listar ingredientes: {e}")
        raise

def update_ingredient(ingredient_id: int, update_data: Dict) -> Optional[Dict]:
    """Actualiza un ingrediente existente."""
    try:
        # Construir consulta dinámica con los campos proporcionados
        update_fields = []
        params = []
        
        if 'ingredient_name' in update_data:
            update_fields.append("ingredient_name = %s")
            params.append(update_data['ingredient_name'])
        
        if 'calories' in update_data:
            update_fields.append("calories = %s")
            params.append(update_data['calories'])
        
        if 'proteins' in update_data:
            update_fields.append("proteins = %s")
            params.append(update_data['proteins'])
        
        if 'carbohydrates' in update_data:
            update_fields.append("carbohydrates = %s")
            params.append(update_data['carbohydrates'])
        
        if 'fats' in update_data:
            update_fields.append("fats = %s")
            params.append(update_data['fats'])
        
        # Si no hay campos para actualizar
        if not update_fields:
            return get_ingredient(ingredient_id)
        
        # Añadir campo updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # Construir consulta
        update_query = f"""
        UPDATE ingredients 
        SET {", ".join(update_fields)}
        WHERE id = %s
        RETURNING id, ingredient_name, calories, proteins, carbohydrates, fats, created_at, updated_at
        """
        
        # Añadir id al final de los parámetros
        params.append(ingredient_id)
        
        result = execute_db_query(update_query, params, fetch_one=True)
        
        if not result:
            return None
            
        return {
            "id": result[0],
            "ingredient_name": result[1],
            "calories": result[2],
            "proteins": result[3],
            "carbohydrates": result[4],
            "fats": result[5],
            "created_at": result[6],
            "updated_at": result[7]
        }
    except Exception as e:
        logger.error(f"Error al actualizar ingrediente {ingredient_id}: {e}")
        raise

def delete_ingredient(ingredient_id: int) -> bool:
    """Elimina un ingrediente."""
    try:
        # Verificar si el ingrediente está siendo usado en alguna comida
        check_usage_query = """
        SELECT COUNT(*) FROM meal_ingredients WHERE ingredient_id = %s
        """
        
        usage_count = execute_db_query(check_usage_query, (ingredient_id,), fetch_one=True)
        
        if usage_count and usage_count[0] > 0:
            raise ValueError(f"No se puede eliminar el ingrediente porque está siendo usado en {usage_count[0]} comidas")
            
        # Eliminar el ingrediente
        delete_query = "DELETE FROM ingredients WHERE id = %s"
        result = execute_db_query(delete_query, (ingredient_id,), commit=True)
        
        return bool(result)
    except Exception as e:
        logger.error(f"Error al eliminar ingrediente {ingredient_id}: {e}")
        raise

def check_ingredient_exists(ingredient_id: int) -> bool:
    """Verifica si un ingrediente existe."""
    try:
        query = "SELECT id FROM ingredients WHERE id = %s"
        result = execute_db_query(query, (ingredient_id,), fetch_one=True)
        return result is not None
    except Exception as e:
        logger.error(f"Error al verificar existencia de ingrediente {ingredient_id}: {e}")
        raise