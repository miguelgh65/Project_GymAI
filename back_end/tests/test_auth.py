import pytest
import os 
import time 
from unittest.mock import patch, MagicMock, ANY

# Excepción personalizada para diagnóstico (ya no se usará en test_google_auth_verify_success)
# class MockRoutesGetOrCreateUserCalled(Exception):
#     pass

def test_google_auth_verify_success(test_client):
    """Test successful Google authentication"""
    mock_google_lib_response = {
        "iss": "accounts.google.com",
        "azp": os.getenv("GOOGLE_CLIENT_ID", "test_client_id.apps.googleusercontent.com"),
        "aud": os.getenv("GOOGLE_CLIENT_ID", "test_client_id.apps.googleusercontent.com"),
        "sub": "google_user_12345", 
        "email": "test.user@example.com",
        "email_verified": True,
        "name": "Test User Google",
        "picture": "https://example.com/photo.jpg",
        "given_name": "Test",
        "family_name": "User",
        "locale": "en",
        "iat": 1600000000, 
        "exp": int(time.time()) + 3600, 
    }

    mock_internal_user_id = 1 # Simula el ID de usuario devuelto por get_or_create_user

    mock_user_details_from_db = { # Simula lo que get_user_by_id devolvería
        "id": mock_internal_user_id, 
        "email": "test.user@example.com",
        "name": "Test User Google",
        "profile_picture_url": "https://example.com/photo.jpg",
        "google_id": "google_user_12345", 
        "is_active": True, 
        "is_superuser": False,
        # Asegúrate que esta estructura coincida con tu UserPublicSchema o lo que devuelve el endpoint
    }
    
    # Parchear las funciones donde están DEFINIDAS (en los módulos de servicio)
    with patch('google.oauth2.id_token.verify_oauth2_token', return_value=mock_google_lib_response) as mock_google_verify_lib, \
         patch('back_end.gym.services.auth_service.get_or_create_user', return_value=mock_internal_user_id) as mock_get_or_create_user, \
         patch('back_end.gym.services.auth_service.get_user_by_id', return_value=mock_user_details_from_db) as mock_get_user_by_id, \
         patch('back_end.gym.services.jwt_service.create_access_token', return_value="generated_jwt_for_google_test") as mock_create_jwt:
        
        print("DEBUG: Mocks para test_google_auth_verify_success (patching en módulos de servicio) configurados.")
        response = test_client.post(
            "/api/auth/google/verify",
            json={"id_token": "fake_google_token_string_that_will_be_mocked"}
        )
        print(f"DEBUG: Response status: {response.status_code}, Response text: {response.text}")
            
        assert response.status_code == 200, f"Response: {response.text}"
        
        mock_google_verify_lib.assert_called_once_with(
            "fake_google_token_string_that_will_be_mocked", 
            ANY, 
            audience=os.getenv("GOOGLE_CLIENT_ID", "test_client_id.apps.googleusercontent.com")
        )
        
        mock_get_or_create_user.assert_called_once_with(
            db_session=ANY, 
            google_id=mock_google_lib_response['sub'],
            email=mock_google_lib_response['email'],
            name=mock_google_lib_response['name'],
            profile_picture_url=mock_google_lib_response['picture']
        )
        
        mock_get_user_by_id.assert_called_once_with(db_session=ANY, user_id=mock_internal_user_id)

        expected_token_payload = {"user_id": str(mock_internal_user_id), "email": mock_user_details_from_db["email"]}
        mock_create_jwt.assert_called_once_with(data=expected_token_payload)

        data = response.json()
        assert data.get("access_token") == "generated_jwt_for_google_test"
        
        user_response_data = data.get("user")
        assert user_response_data is not None
        assert user_response_data.get("id") == mock_user_details_from_db["id"]
        assert user_response_data.get("email") == mock_user_details_from_db["email"]
        assert user_response_data.get("name") == mock_user_details_from_db["name"]
        assert user_response_data.get("google_id") == mock_user_details_from_db["google_id"]


def test_google_auth_verify_invalid_token(test_client):
    """Test Google authentication with an invalid token"""
    with patch('google.oauth2.id_token.verify_oauth2_token', side_effect=ValueError("Invalid token")) as mock_google_verify_lib:
        response = test_client.post(
            "/api/auth/google/verify",
            json={"id_token": "invalid_token"}
        )
    assert response.status_code == 400
    mock_google_verify_lib.assert_called_once()
    assert "Token de Google inválido o expirado" in response.text


