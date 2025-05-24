import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from back_end.gym.app_fastapi import app
from back_end.gym.middlewares import get_current_user


class TestNutritionCalculator:
    """Test suite for nutrition calculator endpoints"""

    @pytest.fixture
    def auth_user(self):
        return {"id": 1, "email": "test@example.com"}

    @pytest.fixture
    def mock_auth(self, auth_user):
        app.dependency_overrides[get_current_user] = lambda: auth_user
        yield
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
        with patch('back_end.gym.services.db_utils.execute_db_query') as mock_db:
            mock_db.return_value = None  # No existing profile
            
            response = test_client.post(
                "/api/nutrition/calculate-macros",
                json=macro_calculator_data
            )
            
            assert response.status_code == 200
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
                "/api/nutrition/calculate-macros",
                json=data
            )
            
            assert response.status_code == 200
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
            "/api/nutrition/calculate-macros",
            json=data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["units"] == "imperial"
        assert result["daily_calories"] < result["tdee"]  # Deficit for weight loss

    def test_get_nutrition_profile(self, test_client: TestClient, mock_auth):
        """Test getting existing nutrition profile"""
        profile_data = {
            "user_id": "1",
            "formula": "mifflin_st_jeor",
            "sex": "male",
            "age": 30,
            "height": 180,
            "weight": 80,
            "body_fat_percentage": 15,
            "activity_level": "moderate",
            "goal": "maintain",
            "goal_intensity": "normal",
            "units": "metric",
            "bmr": 1800,
            "tdee": 2790,
            "bmi": 24.7,
            "daily_calories": 2790,
            "proteins_grams": 209,
            "carbs_grams": 279,
            "fats_grams": 93
        }
        
        with patch('back_end.gym.services.db_utils.execute_db_query') as mock_db:
            mock_db.return_value = profile_data
            
            response = test_client.get("/api/nutrition/profile")
            
            assert response.status_code == 200
            result = response.json()
            assert result["user_id"] == "1"
            assert result["bmr"] == 1800

    def test_save_nutrition_profile(self, test_client: TestClient, mock_auth):
        """Test saving nutrition profile"""
        profile_data = {
            "formula": "harris_benedict",
            "sex": "female",
            "age": 28,
            "height": 165,
            "weight": 60,
            "activity_level": "light",
            "goal": "gain",
            "goal_intensity": "normal",
            "units": "metric",
            "bmr": 1400,
            "tdee": 1925,
            "bmi": 22.0,
            "daily_calories": 2425,
            "proteins_grams": 121,
            "carbs_grams": 303,
            "fats_grams": 81
        }
        
        with patch('back_end.gym.services.db_utils.execute_db_query') as mock_db:
            mock_db.return_value = None
            
            response = test_client.post(
                "/api/nutrition/profile",
                json=profile_data
            )
            
            assert response.status_code == 200
            # Verify INSERT or UPDATE was called
