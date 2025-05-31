import pytest
from unittest.mock import patch, MagicMock, ANY 
import time 
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException 
from fastapi.testclient import TestClient

from back_end.gym.app_fastapi import app
from back_end.gym.middlewares import get_current_user


class TestIngredients:
    """Test suite for ingredients endpoints"""

    @pytest.fixture
    def auth_user(self):
        return {
            "id": 1, "email": "test@example.com", "google_id": "google_test_id_ingredients",
            "display_name": "Test User Ingredients" 
        }

    @pytest.fixture
    def auth_user_payload(self, auth_user: dict) -> dict:
        return {
            "sub": str(auth_user["id"]), "email": auth_user["email"],
            "name": auth_user.get("display_name", "Test User"), "type": "access", 
            "exp": time.time() + 3600, "user_id_internal": auth_user["id"] 
        }

    @pytest.fixture
    def mock_auth(self, auth_user: dict, auth_user_payload: dict):
        with patch('back_end.gym.services.jwt_service.verify_token', return_value=auth_user_payload) as mock_verify_token:
            app.dependency_overrides[get_current_user] = lambda: auth_user
            yield mock_verify_token 
            app.dependency_overrides.clear()

    @pytest.fixture
    def sample_ingredient_payload(self):
        return {
            "ingredient_name": "Pollo", "calories": 165, "proteins": 31.0,
            "carbohydrates": 0.0, "fats": 3.6
        }

    @pytest.fixture
    def mock_ingredient_from_db(self, sample_ingredient_payload, auth_user):
        now = datetime.now()
        return {
            "id": 1, **sample_ingredient_payload, "user_id": auth_user["id"],
            "calories": Decimal(str(sample_ingredient_payload["calories"])),
            "proteins": Decimal(str(sample_ingredient_payload["proteins"])),
            "carbohydrates": Decimal(str(sample_ingredient_payload["carbohydrates"])),
            "fats": Decimal(str(sample_ingredient_payload["fats"])),
            "created_at": now, "updated_at": now
        }

    # !!! IMPORTANTE: Los siguientes 'patch' asumen que en tu archivo
    # back_end/gym/routes/nutrition/ingredients.py importas las funciones del servicio
    # con estos nombres: create_ingredient, list_ingredients, etc. 
    # Si usas otros nombres o alias, DEBES CAMBIARLOS aquí. !!!

    def test_create_ingredient(self, test_client: TestClient, mock_auth, sample_ingredient_payload, mock_ingredient_from_db, auth_user):
        with patch('back_end.gym.routes.nutrition.ingredients.create_ingredient', return_value=mock_ingredient_from_db) as mock_create_service:
            response = test_client.post(
                "/api/nutrition/ingredients",
                json=sample_ingredient_payload,
                headers={"Authorization": "Bearer fake.jwt.token"}
            )
            assert response.status_code == 201, f"Response: {response.text}"
            data = response.json()
            assert data["ingredient_name"] == sample_ingredient_payload["ingredient_name"]
            # Asumimos que la ruta llama al servicio así:
            # servicio.create_ingredient(db_session=db, ingredient_data=payload, user_id=user.id)
            mock_create_service.assert_called_once_with(db_session=ANY, ingredient_data=sample_ingredient_payload, user_id=auth_user["id"])

    def test_create_ingredient_duplicate(self, test_client: TestClient, mock_auth, sample_ingredient_payload, auth_user):
        with patch('back_end.gym.routes.nutrition.ingredients.create_ingredient') as mock_create_service:
            # Para que el test pase esperando 409, la RUTA debe convertir el error del servicio en HTTPException(409)
            # Aquí simulamos que el servicio ya lanza la HTTPException que la ruta podría estar simplemente relanzando.
            mock_create_service.side_effect = HTTPException(status_code=409, detail="El ingrediente 'Pollo' ya existe.")
            
            response = test_client.post(
                "/api/nutrition/ingredients",
                json=sample_ingredient_payload,
                headers={"Authorization": "Bearer fake.jwt.token"}
            )
            assert response.status_code == 409, f"Response: {response.text}"
            assert "ya existe" in response.json()["detail"].lower()
            mock_create_service.assert_called_once_with(db_session=ANY, ingredient_data=sample_ingredient_payload, user_id=auth_user["id"])

    def test_list_ingredients(self, test_client: TestClient, mock_auth, mock_ingredient_from_db, auth_user):
        mock_ingredients_list = [mock_ingredient_from_db]
        with patch('back_end.gym.routes.nutrition.ingredients.list_ingredients', return_value=mock_ingredients_list) as mock_list_service:
            response = test_client.get("/api/nutrition/ingredients", headers={"Authorization": "Bearer fake.jwt.token"})
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert len(data["ingredients"]) == 1
            # Asumimos que la ruta llama al servicio así:
            # servicio.list_ingredients(db_session=db, user_id=user.id, search_term=None)
            mock_list_service.assert_called_once_with(db_session=ANY, user_id=auth_user["id"], search_term=None)

    def test_list_ingredients_with_search(self, test_client: TestClient, mock_auth, auth_user):
        with patch('back_end.gym.routes.nutrition.ingredients.list_ingredients', return_value=[]) as mock_list_service:
            response = test_client.get("/api/nutrition/ingredients?search=pollo", headers={"Authorization": "Bearer fake.jwt.token"})
            assert response.status_code == 200, f"Response: {response.text}"
            # Asumimos que la ruta llama al servicio así:
            # servicio.list_ingredients(db_session=db, user_id=user.id, search_term="pollo")
            mock_list_service.assert_called_once_with(db_session=ANY, user_id=auth_user["id"], search_term="pollo")

    def test_get_ingredient_by_id(self, test_client: TestClient, mock_auth, mock_ingredient_from_db, auth_user):
        with patch('back_end.gym.routes.nutrition.ingredients.get_ingredient_by_id', return_value=mock_ingredient_from_db) as mock_get_service:
            response = test_client.get(f"/api/nutrition/ingredients/{mock_ingredient_from_db['id']}", headers={"Authorization": "Bearer fake.jwt.token"})
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert data["id"] == mock_ingredient_from_db["id"]
            # Asumimos que la ruta llama al servicio así:
            # servicio.get_ingredient_by_id(db_session=db, ingredient_id=id, user_id=user.id)
            mock_get_service.assert_called_once_with(db_session=ANY, ingredient_id=mock_ingredient_from_db['id'], user_id=auth_user["id"])

    def test_get_ingredient_not_found(self, test_client: TestClient, mock_auth, auth_user):
        with patch('back_end.gym.routes.nutrition.ingredients.get_ingredient_by_id', return_value=None) as mock_get_service:
            response = test_client.get("/api/nutrition/ingredients/999", headers={"Authorization": "Bearer fake.jwt.token"})
            assert response.status_code == 404, f"Response: {response.text}"
            mock_get_service.assert_called_once_with(db_session=ANY, ingredient_id=999, user_id=auth_user["id"])

    def test_update_ingredient(self, test_client: TestClient, mock_auth, sample_ingredient_payload, auth_user):
        ingredient_id_to_update = 1
        update_data_payload = {"calories": 170, "proteins": 32.0} 
        updated_ingredient_from_service = {
            "id": ingredient_id_to_update, "ingredient_name": sample_ingredient_payload["ingredient_name"],
            "calories": Decimal("170"), "proteins": Decimal("32.0"), 
            "carbohydrates": Decimal(str(sample_ingredient_payload["carbohydrates"])), 
            "fats": Decimal(str(sample_ingredient_payload["fats"])),
            "created_at": datetime.now(), "updated_at": datetime.now(), "user_id": auth_user["id"]
        }
        
        # La ruta probablemente primero verifica la existencia y pertenencia del ingrediente.
        # Y luego llama a la función de actualización. AMBAS deben ser parcheadas si tocan BD.
        with patch('back_end.gym.routes.nutrition.ingredients.get_ingredient_by_id', return_value=updated_ingredient_from_service) as mock_check_exists, \
             patch('back_end.gym.routes.nutrition.ingredients.update_ingredient', return_value=updated_ingredient_from_service) as mock_update_service:
            
            response = test_client.put(
                f"/api/nutrition/ingredients/{ingredient_id_to_update}",
                json=update_data_payload,
                headers={"Authorization": "Bearer fake.jwt.token"}
            )
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert data["calories"] == 170.0
            mock_check_exists.assert_called_once_with(db_session=ANY, ingredient_id=ingredient_id_to_update, user_id=auth_user["id"])
            # Asumimos que la ruta pasa el objeto ingrediente_a_actualizar (obtenido de get_ingredient_by_id)
            # y los datos de actualización al servicio de update. Ajusta si es diferente.
            mock_update_service.assert_called_once_with(db_session=ANY, ingredient_to_update=ANY, ingredient_update_data=update_data_payload)


    def test_delete_ingredient(self, test_client: TestClient, mock_auth, auth_user):
        ingredient_id_to_delete = 1
        # La ruta probablemente primero verifica la existencia y pertenencia.
        with patch('back_end.gym.routes.nutrition.ingredients.get_ingredient_by_id', return_value={"id": ingredient_id_to_delete, "user_id": auth_user["id"]}) as mock_check_exists, \
             patch('back_end.gym.routes.nutrition.ingredients.delete_ingredient', return_value=True) as mock_delete_service:
            
            response = test_client.delete(f"/api/nutrition/ingredients/{ingredient_id_to_delete}", headers={"Authorization": "Bearer fake.jwt.token"})
            assert response.status_code == 204, f"Response: {response.text}" 
            mock_check_exists.assert_called_once_with(db_session=ANY, ingredient_id=ingredient_id_to_delete, user_id=auth_user["id"])
            # Asumimos que la ruta pasa el objeto ingrediente_a_eliminar al servicio de delete.
            mock_delete_service.assert_called_once_with(db_session=ANY, ingredient_to_delete=ANY, user_id=auth_user["id"])


    def test_delete_ingredient_in_use(self, test_client: TestClient, mock_auth, auth_user):
        ingredient_id_to_delete = 1
        with patch('back_end.gym.routes.nutrition.ingredients.get_ingredient_by_id', return_value={"id": ingredient_id_to_delete, "user_id": auth_user["id"]}) as mock_check_exists, \
             patch('back_end.gym.routes.nutrition.ingredients.delete_ingredient') as mock_delete_service:
            # La RUTA debe convertir el error del servicio en HTTPException(409)
            mock_delete_service.side_effect = HTTPException(status_code=409, detail="No se puede eliminar el ingrediente porque está siendo usado")
            
            response = test_client.delete(f"/api/nutrition/ingredients/{ingredient_id_to_delete}", headers={"Authorization": "Bearer fake.jwt.token"})
            assert response.status_code == 409, f"Response: {response.text}"
            assert "está siendo usado" in response.json()["detail"].lower()
            mock_check_exists.assert_called_once_with(db_session=ANY, ingredient_id=ingredient_id_to_delete, user_id=auth_user["id"])
            mock_delete_service.assert_called_once_with(db_session=ANY, ingredient_to_delete=ANY, user_id=auth_user["id"])

    def test_list_ingredients_unauthenticated(self, test_client: TestClient):
        app.dependency_overrides.clear()
        response = test_client.get("/api/nutrition/ingredients", follow_redirects=False)
        assert response.status_code == 307
        assert "/login" in response.headers.get("Location", "")

    def test_create_ingredient_unauthenticated(self, test_client: TestClient, sample_ingredient_payload):
        app.dependency_overrides.clear()
        response = test_client.post(
            "/api/nutrition/ingredients",
            json=sample_ingredient_payload,
            follow_redirects=False
        )
        assert response.status_code == 307
        assert "/login" in response.headers.get("Location", "")