def test_generate_link_code_authenticated(test_client, auth_headers, mock_user): 
    """Test generating link code for authenticated user"""
    # Asumimos que el endpoint usa una dependencia `get_current_user`
    # y que esta dependencia está en `back_end.gym.middlewares` (o donde la hayas definido).
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.services.auth_service.generate_link_code', return_value="ABC123XYZ") as mock_generate_code_service: 
            # ^^^ Parchear generate_link_code en su módulo de servicio de origen
            response = test_client.post(
                "/api/generate-link-code",
                headers=auth_headers 
            )

    assert response.status_code == 200, f"Response: {response.text}"
    mock_dep_get_user.assert_called_once() 
    mock_generate_code_service.assert_called_once_with(user_id=int(mock_user["user_id"]), db_session=ANY)
    data = response.json()
    assert data["link_code"] == "ABC123XYZ"


def test_generate_link_code_unauthenticated(test_client):
    """Test generating link code without authentication, expects redirect"""
    response = test_client.post("/api/generate-link-code", follow_redirects=False) 
    assert response.status_code == 307 
    assert "/login" in response.headers.get("location", "")


def test_verify_link_code_success(test_client):
    """Test successful link code verification"""
    mock_auth_service_response = {"user_id": "123", "email": "verified_user@example.com"} 
    # La respuesta esperada del endpoint podría ser más completa si incluye el token y el usuario
    expected_endpoint_response = {"message": "Código verificado correctamente", 
                                  "access_token": "jwt_token_after_link_verify", 
                                  "user": mock_auth_service_response}

    # Parchear verify_link_code y create_access_token en sus módulos de servicio de origen
    with patch('back_end.gym.services.auth_service.verify_link_code', return_value=mock_auth_service_response) as mock_verify_link_code_service, \
         patch('back_end.gym.services.jwt_service.create_access_token', return_value="jwt_token_after_link_verify") as mock_jwt_create:
        
        response = test_client.post(
            "/api/verify-link-code",
            json={"code": "VALIDCODE123", "telegram_id": "telegram_user_789"}
        )

    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("message") == "Código verificado correctamente" 
    assert data.get("access_token") == "jwt_token_after_link_verify"
    user_in_response = data.get("user")
    assert user_in_response is not None
    assert user_in_response.get("user_id") == mock_auth_service_response["user_id"] # o "id"
    assert user_in_response.get("email") == mock_auth_service_response["email"]


def test_current_user_authenticated(test_client, auth_headers, mock_user): 
    """Test getting current user info when authenticated"""
    # Asumimos que el endpoint /api/current-user usa una dependencia get_current_user
    # que devuelve el objeto mock_user.
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user: 
        response = test_client.get(
            "/api/current-user",
            headers=auth_headers 
        )

    assert response.status_code == 200, f"Response: {response.text}"
    mock_dep_get_user.assert_called_once()
    data = response.json()
    assert data.get("email") == mock_user["email"]
    # mock_user tiene 'id' (int) y 'user_id' (str). El endpoint devuelve el schema User, que usa 'id'.
    assert data.get("id") == mock_user["id"] 
    assert data.get("name") == mock_user["name"]


def test_log_exercise_with_ai(test_client, auth_headers, mock_user):
    """Test logging exercise with AI processing"""
    mock_formatted_data = {"registro": [{"ejercicio": "press banca", "series": [{"repeticiones": 10, "peso": 50, "rir": None}]}]}
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.main.format_for_postgres', return_value=mock_formatted_data) as mock_format, \
         patch('back_end.gym.routes.main.insert_into_db', return_value=True) as mock_insert:
        
        response = test_client.post(
            "/api/log-exercise",
            json={"exercise_data": "press banca 10x50"},
            headers=auth_headers
        )
    
    assert response.status_code == 200, f"Response: {response.text}"
    assert "Ejercicio registrado correctamente" in response.json()["message"]


def test_log_exercise_reset_routine(test_client, auth_headers, mock_user):
    """Test resetting today's routine"""
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.main.reset_today_routine_status', return_value=True) as mock_reset:
        
        response = test_client.post(
            "/api/log-exercise",
            json={"exercise_data": "RESET_ROUTINE"},
            headers=auth_headers
        )
    
    assert response.status_code == 200, f"Response: {response.text}"
    assert response.json()["message"] == "Rutina de hoy reseteada."


def test_get_exercise_logs(test_client, auth_headers, mock_user):
    """Test getting exercise logs"""
    mock_logs = [{"fecha": "2024-03-20", "ejercicio": "press banca", "data": 50, "series_json": [{"repeticiones": 10, "peso": 50}]}]
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.main.get_exercise_logs_service', return_value=mock_logs) as mock_get_logs:
        
        response = test_client.get("/api/logs?days=7", headers=auth_headers)

    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert len(data) == 1
    assert data[0]["ejercicio"] == "press banca"


def test_get_today_routine(test_client, auth_headers, mock_user):
    """Test getting today's routine"""
    mock_routine_response = {"success": True, "rutina": [{"ejercicio": "press banca", "realizado": False}], "dia_nombre": "Lunes"}
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.routine.get_today_routine_details_service', return_value=mock_routine_response) as mock_get_routine:

        response = test_client.get("/api/rutina_hoy", headers=auth_headers)

    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["success"] is True


