import pytest
from unittest.mock import patch, MagicMock
import time # Necesario para el payload del JWT
from fastapi.testclient import TestClient

from back_end.gym.app_fastapi import app
from back_end.gym.middlewares import get_current_user


class TestNutritionCalculator:
    """Test suite for nutrition calculator endpoints"""

    @pytest.fixture
    def auth_user(self):
        """Datos para el usuario mock."""
        return {
            "id": 1, 
            "email": "test@example.com",
            "google_id": "google_test_id_nutrition", 
            "display_name": "Test User Nutrition" 
        }

    @pytest.fixture
    def auth_user_payload(self, auth_user: dict) -> dict:
        """
        Prepara un payload JWT simulado que la función 'verify_token' (mockeada) 
        debería devolver.
        """
        return {
            "sub": str(auth_user["id"]), 
            "email": auth_user["email"],
            "name": auth_user.get("display_name", "Test User"), 
            "type": "access", 
            "exp": time.time() + 3600, 
            "user_id_internal": auth_user["id"] 
        }

    @pytest.fixture
    def mock_auth(self, auth_user: dict, auth_user_payload: dict):
        """
        Mocks authentication.
        1. Patches 'verify_token' (called by middleware) to return a JWT payload.
        2. Overrides 'get_current_user' (route dependency) to return the full user dict.
        """
        with patch('back_end.gym.services.jwt_service.verify_token', return_value=auth_user_payload) as mock_verify_token_in_service:
            app.dependency_overrides[get_current_user] = lambda: auth_user
            yield mock_verify_token_in_service 
            app.dependency_overrides.clear()

    @pytest.fixture
    def macro_calculator_data(self):
        return {
            "units": "metric",
            "formula": "mifflin_st_jeor",
            "gender": "male",
            "age": 30,
            "height": 180,
            "weight": 80,
            "body_fat_percentage": 15,
            "activity_level": "moderate",
            "goal": "maintain",
            "goal_intensity": "normal",
            "macro_distribution": {
                "protein": 30,
                "carbs": 40,
                "fat": 30
            }
        }

    def test_calculate_macros_success(self, test_client: TestClient, mock_auth, macro_calculator_data):
        """Test successful macro calculation"""
        response = test_client.post(
            "/api/nutrition/calculator/calculate-macros", # URL sigue siendo sospechosa de 404
            json=macro_calculator_data,
            headers={"Authorization": "Bearer fake.jwt.token"} 
        )
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        assert data["bmr"] > 0
        assert data["tdee"] > 0
        assert data["bmi"] > 0
        assert data["daily_calories"] > 0
        assert data["proteins_grams"] > 0
        assert data["carbs_grams"] > 0
        assert data["fats_grams"] > 0

    def test_calculate_macros_different_formulas(self, test_client: TestClient, mock_auth, macro_calculator_data):
        """Test calculation with different formulas"""
        formulas = ["mifflin_st_jeor", "harris_benedict", "katch_mcardle", "who"]
        
        for formula in formulas:
            data = macro_calculator_data.copy()
            data["formula"] = formula
            
            response = test_client.post(
                "/api/nutrition/calculator/calculate-macros", # URL sigue siendo sospechosa de 404
                json=data,
                headers={"Authorization": "Bearer fake.jwt.token"} 
            )
            
            assert response.status_code == 200, f"Response: {response.text}"
            result = response.json()
            assert result["formula"] == formula
            assert result["bmr"] > 0

    def test_calculate_macros_imperial_units(self, test_client: TestClient, mock_auth):
        """Test calculation with imperial units"""
        data = {
            "units": "imperial",
            "formula": "mifflin_st_jeor",
            "gender": "female",
            "age": 25,
            "height": 65,  # inches
            "weight": 140,  # pounds
            "activity_level": "active",
            "goal": "lose",
            "goal_intensity": "normal",
            "macro_distribution": {
                "protein": 35,
                "carbs": 35,
                "fat": 30
            }
        }
        
        response = test_client.post(
            "/api/nutrition/calculator/calculate-macros", # URL sigue siendo sospechosa de 404
            json=data,
            headers={"Authorization": "Bearer fake.jwt.token"} 
        )
        
        assert response.status_code == 200, f"Response: {response.text}"
        result = response.json()
        assert result["units"] == "imperial"
        assert result["daily_calories"] < result["tdee"]  # Deficit for weight loss

    def test_get_nutrition_profile(self, test_client: TestClient, mock_auth, auth_user): 
        """Test getting existing nutrition profile. Este SÍ requiere autenticación."""
        profile_data_from_db = { 
            "user_id": auth_user["id"], 
            "formula": "mifflin_st_jeor",
            "sex": "male", 
            "age": 30,
            "height": 180.0, 
            "weight": 80.0,
            "body_fat_percentage": 15.0,
            "activity_level": "moderate",
            "goal": "maintain",
            "goal_intensity": "normal",
            "units": "metric",
            "bmr": 1800.0,
            "tdee": 2790.0,
            "bmi": 24.7,
            "daily_calories": 2790.0,
            "proteins_grams": 209.0,
            "carbs_grams": 279.0,
            "fats_grams": 93.0,
            "created_at": "2024-01-01T10:00:00", 
            "updated_at": "2024-01-01T10:00:00"  
        }
        
        # CORREGIDO: Parchear el nombre real de la función como se usa en el módulo de la ruta.
        # Asumimos que en `routes/nutrition/nutrition.py` se importa y usa directamente `get_user_nutrition_profile`.
        with patch('back_end.gym.routes.nutrition.nutrition.get_user_nutrition_profile', return_value=profile_data_from_db) as mock_get_profile_service_in_route:
            
            response = test_client.get("/api/nutrition/profile", headers={"Authorization": "Bearer fake.jwt.token"})
            
            assert response.status_code == 200, f"Response: {response.text}"
            result = response.json()
            assert result["user_id"] == auth_user["id"] 
            assert result["bmr"] == 1800.0
            mock_get_profile_service_in_route.assert_called_once_with(user_id=auth_user["id"])


    def test_save_nutrition_profile(self, test_client: TestClient, mock_auth, auth_user): 
        """Test saving nutrition profile. Este SÍ requiere autenticación."""
        profile_to_save = { 
            "formula": "harris_benedict",
            "gender": "female", 
            "age": 28,
            "height": 165.0,
            "weight": 60.0,
            "body_fat_percentage": 20.0, 
            "activity_level": "light",
            "goal": "gain",
            "goal_intensity": "normal",
            "units": "metric",
            "macro_distribution": { 
                "protein": 25,
                "carbs": 50,
                "fat": 25
            }
        }
        
        service_response_on_save = {"message": "Perfil nutricional guardado con éxito", "user_id": auth_user["id"]}

        # CORREGIDO: Parchear el nombre real de la función como se usa en el módulo de la ruta.
        # Asumimos que en `routes/nutrition/nutrition.py` se importa y usa directamente `save_user_nutrition_profile`.
        with patch('back_end.gym.routes.nutrition.nutrition.save_user_nutrition_profile', return_value=service_response_on_save) as mock_save_profile_service_in_route:
            
            response = test_client.post(
                "/api/nutrition/profile",
                json=profile_to_save,
                headers={"Authorization": "Bearer fake.jwt.token"}
            )
            
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert data["message"] == "Perfil nutricional guardado con éxito"
            
            mock_save_profile_service_in_route.assert_called_once_with(user_id=auth_user["id"], profile_data=profile_to_save)


    def test_calculate_macros_unauthenticated(self, test_client: TestClient, macro_calculator_data):
        """Test calculate_macros endpoint when unauthenticated."""
        app.dependency_overrides.clear() 
        response = test_client.post(
            "/api/nutrition/calculator/calculate-macros", # URL CORREGIDA
            json=macro_calculator_data,
            follow_redirects=False
        )
        assert response.status_code == 307, f"Response: {response.text}" # Espera 307 si está protegido
        assert "/login" in response.headers.get("Location", "")


    def test_get_nutrition_profile_unauthenticated(self, test_client: TestClient):
        """Test get_nutrition_profile endpoint without authentication."""
        app.dependency_overrides.clear()
        response = test_client.get("/api/nutrition/profile", follow_redirects=False)
        assert response.status_code == 307
        assert "/login" in response.headers.get("Location", "")

    def test_save_nutrition_profile_unauthenticated(self, test_client: TestClient, macro_calculator_data):
        """Test save_nutrition_profile endpoint without authentication."""
        app.dependency_overrides.clear()
        profile_to_save_unauth = {
            "formula": macro_calculator_data["formula"],
            "gender": macro_calculator_data["gender"],
            "age": macro_calculator_data["age"],
            "height": macro_calculator_data["height"],
            "weight": macro_calculator_data["weight"],
            "activity_level": macro_calculator_data["activity_level"],
            "goal": macro_calculator_data["goal"],
            "goal_intensity": macro_calculator_data["goal_intensity"],
            "units": macro_calculator_data["units"],
            "macro_distribution": macro_calculator_data["macro_distribution"]
        }
        response = test_client.post(
            "/api/nutrition/profile",
            json=profile_to_save_unauth,
            follow_redirects=False
        )
        assert response.status_code == 307
        assert "/login" in response.headers.get("Location", "")

