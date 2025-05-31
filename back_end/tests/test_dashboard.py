import pytest
from unittest.mock import patch, MagicMock
import time # Necesario para el payload del JWT
from datetime import datetime, date
from fastapi.testclient import TestClient

from back_end.gym.app_fastapi import app
from back_end.gym.middlewares import get_current_user


class TestDashboard:
    """Test suite for dashboard endpoints"""

    @pytest.fixture
    def auth_user(self):
        return {
            "id": 1,
            "google_id": "google_123",
            "email": "test@example.com",
            "display_name": "Test User"
        }

    @pytest.fixture
    def auth_user_payload(self, auth_user: dict) -> dict:
        """
        Prepara un payload JWT simulado que la función 'verify_token' (mockeada) 
        debería devolver. Esto representa el contenido decodificado del token.
        """
        return {
            "sub": str(auth_user["id"]), 
            "email": auth_user["email"],
            "name": auth_user.get("display_name", "Test User"), 
            "type": "access", 
            "exp": time.time() + 3600, 
            # Asegúrate que este campo (o el que uses para el ID interno en el payload)
            # es el que la lógica de `get_current_user` (o las funciones que llama)
            # espera para buscar el usuario si lo hace a partir del payload.
            "user_id_internal": auth_user["id"] 
        }

    @pytest.fixture
    def mock_auth(self, auth_user: dict, auth_user_payload: dict):
        """
        Mocks authentication.
        1. Patches 'verify_token' (called by middleware) to return a JWT payload.
        2. Overrides 'get_current_user' (route dependency) to return the full user dict.
        """
        # 1. Parchear la función de verificación de token que usa el middleware.
        #    Debe devolver un payload de token, no el objeto de usuario completo.
        with patch('back_end.gym.services.jwt_service.verify_token', return_value=auth_user_payload) as mock_verify_token_in_service:
            # 2. Sobrescribir la dependencia `get_current_user` para la ruta.
            #    Esto asegura que la ruta reciba el diccionario completo del usuario.
            app.dependency_overrides[get_current_user] = lambda: auth_user
            yield mock_verify_token_in_service # Puedes usar esto para aserciones si es necesario
            app.dependency_overrides.clear()

    @pytest.fixture
    def mock_db_data(self):
        """Mock database exercise data"""
        return [
            (datetime(2024, 1, 15), 30, "press banca", 
             '[{"repeticiones": 10, "peso": 60}, {"repeticiones": 8, "peso": 70}]', 
             "Bien", 2),
            (datetime(2024, 1, 17), 24, "press banca", 
             '[{"repeticiones": 12, "peso": 65}, {"repeticiones": 10, "peso": 75}]', 
             "Mejor", 1),
        ]

    def test_get_ejercicios_list(self, test_client: TestClient, mock_auth, mock_db_data):
        """Test getting list of available exercises"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = [("press banca",), ("sentadilla",), ("dominadas",)]
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn
            
            response = test_client.get("/api/ejercicios_stats", headers={"Authorization": "Bearer fake.jwt.token"})
            
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert len(data["ejercicios_disponibles"]) == 3
            assert "press banca" in data["ejercicios_disponibles"]

    def test_get_ejercicio_stats_with_data(self, test_client: TestClient, mock_auth, mock_db_data):
        """Test getting statistics for specific exercise"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = mock_db_data
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn
            
            response = test_client.get("/api/ejercicios_stats?ejercicio=press banca", headers={"Authorization": "Bearer fake.jwt.token"})
            
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert len(data["datos"]) == 2
            assert data["resumen"]["total_sesiones"] == 2
            assert data["resumen"]["max_weight_ever"] == 75.0

    def test_get_ejercicio_stats_with_date_filter(self, test_client: TestClient, mock_auth):
        """Test getting statistics with date filters"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = [] 
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn
            
            response = test_client.get(
                "/api/ejercicios_stats?ejercicio=press banca&desde=2024-01-01&hasta=2024-01-31",
                headers={"Authorization": "Bearer fake.jwt.token"}
            )
            
            assert response.status_code == 200, f"Response: {response.text}"
            mock_cur.execute.assert_called()
            # Para una verificación más robusta, podrías inspeccionar la consulta SQL:
            # called_query = mock_cur.execute.call_args[0][0]
            # assert "fecha_sesion >= %s" in called_query # O la sintaxis que uses
            # assert "fecha_sesion <= %s" in called_query
            # params = mock_cur.execute.call_args[0][1]
            # assert date(2024,1,1) in params # O como pases las fechas
            # assert date(2024,1,31) in params


    def test_calendar_heatmap_current_year(self, test_client: TestClient, mock_auth):
        """Test getting calendar heatmap data for current year"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = [
                (date(2024, 1, 15), 3),
                (date(2024, 1, 16), 2),
                (date(2024, 1, 17), 4)
            ]
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn
            
            response = test_client.get("/api/calendar_heatmap", headers={"Authorization": "Bearer fake.jwt.token"})
            
            assert response.status_code == 200, f"Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 3
            assert data["data"][0]["date"] == "2024-01-15"
            assert data["data"][0]["count"] == 3

    def test_calendar_heatmap_specific_year(self, test_client: TestClient, mock_auth):
        """Test getting calendar heatmap data for specific year"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn
            
            response = test_client.get("/api/calendar_heatmap?year=2023", headers={"Authorization": "Bearer fake.jwt.token"})
            
            assert response.status_code == 200, f"Response: {response.text}"
            mock_cur.execute.assert_called()
            # Para una verificación más robusta:
            # called_query = mock_cur.execute.call_args[0][0]
            # assert "EXTRACT(YEAR FROM fecha_sesion) = %s" in called_query # O la sintaxis que uses
            # params = mock_cur.execute.call_args[0][1]
            # assert 2023 in params


    def test_dashboard_unauthenticated(self, test_client: TestClient):
        """Test accessing dashboard without authentication"""
        app.dependency_overrides.clear() # Asegura que no hay overrides de autenticación
        
        response = test_client.get("/api/ejercicios_stats", follow_redirects=False)
        assert response.status_code == 307  # Redirect to login
        assert "/login" in response.headers.get("Location", "")