def test_save_routine(test_client, auth_headers, mock_user):
    """Test saving weekly routine"""
    routine_data = {"rutina": {"1": ["press banca"], "3": ["peso muerto"]}}
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.routine.save_user_routine_service', return_value=True) as mock_save:

        response = test_client.post("/api/rutina", json=routine_data, headers=auth_headers)

    assert response.status_code == 200, f"Response: {response.text}" 
    assert response.json().get("success") is True


def test_calculate_macros(test_client, auth_headers, mock_user): 
    """Test macro calculation - assuming it requires auth"""
    macro_input = {"units": "metric", "formula": "mifflin_st_jeor", "gender": "male", "age": 30, "height": 180, "weight": 80, "activity_level": "moderate", "goal": "maintain", "goal_intensity": "normal", "macro_distribution": {"protein": 30, "carbs": 40, "fat": 30}}
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user:
        response = test_client.post(
            "/api/nutrition/calculator/calculate-macros", 
            json=macro_input,
            headers=auth_headers 
        )

    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert "tdee" in data
    assert "macros" in data


def test_create_ingredient(test_client, auth_headers, mock_user):
    """Test creating a new ingredient"""
    ingredient_data = {"ingredient_name": "Pollo Test", "calories": 165, "proteins": 31, "carbohydrates": 0, "fats": 3.6, "unit": "g", "portion_size": 100}
    mock_service_response = {**ingredient_data, "id": 12345}

    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.nutrition.ingredients.create_ingredient_service', return_value=mock_service_response) as mock_create:
        
        response = test_client.post("/api/nutrition/ingredients", json=ingredient_data, headers=auth_headers)

    assert response.status_code == 201, f"Response: {response.text}"
    data = response.json()
    assert data["ingredient_name"] == "Pollo Test"


def test_create_meal(test_client, auth_headers, mock_user):
    """Test creating a new meal"""
    meal_data = {"meal_name": "Pollo con Arroz Test", "recipe": "Cocinar y servir.", "calories": 400, "proteins": 35, "carbohydrates": 45, "fats": 8, "meal_type": "Almuerzo", "ingredients": [{"ingredient_id": 1, "quantity": 150}]}
    mock_service_response = {**meal_data, "id": 56789}
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.nutrition.meals.create_meal_service', return_value=mock_service_response) as mock_create:
        response = test_client.post("/api/nutrition/meals", json=meal_data, headers=auth_headers)

    assert response.status_code == 201, f"Response: {response.text}"
    data = response.json()
    assert data["meal_name"] == "Pollo con Arroz Test"


def test_create_meal_plan(test_client, auth_headers, mock_user):
    """Test creating a meal plan"""
    plan_data = {"plan_name": "Plan Semanal Test", "start_date": "2024-05-25", "end_date": "2024-05-31", "is_active": True, "target_calories": 2500, "target_proteins": 180, "target_carbohydrates": 250, "target_fats": 70, "days": [{"day_of_week": "Lunes", "meals": [{"meal_id": 1, "meal_type": "Desayuno"}]}]}
    mock_service_response = {"id": 101, **plan_data} 
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.nutrition.meal_plans.create_meal_plan_service', return_value=mock_service_response) as mock_create_plan:
        response = test_client.post("/api/nutrition/meal-plans", json=plan_data, headers=auth_headers)

    assert response.status_code == 201, f"Response: {response.text}" 
    data = response.json()
    assert data["plan_name"] == "Plan Semanal Test"


def test_save_daily_tracking(test_client, auth_headers, mock_user):
    """Test saving daily nutrition tracking"""
    tracking_data = {"tracking_date": "2024-05-20", "completed_meals": {"Desayuno": True, "Almuerzo": True}, "calorie_note": "Día normal de test", "actual_calories": 2300, "excess_deficit": -200}
    mock_service_response = {"id": 202, "user_id": mock_user["user_id"], **tracking_data}
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.nutrition.tracking.save_daily_tracking_service', return_value=mock_service_response) as mock_save_track:
        response = test_client.post("/api/nutrition/tracking", json=tracking_data, headers=auth_headers)

    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["actual_calories"] == 2300


def test_get_exercise_stats(test_client, auth_headers, mock_user):
    """Test getting exercise statistics"""
    mock_dashboard_service_response = {"success": True, "ejercicios": ["press banca", "dominadas"], "total_ejercicios": 2}
    
    with patch('back_end.gym.middlewares.get_current_user', return_value=mock_user) as mock_dep_get_user, \
         patch('back_end.gym.routes.dashboard.get_user_exercise_stats_from_db', return_value=mock_dashboard_service_response) as mock_dashboard_call:
        response = test_client.get("/api/ejercicios_stats", headers=auth_headers)

    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data.get("success") is True
    assert "ejercicios" in data
