import pytest
from fastapi.testclient import TestClient
import sys
import os
import logging
# import time # No es necesario aquí, pero sí en test_auth.py si se usa time.time()

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import FastAPI App ---
try:
    from back_end.gym.app_fastapi import app
except ModuleNotFoundError as e:
    logging.error(f"CRITICAL ERROR in conftest.py: Could not import 'app' from 'back_end.gym.app_fastapi'. ModuleNotFoundError: {e}", exc_info=True)
    logging.error(f"Calculated project_root: {project_root}")
    logging.error(f"sys.path at time of error: {sys.path}")
    expected_app_file = os.path.join(project_root, "back_end", "gym", "app_fastapi.py")
    logging.error(f"Expected app file location: {expected_app_file}")
    logging.error(f"Does app file exist? {os.path.exists(expected_app_file)}")
    sys.exit(f"pytest setup failed: Cannot import FastAPI app. Details: {e}")
except ImportError as e:
    logging.error(f"CRITICAL ERROR in conftest.py: ImportError while importing 'app' from 'back_end.gym.app_fastapi': {e}", exc_info=True)
    sys.exit(f"pytest setup failed: ImportError during app import. Details: {e}")


# --- Fixtures ---
@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="session")
def mock_user_data():
    """
    Provides mock user data. User ID is now an integer-like string.
    """
    return {
        "user_id": "123",  # <--- CAMBIO IMPORTANTE: ID de usuario que puede ser int()
        "email": "test@example.com",
        "name": "Test User",
        "profile_picture_url": "https://example.com/avatar.jpg",
        "is_active": True,
        "roles": ["user"],
    }

@pytest.fixture(scope="function")
def auth_headers(mock_user_data):
    try:
        from back_end.gym.services import jwt_service #

        token_data_for_creation = {
            "sub": mock_user_data["user_id"], # Se usará "123"
            "email": mock_user_data["email"]
        }
        access_token = jwt_service.create_access_token(data=token_data_for_creation)
        return {"Authorization": f"Bearer {access_token}"}
    except ImportError as e:
        logging.error(f"Failed to import jwt_service for auth_headers fixture: {e}")
        return {"Authorization": "Bearer mock_token_import_failed"}
    except Exception as e:
        logging.error(f"Error creating token in auth_headers fixture: {e}", exc_info=True)
        return {"Authorization": "Bearer mock_token_creation_failed"}

@pytest.fixture(scope="function")
def mock_user(mock_user_data):
    # Esta fixture ahora devolverá un mock_user_data con user_id "123".
    # Si tus patches `patch('back_end.gym.middlewares.get_current_user', return_value=mock_user)`
    # esperan que mock_user tenga una estructura específica (ej. un objeto User de Pydantic),
    # deberás ajustarlo aquí. Por ahora, devolvemos el dict.
    # Si get_current_user en tu app devuelve un objeto User con user_id como int,
    # este mock_user debería reflejarlo.
    processed_mock_user = mock_user_data.copy()
    try:
        # Si el user_id se usa como int en el objeto User que devuelve get_current_user
        processed_mock_user["id"] = int(mock_user_data["user_id"]) # Asumimos que el objeto user tiene 'id' como int
    except ValueError:
        pass # Mantener como string si no se puede convertir, aunque el problema principal está en la app
    return processed_mock_user