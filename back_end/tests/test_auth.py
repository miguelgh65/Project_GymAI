import os
import time
import pytest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Importa tu aplicación FastAPI principal y la dependencia original
from back_end.gym.app_fastapi import app as main_app
from back_end.gym.middlewares import get_current_user as get_current_user_original_dependency
# from back_end.gym.models.schemas import UserPublicSchema # Si necesitas instanciarla


@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Fixture para la instancia de la aplicación FastAPI."""
    main_app.dependency_overrides.clear()
    return main_app


@pytest.fixture
def test_client(app: FastAPI) -> TestClient:
    """Fixture para el TestClient que usa la app con posibles overrides."""
    return TestClient(app)


@pytest.fixture
def mock_user_data() -> dict:
    """Datos para el usuario mock."""
    return {
        "id": 123,
        "user_id_internal": 123,
        "email": "test@example.com",
        "name": "Test User",
        "display_name": "Test User",
        "is_active": True,
        "google_id": "google_test_id",
        "telegram_id": None,
        "profile_picture": "http://example.com/pic.jpg"
    }

@pytest.fixture
def mock_jwt_payload(mock_user_data: dict) -> dict:
    """Payload JWT mock que `verify_token` (mockeado) debería devolver."""
    return {
        "sub": str(mock_user_data["id"]),
        "email": mock_user_data["email"],
        "name": mock_user_data["name"],
        "type": "access",
        "exp": time.time() + 3600
    }

@pytest.fixture
def auth_headers() -> dict:
    """Cabeceras de autenticación con un token JWT falso pero bien formado."""
    return {"Authorization": "Bearer fake.jwt.token.string"}


# Test que ya pasaba
def test_google_auth_verify_success(test_client: TestClient):
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
    }
    mock_internal_user_id = 1
    mock_user_details_from_db = { "id": mock_internal_user_id, "email": "test.user@example.com", "display_name": "Test User Google", "google_id": "google_user_12345", "telegram_id": None }

    with patch('google.oauth2.id_token.verify_oauth2_token', return_value=mock_google_lib_response), \
         patch('back_end.gym.routes.auth.get_or_create_user', return_value=mock_internal_user_id), \
         patch('back_end.gym.routes.auth.get_user_by_id', return_value=mock_user_details_from_db), \
         patch('back_end.gym.services.jwt_service.create_access_token', return_value="generated_jwt_for_google_test"):
        response = test_client.post(
            "/api/auth/google/verify",
            json={"id_token": "fake_google_token_string_that_will_be_mocked"}
        )
        assert response.status_code == 200, f"Response: {response.text}"
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["user"]["id"] == mock_internal_user_id


# RECOMENDADO: Usando app.dependency_overrides Y parcheando verify_token en `services.jwt_service`
def test_generate_link_code_authenticated_with_override(
    app: FastAPI,
    test_client: TestClient,
    mock_user_data: dict,
    mock_jwt_payload: dict, # Payload que verify_token (mockeado) devolverá
    auth_headers: dict
):
    """Test generating link code for authenticated user with middleware and route dependency mocked."""
    
    # 1. Parchear `verify_token` en `services.jwt_service`.
    #    El AuthenticationMiddleware importa y usa `verify_token` desde `.services.jwt_service`.
    #    Este parche hará que el middleware crea que el token es válido.
    with patch('back_end.gym.services.jwt_service.verify_token', return_value=mock_jwt_payload) as mock_service_verify_token:
        
        # 2. Sobrescribir la dependencia `get_current_user` para la RUTA.
        app.dependency_overrides[get_current_user_original_dependency] = lambda: mock_user_data
        
        # 3. Parchear la función de servicio que la ruta llama DESPUÉS de la autenticación.
        with patch('back_end.gym.routes.auth.generate_link_code', return_value="ABC123XYZ") as mock_generate_code_service:
            response = test_client.post(
                "/api/generate-link-code",
                headers=auth_headers
            )

    app.dependency_overrides.clear()

    assert response.status_code == 200, f"Response: {response.text}"
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["code"] == "ABC123XYZ"
    
    mock_service_verify_token.assert_called_once_with(auth_headers["Authorization"].replace("Bearer ", ""))
    mock_generate_code_service.assert_called_once_with(mock_user_data.get("id"))


# Test que ya pasaba
def test_generate_link_code_authenticated_patch_based(
    test_client: TestClient,
    mock_user_data: dict,
    mock_jwt_payload: dict,
    auth_headers: dict
):
    """Test generating link code for authenticated user using multiple patches."""
    with patch('back_end.gym.services.jwt_service.verify_token', return_value=mock_jwt_payload) as mock_jwt_verify, \
         patch('back_end.gym.services.auth_service.get_user_by_id', return_value=mock_user_data) as mock_get_user_db, \
         patch('back_end.gym.routes.auth.generate_link_code', return_value="ABC123XYZ") as mock_generate_code_service:
        response = test_client.post(
            "/api/generate-link-code",
            headers=auth_headers
        )
    assert response.status_code == 200, f"Response: {response.text}"
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["code"] == "ABC123XYZ"
    mock_jwt_verify.assert_called_once_with(auth_headers["Authorization"].replace("Bearer ", ""))
    mock_get_user_db.assert_called_once_with(int(mock_jwt_payload["sub"]))
    mock_generate_code_service.assert_called_once_with(mock_user_data.get("id"))


# Test que ya pasaba
def test_verify_link_code_success(test_client: TestClient):
    """Test successful link code verification"""
    with patch('back_end.gym.routes.auth.verify_link_code', return_value=True) as mock_verify_link_in_route:
        response = test_client.post(
            "/api/verify-link-code",
            json={"code": "VALIDCODE123", "telegram_id": "telegram_user_789"}
        )
    assert response.status_code == 200, f"Response: {response.text}"
    # ... (aserciones como estaban) ...

# Test `test_current_user_authenticated` CORREGIDO
def test_current_user_authenticated(
    app: FastAPI,
    test_client: TestClient,
    mock_user_data: dict,
    mock_jwt_payload: dict, # Payload que verify_token (mockeado) devolverá
    auth_headers: dict
):
    """Test fetching current user when authenticated."""
    # 1. Parchear `verify_token` en `services.jwt_service` para que el middleware autentique.
    with patch('back_end.gym.services.jwt_service.verify_token', return_value=mock_jwt_payload) as mock_service_verify_token:
        # 2. Sobrescribir la dependencia `get_current_user` para la RUTA.
        app.dependency_overrides[get_current_user_original_dependency] = lambda: mock_user_data
        
        response = test_client.get("/api/current-user", headers=auth_headers)

    app.dependency_overrides.clear()

    assert response.status_code == 200, f"Response: {response.text}"
    response_data = response.json()
    assert response_data["success"] is True
    expected_user = {
        "id": mock_user_data["id"],
        "display_name": mock_user_data["display_name"],
        "email": mock_user_data["email"],
        "profile_picture": mock_user_data["profile_picture"],
        "has_telegram": (mock_user_data.get("telegram_id") is not None),
        "has_google": (mock_user_data.get("google_id") is not None),
    }
    assert response_data["user"] == expected_user
    mock_service_verify_token.assert_called_once_with(auth_headers["Authorization"].replace("Bearer ", ""))