# test_app.py
import pytest
from app import app


# Clases "fake" para simular las funciones de formateo e inserción
class FakePrompts:
    @staticmethod
    def format_for_postgres(text: str):
        # Devuelve un JSON simulado representando el resultado del formateo
        return {
            "registro": [
                {
                    "ejercicio": "press banca",
                    "series": [{"repeticiones": 5, "peso": 75}]
                }
            ]
        }

class FakeLogic:
    @staticmethod
    def insert_into_db(json_data):
        # Simula que la inserción en la base de datos fue exitosa
        return True

# Fixture que configura el entorno de test, parcheando las funciones reales
@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app, "format_for_postgres", FakePrompts.format_for_postgres)
    monkeypatch.setattr(app, "insert_into_db", FakeLogic.insert_into_db)
    with app.test_client() as client:
        yield client

# Pruebas organizadas en una clase
class TestApp:
    def test_index_get(self, client):
        response = client.get('/')
        assert response.status_code == 200
        # Verifica que se retorne HTML (se asume que index.html contiene la etiqueta <html>)
        assert b"<html" in response.data.lower()

    def test_index_post_success(self, client):
        # Envía datos de prueba mediante POST
        data = {"exercise_data": "press banca 5x75, 7x70, 8x60"}
        response = client.post("/", data=data)
        json_data = response.get_json()
        assert json_data["success"] is True
        assert "Datos insertados correctamente" in json_data["message"]
