import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime

from back_end.gym.app_fastapi import app
from back_end.gym.middlewares import get_current_user


class TestIngredients:
    """Test suite for ingredients endpoints"""

    @pytest.fixture
    def auth_user(self):
        return {"id": 1, "email": "test@example.com"}

    @pytest.fixture
    def mock_auth(self, auth_user):
        app.dependency_overrides[get_current_user] = lambda: auth_user
        yield
        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_ingredient(self):
        return {
            "ingredient_name": "Pollo",
            "calories": 165,
            "proteins": 31.0,
            "carbohydrates": 0,
            "fats": 3.6
        }

    def test_create_ingredient(self, test_client: TestClient, mock_auth, sample_ingredient):
        """Test creating a new ingredient"""
        with patch('back_end.gym.services.db_utils.execute_db_query') as mock_db:
            mock_db.return_value = (
                1, "Pollo", 165, 31.0, 0, 3.6, 
                datetime.now(), datetime.now()
            )
            
            response = test_client.post(
                "/api/nutrition/ingredients",
                json=sample_ingredient
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["ingredient_name"] == "Pollo"
            assert data["calories"] == 165

    def test_create_ingredient_duplicate(self, test_client: TestClient, mock_auth, sample_ingredient):
        """Test creating duplicate ingredient"""
        with patch('back_end.gym.services.db_utils.execute_db_query') as mock_db:
            mock_db.side_effect = Exception("duplicate key")
            
            response = test_client.post(
                "/api/nutrition/ingredients",
                json=sample_ingredient
            )
            
            assert response.status_code == 409
            assert "ya existe" in response.json()["detail"]

    def test_list_ingredients(self, test_client: TestClient, mock_auth):
        """Test listing all ingredients"""
        mock_ingredients = [
            {"id": 1, "ingredient_name": "Pollo", "calories": Decimal("165"), 
             "proteins": Decimal("31.0"), "carbohydrates": Decimal("0"), 
             "fats": Decimal("3.6"), "created_at": datetime.now(), 
             "updated_at": datetime.now()},
            {"id": 2, "ingredient_name": "Arroz", "calories": Decimal("130"), 
             "proteins": Decimal("2.7"), "carbohydrates": Decimal("28.2"), 
             "fats": Decimal("0.3"), "created_at": datetime.now(), 
             "updated_at": datetime.now()}
        ]
        
        with patch('back_end.gym.services.nutrition.ingredient_service.list_ingredients') as mock_list:
            mock_list.return_value = mock_ingredients
            
            response = test_client.get("/api/nutrition/ingredients")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["ingredients"]) == 2
            assert data["ingredients"][0]["calories"] == 165.0  # Decimal converted to float

    def test_list_ingredients_with_search(self, test_client: TestClient, mock_auth):
        """Test searching ingredients"""
        with patch('back_end.gym.services.nutrition.ingredient_service.list_ingredients') as mock_list:
            mock_list.return_value = []
            
            response = test_client.get("/api/nutrition/ingredients?search=pollo")
            
            assert response.status_code == 200
            mock_list.assert_called_with("pollo")

    def test_get_ingredient_by_id(self, test_client: TestClient, mock_auth):
        """Test getting specific ingredient"""
        with patch('back_end.gym.services.nutrition.ingredient_service.get_ingredient') as mock_get:
            mock_get.return_value = {
                "id": 1, "ingredient_name": "Pollo", "calories": 165,
                "proteins": 31.0, "carbohydrates": 0, "fats": 3.6
            }
            
            response = test_client.get("/api/nutrition/ingredients/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["ingredient_name"] == "Pollo"

    def test_get_ingredient_not_found(self, test_client: TestClient, mock_auth):
        """Test getting non-existent ingredient"""
        with patch('back_end.gym.services.nutrition.ingredient_service.get_ingredient') as mock_get:
            mock_get.return_value = None
            
            response = test_client.get("/api/nutrition/ingredients/999")
            
            assert response.status_code == 404

    def test_update_ingredient(self, test_client: TestClient, mock_auth):
        """Test updating ingredient"""
        update_data = {"calories": 170, "proteins": 32.0}
        
        with patch('back_end.gym.services.nutrition.ingredient_service.check_ingredient_exists') as mock_exists, \
             patch('back_end.gym.services.nutrition.ingredient_service.update_ingredient') as mock_update:
            mock_exists.return_value = True
            mock_update.return_value = {
                "id": 1, "ingredient_name": "Pollo", "calories": 170,
                "proteins": 32.0, "carbohydrates": 0, "fats": 3.6
            }
            
            response = test_client.put(
                "/api/nutrition/ingredients/1",
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["calories"] == 170
            assert data["proteins"] == 32.0

    def test_delete_ingredient(self, test_client: TestClient, mock_auth):
        """Test deleting ingredient"""
        with patch('back_end.gym.services.nutrition.ingredient_service.check_ingredient_exists') as mock_exists, \
             patch('back_end.gym.services.nutrition.ingredient_service.delete_ingredient') as mock_delete:
            mock_exists.return_value = True
            mock_delete.return_value = True
            
            response = test_client.delete("/api/nutrition/ingredients/1")
            
            assert response.status_code == 204

    def test_delete_ingredient_in_use(self, test_client: TestClient, mock_auth):
        """Test deleting ingredient that's being used"""
        with patch('back_end.gym.services.nutrition.ingredient_service.check_ingredient_exists') as mock_exists, \
             patch('back_end.gym.services.nutrition.ingredient_service.delete_ingredient') as mock_delete:
            mock_exists.return_value = True
            mock_delete.side_effect = ValueError("No se puede eliminar el ingrediente porque está siendo usado en 3 comidas")
            
            response = test_client.delete("/api/nutrition/ingredients/1")
            
            assert response.status_code == 409
            assert "está siendo usado" in response.json()["detail"]