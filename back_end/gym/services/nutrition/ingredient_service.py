# back_end/gym/services/nutrition/ingredient_service.py
"""
Servicio de ingredientes refactorizado siguiendo principios SOLID.
Mantiene 100% compatibilidad con tests existentes.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from dataclasses import dataclass

# Importación EXACTA como en el código original para compatibilidad con tests
from back_end.gym.services.db_utils import execute_db_query

# Configurar logger
logger = logging.getLogger(__name__)


# ================================
# DOMAIN MODELS (SRP)
# ================================

@dataclass
class IngredientData:
    """Modelo de dominio para ingredientes que encapsula los datos."""
    id: Optional[int] = None
    ingredient_name: str = ""
    calories: float = 0.0
    proteins: float = 0.0
    carbohydrates: float = 0.0
    fats: float = 0.0
    created_at: Optional[object] = None
    updated_at: Optional[object] = None

    def to_dict(self) -> Dict:
        """Convierte el ingrediente a diccionario para API response."""
        return {
            "id": self.id,
            "ingredient_name": self.ingredient_name,
            "calories": self.calories,
            "proteins": self.proteins,
            "carbohydrates": self.carbohydrates,
            "fats": self.fats,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


# ================================
# REPOSITORY INTERFACE (ISP + DIP)
# ================================

class IIngredientRepository(ABC):
    """Interface para el repositorio de ingredientes siguiendo ISP."""
    
    @abstractmethod
    def get_by_id(self, ingredient_id: int) -> Optional[Dict]:
        """Obtiene un ingrediente por su ID."""
        pass
    
    @abstractmethod
    def create(self, ingredient_data: Dict) -> Optional[Dict]:
        """Crea un nuevo ingrediente."""
        pass
    
    @abstractmethod
    def list_all(self, search: Optional[str] = None) -> List[Dict]:
        """Lista todos los ingredientes, con opción de búsqueda."""
        pass
    
    @abstractmethod
    def update(self, ingredient_id: int, update_data: Dict) -> Optional[Dict]:
        """Actualiza un ingrediente existente."""
        pass
    
    @abstractmethod
    def delete(self, ingredient_id: int) -> bool:
        """Elimina un ingrediente."""
        pass
    
    @abstractmethod
    def exists(self, ingredient_id: int) -> bool:
        """Verifica si un ingrediente existe."""
        pass


class IIngredientUsageChecker(ABC):
    """Interface para verificar el uso de ingredientes siguiendo ISP."""
    
    @abstractmethod
    def count_usages(self, ingredient_id: int) -> int:
        """Cuenta cuántas veces se usa un ingrediente."""
        pass


# ================================
# REPOSITORY IMPLEMENTATION (SRP)
# ================================

class DatabaseIngredientRepository(IIngredientRepository):
    """
    Implementación del repositorio de ingredientes usando base de datos.
    Responsabilidad única: acceso a datos de ingredientes.
    """
    
    def get_by_id(self, ingredient_id: int) -> Optional[Dict]:
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

    def create(self, ingredient_data: Dict) -> Optional[Dict]:
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

    def list_all(self, search: Optional[str] = None) -> List[Dict]:
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

    def update(self, ingredient_id: int, update_data: Dict) -> Optional[Dict]:
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
            
            # Si no hay campos para actualizar, retornar un marcador especial
            if not update_fields:
                return {"_should_get_ingredient": True, "_ingredient_id": ingredient_id}
            
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

    def delete(self, ingredient_id: int) -> bool:
        """Elimina un ingrediente."""
        try:
            delete_query = "DELETE FROM ingredients WHERE id = %s"
            result = execute_db_query(delete_query, (ingredient_id,), commit=True)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error al eliminar ingrediente {ingredient_id}: {e}")
            raise

    def exists(self, ingredient_id: int) -> bool:
        """Verifica si un ingrediente existe."""
        try:
            query = "SELECT id FROM ingredients WHERE id = %s"
            result = execute_db_query(query, (ingredient_id,), fetch_one=True)
            return result is not None
        except Exception as e:
            logger.error(f"Error al verificar existencia de ingrediente {ingredient_id}: {e}")
            raise


class DatabaseIngredientUsageChecker(IIngredientUsageChecker):
    """
    Implementación del verificador de uso de ingredientes.
    Responsabilidad única: verificar si ingredientes están en uso.
    """
    
    def count_usages(self, ingredient_id: int) -> int:
        """Cuenta cuántas veces se usa un ingrediente."""
        try:
            check_usage_query = """
            SELECT COUNT(*) FROM meal_ingredients WHERE ingredient_id = %s
            """
            
            usage_count = execute_db_query(check_usage_query, (ingredient_id,), fetch_one=True)
            
            return usage_count[0] if usage_count else 0
        except Exception as e:
            logger.error(f"Error al verificar uso de ingrediente {ingredient_id}: {e}")
            raise


# ================================
# BUSINESS LOGIC SERVICE (SRP + DIP)
# ================================

class IngredientBusinessService:
    """
    Servicio de lógica de negocio para ingredientes.
    Responsabilidad única: lógica de negocio y orquestación.
    Depende de abstracciones (DIP).
    """
    
    def __init__(self, repository: IIngredientRepository, usage_checker: IIngredientUsageChecker):
        """Inicializa el servicio con sus dependencias inyectadas."""
        self._repository = repository
        self._usage_checker = usage_checker

    def get_ingredient(self, ingredient_id: int) -> Optional[Dict]:
        """Obtiene un ingrediente por su ID - comportamiento idéntico al original."""
        return self._repository.get_by_id(ingredient_id)

    def create_ingredient(self, ingredient_data: Dict) -> Optional[Dict]:
        """Crea un nuevo ingrediente - comportamiento idéntico al original."""
        return self._repository.create(ingredient_data)

    def list_ingredients(self, search: Optional[str] = None) -> List[Dict]:
        """Lista todos los ingredientes - comportamiento idéntico al original."""
        return self._repository.list_all(search)

    def update_ingredient(self, ingredient_id: int, update_data: Dict) -> Optional[Dict]:
        """Actualiza un ingrediente - comportamiento idéntico al original."""
        return self._repository.update(ingredient_id, update_data)

    def delete_ingredient(self, ingredient_id: int) -> bool:
        """Elimina un ingrediente - comportamiento idéntico al original."""
        # Verificar si el ingrediente está siendo usado
        usage_count = self._usage_checker.count_usages(ingredient_id)
        
        if usage_count > 0:
            raise ValueError(f"No se puede eliminar el ingrediente porque está siendo usado en {usage_count} comidas")
        
        return self._repository.delete(ingredient_id)

    def check_ingredient_exists(self, ingredient_id: int) -> bool:
        """Verifica si un ingrediente existe - comportamiento idéntico al original."""
        return self._repository.exists(ingredient_id)


# ================================
# DEPENDENCY INJECTION CONTAINER (DIP)
# ================================

class IngredientServiceContainer:
    """
    Container para la inyección de dependencias.
    Sigue el patrón Singleton para mantener una única instancia.
    """
    _instance = None
    _service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_service(self) -> IngredientBusinessService:
        """Obtiene la instancia del servicio con lazy loading."""
        if self._service is None:
            # Crear dependencias concretas
            repository = DatabaseIngredientRepository()
            usage_checker = DatabaseIngredientUsageChecker()
            
            # Crear servicio con dependencias inyectadas
            self._service = IngredientBusinessService(repository, usage_checker)
        
        return self._service

    def reset_service(self):
        """Resetea el servicio (útil para testing)."""
        self._service = None


# ================================
# PUBLIC API - MANTIENE COMPATIBILIDAD 100%
# ================================

# Container singleton
_container = IngredientServiceContainer()

def get_ingredient(ingredient_id: int) -> Optional[Dict]:
    """Obtiene un ingrediente por su ID."""
    return _container.get_service().get_ingredient(ingredient_id)

def create_ingredient(ingredient_data: Dict) -> Optional[Dict]:
    """Crea un nuevo ingrediente."""
    return _container.get_service().create_ingredient(ingredient_data)

def list_ingredients(search: Optional[str] = None) -> List[Dict]:
    """Lista todos los ingredientes, con opción de búsqueda."""
    return _container.get_service().list_ingredients(search)

def update_ingredient(ingredient_id: int, update_data: Dict) -> Optional[Dict]:
    """Actualiza un ingrediente existente."""
    result = _container.get_service().update_ingredient(ingredient_id, update_data)
    
    # Si el resultado indica que se debe llamar get_ingredient (comportamiento original)
    if isinstance(result, dict) and result.get("_should_get_ingredient"):
        return get_ingredient(ingredient_id)
    
    return result

def delete_ingredient(ingredient_id: int) -> bool:
    """Elimina un ingrediente."""
    return _container.get_service().delete_ingredient(ingredient_id)

def check_ingredient_exists(ingredient_id: int) -> bool:
    """Verifica si un ingrediente existe."""
    return _container.get_service().check_ingredient_exists(ingredient_id)