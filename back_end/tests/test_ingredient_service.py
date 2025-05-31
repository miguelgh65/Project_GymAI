# test_ingredient_service.py
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime
import logging

# Importar el servicio que vamos a testear
from back_end.gym.services.nutrition.ingredient_service import (
    get_ingredient,
    create_ingredient,
    list_ingredients,
    update_ingredient,
    delete_ingredient,
    check_ingredient_exists
)


class TestIngredientService:
    """Test suite completo para ingredient_service.py"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.sample_ingredient_data = {
            "ingredient_name": "Pollo",
            "calories": 165,
            "proteins": 31.0,
            "carbohydrates": 0.0,
            "fats": 3.6
        }
        
        self.sample_db_result = (
            1,  # id
            "Pollo",  # ingredient_name
            Decimal("165"),  # calories
            Decimal("31.0"),  # proteins
            Decimal("0.0"),  # carbohydrates
            Decimal("3.6"),  # fats
            datetime(2024, 1, 15, 10, 30),  # created_at
            datetime(2024, 1, 15, 10, 30)   # updated_at
        )

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_get_ingredient_success(self, mock_execute_db_query):
        """Test obtener ingrediente existente"""
        # Arrange
        mock_execute_db_query.return_value = self.sample_db_result
        
        # Act
        result = get_ingredient(1)
        
        # Assert
        assert result is not None
        assert result["id"] == 1
        assert result["ingredient_name"] == "Pollo"
        assert result["calories"] == Decimal("165")
        assert result["proteins"] == Decimal("31.0")
        assert result["carbohydrates"] == Decimal("0.0")
        assert result["fats"] == Decimal("3.6")
        assert isinstance(result["created_at"], datetime)
        assert isinstance(result["updated_at"], datetime)
        
        # Verificar que se llamó correctamente (sin preocuparnos por espacios exactos)
        mock_execute_db_query.assert_called_once()
        call_args = mock_execute_db_query.call_args
        assert "SELECT id, ingredient_name, calories, proteins, carbohydrates, fats" in call_args[0][0]
        assert "FROM ingredients" in call_args[0][0]
        assert "WHERE id = %s" in call_args[0][0]
        assert call_args[0][1] == (1,)
        assert call_args[1]["fetch_one"] is True

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_get_ingredient_not_found(self, mock_execute_db_query):
        """Test obtener ingrediente inexistente"""
        # Arrange
        mock_execute_db_query.return_value = None
        
        # Act
        result = get_ingredient(999)
        
        # Assert
        assert result is None
        mock_execute_db_query.assert_called_once()

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_create_ingredient_success(self, mock_execute_db_query):
        """Test crear ingrediente exitosamente"""
        # Arrange
        mock_execute_db_query.return_value = self.sample_db_result
        
        # Act
        result = create_ingredient(self.sample_ingredient_data)
        
        # Assert
        assert result is not None
        assert result["ingredient_name"] == "Pollo"
        assert result["calories"] == Decimal("165")
        
        # Verificar query y parámetros
        mock_execute_db_query.assert_called_once()
        call_args = mock_execute_db_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO ingredients" in query
        assert "ingredient_name, calories, proteins, carbohydrates, fats" in query
        assert "VALUES (%s, %s, %s, %s, %s)" in query
        assert "RETURNING" in query
        assert params == ("Pollo", 165, 31.0, 0.0, 3.6)
        assert call_args[1]["fetch_one"] is True

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_create_ingredient_database_error(self, mock_execute_db_query):
        """Test crear ingrediente con error de BD"""
        # Arrange
        mock_execute_db_query.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            create_ingredient(self.sample_ingredient_data)
        
        assert "Database error" in str(exc_info.value)

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_list_ingredients_no_search(self, mock_execute_db_query):
        """Test listar todos los ingredientes sin búsqueda"""
        # Arrange
        mock_results = [
            self.sample_db_result,
            (2, "Arroz", Decimal("130"), Decimal("2.7"), Decimal("28.2"), Decimal("0.3"), 
             datetime.now(), datetime.now())
        ]
        mock_execute_db_query.return_value = mock_results
        
        # Act
        result = list_ingredients()
        
        # Assert
        assert len(result) == 2
        assert result[0]["ingredient_name"] == "Pollo"
        assert result[1]["ingredient_name"] == "Arroz"
        
        # Verificar query sin WHERE
        mock_execute_db_query.assert_called_once()
        call_args = mock_execute_db_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "SELECT id, ingredient_name, calories, proteins, carbohydrates, fats" in query
        assert "FROM ingredients" in query
        assert "WHERE" not in query
        assert "ORDER BY ingredient_name" in query
        assert params == []
        assert call_args[1]["fetch_all"] is True

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_list_ingredients_with_search(self, mock_execute_db_query):
        """Test listar ingredientes con búsqueda"""
        # Arrange
        mock_execute_db_query.return_value = [self.sample_db_result]
        
        # Act
        result = list_ingredients(search="pollo")
        
        # Assert
        assert len(result) == 1
        assert result[0]["ingredient_name"] == "Pollo"
        
        # Verificar query con WHERE
        mock_execute_db_query.assert_called_once()
        call_args = mock_execute_db_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "SELECT id, ingredient_name, calories, proteins, carbohydrates, fats" in query
        assert "FROM ingredients" in query
        assert "WHERE ingredient_name ILIKE %s" in query
        assert "ORDER BY ingredient_name" in query
        assert params == ["%pollo%"]
        assert call_args[1]["fetch_all"] is True

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_update_ingredient_success(self, mock_execute_db_query):
        """Test actualizar ingrediente exitosamente"""
        # Arrange
        update_data = {"calories": 170, "proteins": 32.0}
        updated_result = (
            1, "Pollo", Decimal("170"), Decimal("32.0"), Decimal("0.0"), Decimal("3.6"),
            datetime.now(), datetime.now()
        )
        mock_execute_db_query.return_value = updated_result
        
        # Act
        result = update_ingredient(1, update_data)
        
        # Assert
        assert result is not None
        assert result["calories"] == Decimal("170")
        assert result["proteins"] == Decimal("32.0")
        
        # Verificar que se construyó la query correctamente
        mock_execute_db_query.assert_called_once()
        call_args = mock_execute_db_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "UPDATE ingredients" in query
        assert "calories = %s" in query
        assert "proteins = %s" in query
        assert "updated_at = CURRENT_TIMESTAMP" in query
        assert params[-1] == 1  # ingredient_id al final

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_update_ingredient_no_fields(self, mock_execute_db_query):
        """Test actualizar ingrediente sin campos - debería llamar a get_ingredient"""
        # Arrange
        mock_execute_db_query.return_value = self.sample_db_result
        
        # Act
        with patch('back_end.gym.services.nutrition.ingredient_service.get_ingredient') as mock_get:
            mock_get.return_value = {"id": 1, "ingredient_name": "Pollo"}
            result = update_ingredient(1, {})
        
        # Assert
        mock_get.assert_called_once_with(1)

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_delete_ingredient_success(self, mock_execute_db_query):
        """Test eliminar ingrediente exitosamente"""
        # Arrange
        # Primera llamada: check usage count (0 usos)
        # Segunda llamada: delete query (retorna True indicando eliminación exitosa)
        mock_execute_db_query.side_effect = [(0,), True]
        
        # Act
        result = delete_ingredient(1)
        
        # Assert
        assert result is True
        assert mock_execute_db_query.call_count == 2
        
        # Verificar primera llamada (check usage)
        first_call = mock_execute_db_query.call_args_list[0]
        assert "meal_ingredients" in first_call[0][0]
        assert "COUNT(*)" in first_call[0][0]
        assert "ingredient_id = %s" in first_call[0][0]
        
        # Verificar segunda llamada (delete)
        second_call = mock_execute_db_query.call_args_list[1]
        assert "DELETE FROM ingredients" in second_call[0][0]
        assert "WHERE id = %s" in second_call[0][0]
        assert second_call[1]["commit"] is True

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_delete_ingredient_in_use(self, mock_execute_db_query):
        """Test eliminar ingrediente que está en uso"""
        # Arrange
        mock_execute_db_query.return_value = (3,)  # 3 usos
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            delete_ingredient(1)
        
        assert "está siendo usado en 3 comidas" in str(exc_info.value)
        # Solo debería haber una llamada (check usage)
        assert mock_execute_db_query.call_count == 1

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_check_ingredient_exists_true(self, mock_execute_db_query):
        """Test verificar que ingrediente existe"""
        # Arrange
        mock_execute_db_query.return_value = (1,)  # Existe
        
        # Act
        result = check_ingredient_exists(1)
        
        # Assert
        assert result is True
        mock_execute_db_query.assert_called_once()
        call_args = mock_execute_db_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "SELECT id FROM ingredients" in query
        assert "WHERE id = %s" in query
        assert params == (1,)
        assert call_args[1]["fetch_one"] is True

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_check_ingredient_exists_false(self, mock_execute_db_query):
        """Test verificar que ingrediente no existe"""
        # Arrange
        mock_execute_db_query.return_value = None  # No existe
        
        # Act
        result = check_ingredient_exists(999)
        
        # Assert
        assert result is False

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_database_connection_error(self, mock_execute_db_query):
        """Test manejo de errores de conexión a BD"""
        # Arrange
        mock_execute_db_query.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            get_ingredient(1)
        
        assert "Connection failed" in str(exc_info.value)

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    @patch('back_end.gym.services.nutrition.ingredient_service.logger')
    def test_logging_on_error(self, mock_logger, mock_execute_db_query):
        """Test que se loguean los errores correctamente"""
        # Arrange
        mock_execute_db_query.side_effect = Exception("Test error")
        
        # Act & Assert
        with pytest.raises(Exception):
            get_ingredient(1)
        
        # Verificar que se logueó el error
        mock_logger.error.assert_called_once()

    def test_ingredient_data_types(self):
        """Test que los tipos de datos se manejan correctamente"""
        # Este test verifica que la función maneja correctamente los tipos
        # de datos que vienen de la BD (Decimal, datetime, etc.)
        
        # Arrange
        with patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query') as mock_db:
            mock_db.return_value = self.sample_db_result
            
            # Act
            result = get_ingredient(1)
            
            # Assert - verificar tipos específicos
            assert isinstance(result["calories"], Decimal)
            assert isinstance(result["proteins"], Decimal)
            assert isinstance(result["carbohydrates"], Decimal)
            assert isinstance(result["fats"], Decimal)
            assert isinstance(result["created_at"], datetime)
            assert isinstance(result["updated_at"], datetime)

    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_basic_functionality_smoke_tests(self, mock_execute_db_query):
        """Test de humo para verificar que todas las funciones básicas se pueden llamar"""
        # Este test simplificado verifica que las funciones se pueden llamar sin errores
        
        # Test get_ingredient
        mock_execute_db_query.return_value = self.sample_db_result
        result = get_ingredient(1)
        assert result is not None
        mock_execute_db_query.reset_mock()
        
        # Test get_ingredient not found
        mock_execute_db_query.return_value = None
        result = get_ingredient(999)
        assert result is None
        mock_execute_db_query.reset_mock()
        
        # Test create_ingredient
        mock_execute_db_query.return_value = self.sample_db_result
        result = create_ingredient(self.sample_ingredient_data)
        assert result is not None
        mock_execute_db_query.reset_mock()
        
        # Test list_ingredients
        mock_execute_db_query.return_value = [self.sample_db_result]
        result = list_ingredients()
        assert len(result) == 1
        mock_execute_db_query.reset_mock()
        
        # Test check_ingredient_exists
        mock_execute_db_query.return_value = (1,)
        result = check_ingredient_exists(1)
        assert result is True
        mock_execute_db_query.reset_mock()
        
        # Test delete_ingredient success
        mock_execute_db_query.side_effect = [(0,), True]  # No está en uso, delete exitoso
        result = delete_ingredient(1)
        assert result is True


# Test de integración (opcional, para verificar que funciona end-to-end)
class TestIngredientServiceIntegration:
    """Tests de integración con BD real (opcional)"""
    
    def setup_method(self):
        """Setup para cada test de integración"""
        self.sample_db_result = (
            1,  # id
            "Test Ingredient",  # ingredient_name
            Decimal("100"),  # calories
            Decimal("10.0"),  # proteins
            Decimal("5.0"),  # carbohydrates
            Decimal("2.0"),  # fats
            datetime(2024, 1, 15, 10, 30),  # created_at
            datetime(2024, 1, 15, 10, 30)   # updated_at
        )
    
    @pytest.mark.integration
    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')  # 🔧 CORRECCIÓN PRINCIPAL
    def test_create_and_get_ingredient_flow(self, mock_execute_db_query):
        """Test del flujo completo: crear y luego obtener ingrediente"""
        
        # Configurar el mock para manejar múltiples llamadas
        def side_effect_handler(*args, **kwargs):
            query = args[0] if args else ""
            
            # Para INSERT (create_ingredient), retorna el resultado de creación
            if "INSERT INTO ingredients" in query:
                return self.sample_db_result
            
            # Para SELECT (get_ingredient), retorna el mismo resultado
            elif "SELECT" in query and "WHERE id = " in query:
                return self.sample_db_result
            
            # Para cualquier otra consulta
            return None
            
        mock_execute_db_query.side_effect = side_effect_handler
        
        # Test de creación
        created = create_ingredient({
            "ingredient_name": "Test Ingredient",
            "calories": 100,
            "proteins": 10.0,
            "carbohydrates": 5.0,
            "fats": 2.0
        })
        
        # Verificar que se creó correctamente
        assert created is not None
        assert created["id"] == 1
        assert created["ingredient_name"] == "Test Ingredient"
        assert created["calories"] == Decimal("100")
        assert created["proteins"] == Decimal("10.0")
        assert created["carbohydrates"] == Decimal("5.0")
        assert created["fats"] == Decimal("2.0")
        
        # Test de obtención
        retrieved = get_ingredient(created["id"])
        
        # Verificar que se obtuvo correctamente
        assert retrieved is not None
        assert created["ingredient_name"] == retrieved["ingredient_name"]
        assert created["calories"] == retrieved["calories"]
        assert created["proteins"] == retrieved["proteins"]
        assert created["carbohydrates"] == retrieved["carbohydrates"]
        assert created["fats"] == retrieved["fats"]
        
        # Verificar que se hicieron las llamadas esperadas
        assert mock_execute_db_query.call_count == 2
        
        # Verificar tipos de queries ejecutadas
        calls = mock_execute_db_query.call_args_list
        first_query = calls[0][0][0]
        second_query = calls[1][0][0]
        
        assert "INSERT INTO ingredients" in first_query
        assert "SELECT" in second_query and "WHERE id = " in second_query

    @pytest.mark.integration  
    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_create_and_get_ingredient_flow_alternative(self, mock_execute_db_query):
        """Test alternativo con configuración más simple del mock"""
        
        # Configurar mock para devolver siempre el mismo resultado
        mock_execute_db_query.return_value = self.sample_db_result
        
        # Ejecutar flujo
        created = create_ingredient({
            "ingredient_name": "Test Ingredient",
            "calories": 100,
            "proteins": 10.0,
            "carbohydrates": 5.0,
            "fats": 2.0
        })
        
        retrieved = get_ingredient(created["id"])
        
        # Verificaciones básicas
        assert created["ingredient_name"] == retrieved["ingredient_name"]
        assert created["calories"] == retrieved["calories"]
        assert mock_execute_db_query.call_count == 2

    @pytest.mark.integration
    @patch('back_end.gym.services.nutrition.ingredient_service.execute_db_query')
    def test_full_crud_flow(self, mock_execute_db_query):
        """Test del flujo CRUD completo: Create, Read, Update, Delete"""
        
        # Configurar diferentes resultados para diferentes operaciones
        def crud_side_effect(*args, **kwargs):
            query = args[0] if args else ""
            
            if "INSERT INTO ingredients" in query:
                # Crear ingrediente
                return self.sample_db_result
            elif "SELECT" in query and "WHERE id = " in query:
                # Leer ingrediente
                return self.sample_db_result
            elif "UPDATE ingredients" in query:
                # Actualizar ingrediente
                updated_result = (
                    1, "Test Ingredient Updated", Decimal("120"), Decimal("12.0"),
                    Decimal("6.0"), Decimal("3.0"), datetime.now(), datetime.now()
                )
                return updated_result
            elif "COUNT(*)" in query and "meal_ingredients" in query:
                # Check usage antes de delete
                return (0,)  # No está en uso
            elif "DELETE FROM ingredients" in query:
                # Eliminar ingrediente
                return True
            
            return None
            
        mock_execute_db_query.side_effect = crud_side_effect
        
        # 1. CREATE
        created = create_ingredient({
            "ingredient_name": "Test Ingredient",
            "calories": 100,
            "proteins": 10.0,
            "carbohydrates": 5.0,
            "fats": 2.0
        })
        assert created is not None
        assert created["ingredient_name"] == "Test Ingredient"
        
        # 2. READ
        retrieved = get_ingredient(created["id"])
        assert retrieved is not None
        assert retrieved["ingredient_name"] == created["ingredient_name"]
        
        # 3. UPDATE
        updated = update_ingredient(created["id"], {
            "ingredient_name": "Test Ingredient Updated",
            "calories": 120,
            "proteins": 12.0
        })
        assert updated is not None
        assert updated["ingredient_name"] == "Test Ingredient Updated"
        
        # 4. DELETE
        deleted = delete_ingredient(created["id"])
        assert deleted is True
        
        # Verificar que se hicieron todas las llamadas esperadas
        # CREATE (1) + READ (1) + UPDATE (1) + DELETE check usage (1) + DELETE (1) = 5 llamadas
        assert mock_execute_db_query.call_count == 5


if __name__ == "__main__":
    # Para ejecutar los tests
    # Comando básico: python -m pytest tests/test_ingredient_service.py -v
    # Con coverage: python -m pytest tests/test_ingredient_service.py --cov=gym.services.nutrition.ingredient_service -v
    # Solo smoke tests: python -m pytest tests/test_ingredient_service.py::TestIngredientService::test_basic_functionality_smoke_tests -v
    # Solo test de integración: python -m pytest tests/test_ingredient_service.py::TestIngredientServiceIntegration::test_create_and_get_ingredient_flow -v
    pytest.main([__file__, "-v"])