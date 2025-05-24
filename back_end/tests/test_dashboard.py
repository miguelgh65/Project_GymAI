import pytest
from unittest.mock import patch, MagicMock
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
    def mock_auth(self, auth_user):
        app.dependency_overrides[get_current_user] = lambda: auth_user
        yield
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
            
            response = test_client.get("/api/ejercicios_stats")
            
            assert response.status_code == 200
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
            
            response = test_client.get("/api/ejercicios_stats?ejercicio=press banca")
            
            assert response.status_code == 200
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
                "/api/ejercicios_stats?ejercicio=press banca&desde=2024-01-01&hasta=2024-01-31"
            )
            
            assert response.status_code == 200
            mock_cur.execute.assert_called()
            # Verify date filters were applied in query

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
            
            response = test_client.get("/api/calendar_heatmap")
            
            assert response.status_code == 200
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
            
            response = test_client.get("/api/calendar_heatmap?year=2023")
            
            assert response.status_code == 200
            # Verify correct year was used in query

    def test_dashboard_unauthenticated(self, test_client: TestClient):
        """Test accessing dashboard without authentication"""
        response = test_client.get("/api/ejercicios_stats")
        assert response.status_code == 307  # Redirect to login