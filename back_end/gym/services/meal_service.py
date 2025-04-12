# back_end/gym/services/meal_service.py
import logging
from typing import Optional, List, Dict, Any

from .db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)

#########################################
# Funciones para comidas (meals)
#########################################

def get_meal(meal_id: int, with_ingredients: bool = False) -> Optional[Dict]:
    """Obtiene una comida por su ID. Opcionalmente incluye ingredientes detallados."""
    try:
        query = """
        SELECT id, meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url, created_at, updated_at
        FROM meals
        WHERE id = %s
        """
        
        result = execute_db_query(query, (meal_id,), fetch_one=True)
        
        if not result:
            return None
        
        meal = {
            "id": result[0],
            "meal_name": result[1],
            "recipe": result[2],
            "ingredients": result[3],
            "calories": result[4],
            "proteins": result[5],
            "carbohydrates": result[6],
            "fats": result[7],
            "image_url": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
        
        # Si se solicitan ingredientes detallados
        if with_ingredients:
            ingredients_query = """
            SELECT mi.id, mi.ingredient_id, i.ingredient_name, mi.quantity, 
                   i.calories, i.proteins, i.carbohydrates, i.fats
            FROM meal_ingredients mi
            JOIN ingredients i ON mi.ingredient_id = i.id
            WHERE mi.meal_id = %s
            """
            
            ingredients_results = execute_db_query(ingredients_query, (meal_id,), fetch_all=True)
            
            detailed_ingredients = []
            for row in ingredients_results:
                detailed_ingredients.append({
                    "id": row[0],
                    "ingredient_id": row[1],
                    "name": row[2],
                    "quantity": row[3],
                    "calories_per_100g": row[4],
                    "proteins_per_100g": row[5],
                    "carbs_per_100g": row[6],
                    "fats_per_100g": row[7],
                    "calories_total": (row[4] * row[3]) / 100,
                    "proteins_total": (row[5] * row[3]) / 100,
                    "carbs_total": (row[6] * row[3]) / 100,
                    "fats_total": (row[7] * row[3]) / 100
                })
            
            meal["detailed_ingredients"] = detailed_ingredients
        
        return meal
    except Exception as e:
        logger.error(f"Error al obtener comida {meal_id}: {e}")
        raise

def create_meal(meal_data: Dict) -> Optional[Dict]:
    """Crea una nueva comida."""
    try:
        query = """
        INSERT INTO meals (meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url, created_at, updated_at
        """
        
        params = (
            meal_data.get('meal_name'),
            meal_data.get('recipe'),
            meal_data.get('ingredients'),
            meal_data.get('calories'),
            meal_data.get('proteins'),
            meal_data.get('carbohydrates'),
            meal_data.get('fats'),
            meal_data.get('image_url')
        )
        
        result = execute_db_query(query, params, fetch_one=True)
        
        if not result:
            return None
        
        return {
            "id": result[0],
            "meal_name": result[1],
            "recipe": result[2],
            "ingredients": result[3],
            "calories": result[4],
            "proteins": result[5],
            "carbohydrates": result[6],
            "fats": result[7],
            "image_url": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    except Exception as e:
        logger.error(f"Error al crear comida: {e}")
        raise

def list_meals(search: Optional[str] = None) -> List[Dict]:
    """Lista todas las comidas, con opción de búsqueda."""
    try:
        query = """
        SELECT id, meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url, created_at, updated_at
        FROM meals
        """
        
        params = []
        
        if search:
            query += " WHERE meal_name ILIKE %s"
            params.append(f"%{search}%")
        
        query += " ORDER BY meal_name"
        
        results = execute_db_query(query, params, fetch_all=True)
        
        meals = []
        for row in results:
            meals.append({
                "id": row[0],
                "meal_name": row[1],
                "recipe": row[2],
                "ingredients": row[3],
                "calories": row[4],
                "proteins": row[5],
                "carbohydrates": row[6],
                "fats": row[7],
                "image_url": row[8],
                "created_at": row[9],
                "updated_at": row[10]
            })
        
        return meals
    except Exception as e:
        logger.error(f"Error al listar comidas: {e}")
        raise

def update_meal(meal_id: int, update_data: Dict) -> Optional[Dict]:
    """Actualiza una comida existente."""
    try:
        # Construir consulta dinámica con los campos proporcionados
        update_fields = []
        params = []
        
        if 'meal_name' in update_data:
            update_fields.append("meal_name = %s")
            params.append(update_data['meal_name'])
        
        if 'recipe' in update_data:
            update_fields.append("recipe = %s")
            params.append(update_data['recipe'])
        
        if 'ingredients' in update_data:
            update_fields.append("ingredients = %s")
            params.append(update_data['ingredients'])
        
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
        
        if 'image_url' in update_data:
            update_fields.append("image_url = %s")
            params.append(update_data['image_url'])
        
        # Si no hay campos para actualizar
        if not update_fields:
            return get_meal(meal_id)
        
        # Añadir campo updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # Construir consulta
        update_query = f"""
        UPDATE meals 
        SET {", ".join(update_fields)}
        WHERE id = %s
        RETURNING id, meal_name, recipe, ingredients, calories, proteins, carbohydrates, fats, image_url, created_at, updated_at
        """
        
        # Añadir id al final de los parámetros
        params.append(meal_id)
        
        result = execute_db_query(update_query, params, fetch_one=True)
        
        if not result:
            return None
            
        return {
            "id": result[0],
            "meal_name": result[1],
            "recipe": result[2],
            "ingredients": result[3],
            "calories": result[4],
            "proteins": result[5],
            "carbohydrates": result[6],
            "fats": result[7],
            "image_url": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    except Exception as e:
        logger.error(f"Error al actualizar comida {meal_id}: {e}")
        raise

def delete_meal(meal_id: int) -> bool:
    """Elimina una comida."""
    try:
        # Verificar si la comida está siendo usada en algún plan
        check_usage_query = """
        SELECT COUNT(*) FROM meal_plan_items WHERE meal_id = %s
        """
        
        usage_count = execute_db_query(check_usage_query, (meal_id,), fetch_one=True)
        
        if usage_count and usage_count[0] > 0:
            raise ValueError(f"No se puede eliminar la comida porque está siendo usada en {usage_count[0]} planes de comida")
            
        # Primero eliminar los ingredientes asociados
        delete_ingredients_query = "DELETE FROM meal_ingredients WHERE meal_id = %s"
        execute_db_query(delete_ingredients_query, (meal_id,), commit=True)
        
        # Luego eliminar la comida
        delete_query = "DELETE FROM meals WHERE id = %s"
        result = execute_db_query(delete_query, (meal_id,), commit=True)
        
        return bool(result)
    except Exception as e:
        logger.error(f"Error al eliminar comida {meal_id}: {e}")
        raise

def check_meal_exists(meal_id: int) -> bool:
    """Verifica si una comida existe."""
    try:
        query = "SELECT id FROM meals WHERE id = %s"
        result = execute_db_query(query, (meal_id,), fetch_one=True)
        return result is not None
    except Exception as e:
        logger.error(f"Error al verificar existencia de comida {meal_id}: {e}")
        raise

#########################################
# Funciones para relaciones meal-ingredient
#########################################

def add_ingredient_to_meal(meal_id: int, ingredient_id: int, quantity: float) -> Optional[Dict]:
    """Añade un ingrediente a una comida con su cantidad."""
    try:
        # Obtener nombres de comida e ingrediente para la respuesta
        check_meal_query = "SELECT meal_name FROM meals WHERE id = %s"
        meal_result = execute_db_query(check_meal_query, (meal_id,), fetch_one=True)
        
        if not meal_result:
            raise ValueError(f"Comida con ID {meal_id} no encontrada")
        
        check_ingredient_query = "SELECT ingredient_name FROM ingredients WHERE id = %s"
        ingredient_result = execute_db_query(check_ingredient_query, (ingredient_id,), fetch_one=True)
        
        if not ingredient_result:
            raise ValueError(f"Ingrediente con ID {ingredient_id} no encontrado")
        
        # Insertar la relación
        query = """
        INSERT INTO meal_ingredients (meal_id, ingredient_id, quantity)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        
        params = (meal_id, ingredient_id, quantity)
        
        result = execute_db_query(query, params, fetch_one=True)
        
        if not result:
            return None
        
        # Recalcular automáticamente las macros de la comida
        recalculate_meal_macros(meal_id)
        
        return {
            "id": result[0],
            "meal_id": meal_id,
            "ingredient_id": ingredient_id,
            "quantity": quantity,
            "meal_name": meal_result[0],
            "ingredient_name": ingredient_result[0]
        }
    except Exception as e:
        logger.error(f"Error al añadir ingrediente {ingredient_id} a comida {meal_id}: {e}")
        raise

def get_meal_ingredients(meal_id: int) -> List[Dict]:
    """Obtiene todos los ingredientes de una comida con sus cantidades."""
    try:
        # Verificar si la comida existe
        if not check_meal_exists(meal_id):
            raise ValueError(f"Comida con ID {meal_id} no encontrada")
        
        # Obtener los ingredientes
        query = """
        SELECT mi.id, mi.ingredient_id, i.ingredient_name, mi.quantity, 
               i.calories, i.proteins, i.carbohydrates, i.fats
        FROM meal_ingredients mi
        JOIN ingredients i ON mi.ingredient_id = i.id
        WHERE mi.meal_id = %s
        ORDER BY i.ingredient_name
        """
        
        results = execute_db_query(query, (meal_id,), fetch_all=True)
        
        ingredients = []
        for row in results:
            ingredients.append({
                "id": row[0],
                "ingredient_id": row[1],
                "ingredient_name": row[2],
                "quantity": row[3],
                "calories_per_100g": row[4],
                "proteins_per_100g": row[5],
                "carbs_per_100g": row[6],
                "fats_per_100g": row[7],
                "calories_total": (row[4] * row[3]) / 100,
                "proteins_total": (row[5] * row[3]) / 100,
                "carbs_total": (row[6] * row[3]) / 100,
                "fats_total": (row[7] * row[3]) / 100
            })
        
        return ingredients
    except Exception as e:
        logger.error(f"Error al obtener ingredientes de comida {meal_id}: {e}")
        raise

def update_meal_ingredient(meal_ingredient_id: int, update_data: Dict) -> Optional[Dict]:
    """Actualiza la cantidad de un ingrediente en una comida."""
    try:
        # Verificar si la relación existe
        check_query = """
        SELECT mi.id, mi.meal_id, mi.ingredient_id, m.meal_name, i.ingredient_name, mi.quantity
        FROM meal_ingredients mi
        JOIN meals m ON mi.meal_id = m.id
        JOIN ingredients i ON mi.ingredient_id = i.id
        WHERE mi.id = %s
        """
        
        relation = execute_db_query(check_query, (meal_ingredient_id,), fetch_one=True)
        
        if not relation:
            raise ValueError(f"Relación comida-ingrediente con ID {meal_ingredient_id} no encontrada")
        
        meal_id = relation[1]
        ingredient_id = relation[2]
        meal_name = relation[3]
        ingredient_name = relation[4]
        current_quantity = relation[5]
        
        # Verificar que los nuevos valores existen si se están cambiando
        new_meal_id = update_data.get('meal_id', meal_id)
        if new_meal_id != meal_id:
            check_new_meal = "SELECT meal_name FROM meals WHERE id = %s"
            new_meal = execute_db_query(check_new_meal, (new_meal_id,), fetch_one=True)
            
            if not new_meal:
                raise ValueError(f"Comida con ID {new_meal_id} no encontrada")
            
            meal_id = new_meal_id
            meal_name = new_meal[0]
        
        new_ingredient_id = update_data.get('ingredient_id', ingredient_id)
        if new_ingredient_id != ingredient_id:
            check_new_ingredient = "SELECT ingredient_name FROM ingredients WHERE id = %s"
            new_ingredient = execute_db_query(check_new_ingredient, (new_ingredient_id,), fetch_one=True)
            
            if not new_ingredient:
                raise ValueError(f"Ingrediente con ID {new_ingredient_id} no encontrado")
            
            ingredient_id = new_ingredient_id
            ingredient_name = new_ingredient[0]
        
        quantity = update_data.get('quantity', current_quantity)
        
        # Construir consulta
        update_query = """
        UPDATE meal_ingredients 
        SET meal_id = %s, ingredient_id = %s, quantity = %s
        WHERE id = %s
        RETURNING id, meal_id, ingredient_id, quantity
        """
        
        params = (meal_id, ingredient_id, quantity, meal_ingredient_id)
        
        result = execute_db_query(update_query, params, fetch_one=True)
        
        if not result:
            return None
            
        # Recalcular los macros de la comida original y la nueva si cambió
        original_meal_id = relation[1]
        recalculate_meal_macros(original_meal_id)
        
        if meal_id != original_meal_id:
            recalculate_meal_macros(meal_id)
        
        return {
            "id": result[0],
            "meal_id": result[1],
            "ingredient_id": result[2],
            "quantity": result[3],
            "meal_name": meal_name,
            "ingredient_name": ingredient_name
        }
    except Exception as e:
        logger.error(f"Error al actualizar ingrediente en comida {meal_ingredient_id}: {e}")
        raise

def delete_meal_ingredient(meal_ingredient_id: int) -> bool:
    """Elimina un ingrediente de una comida."""
    try:
        # Verificar si la relación existe y obtener el meal_id para recalcular macros después
        check_query = "SELECT meal_id FROM meal_ingredients WHERE id = %s"
        relation = execute_db_query(check_query, (meal_ingredient_id,), fetch_one=True)
        
        if not relation:
            raise ValueError(f"Relación comida-ingrediente con ID {meal_ingredient_id} no encontrada")
        
        meal_id = relation[0]
        
        # Eliminar la relación
        delete_query = "DELETE FROM meal_ingredients WHERE id = %s"
        result = execute_db_query(delete_query, (meal_ingredient_id,), commit=True)
        
        # Recalcular automáticamente las macros de la comida
        recalculate_meal_macros(meal_id)
        
        return bool(result)
    except Exception as e:
        logger.error(f"Error al eliminar ingrediente de comida {meal_ingredient_id}: {e}")
        raise

def recalculate_meal_macros(meal_id: int) -> bool:
    """Recalcula los macros de una comida basado en sus ingredientes."""
    try:
        # Calcular los macros totales sumando los ingredientes
        calculation_query = """
        SELECT
            SUM((i.calories * mi.quantity) / 100) as total_calories,
            SUM((i.proteins * mi.quantity) / 100) as total_proteins,
            SUM((i.carbohydrates * mi.quantity) / 100) as total_carbs,
            SUM((i.fats * mi.quantity) / 100) as total_fats
        FROM
            meal_ingredients mi
        JOIN
            ingredients i ON mi.ingredient_id = i.id
        WHERE
            mi.meal_id = %s
        """
        
        result = execute_db_query(calculation_query, (meal_id,), fetch_one=True)
        
        # Si no hay ingredientes, establecer todos los valores a 0
        if not result or all(v is None for v in result):
            calories = 0
            proteins = 0
            carbs = 0
            fats = 0
        else:
            calories = result[0] or 0
            proteins = result[1] or 0
            carbs = result[2] or 0
            fats = result[3] or 0
        
        # Actualizar la comida con los nuevos valores
        update_query = """
        UPDATE meals
        SET
            calories = %s,
            proteins = %s,
            carbohydrates = %s,
            fats = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE
            id = %s
        """
        
        update_params = (
            round(calories),
            round(proteins, 1),
            round(carbs, 1),
            round(fats, 1),
            meal_id
        )
        
        execute_db_query(update_query, update_params, commit=True)
        
        logger.info(f"Macros recalculados para comida ID {meal_id}: {calories} kcal, {proteins}g proteínas, {carbs}g carbohidratos, {fats}g grasas")
        return True
        
    except Exception as e:
        logger.error(f"Error al recalcular macros para comida ID {meal_id}: {e}")
        return False