import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json
import time # Necesario para el payload del JWT

from back_end.gym.app_fastapi import app # Main FastAPI application instance
from back_end.gym.middlewares import get_current_user # Dependency for auth

# It's good practice to have a conftest.py for fixtures,
# but for a single test file, defining them here is also okay.

class TestChatbot:
    """Test suite for chatbot endpoints"""

    @pytest.fixture
    def auth_user(self):
        """Provides a mock authenticated user dictionary."""
        return {
            "id": 1, # Este 'id' es el que se usará en el 'sub' del payload
            "google_id": "google_123", 
            "email": "test@example.com",
            "display_name": "Test User"
            # Añade otros campos que tu aplicación espere en el objeto de usuario completo
        }

    @pytest.fixture
    def auth_user_payload(self, auth_user: dict) -> dict:
        """
        Prepara un payload JWT simulado que la función 'verify_token' (mockeada) 
        debería devolver. Esto representa el contenido decodificado del token.
        """
        return {
            "sub": str(auth_user["id"]), # El 'subject' del token, usualmente el ID del usuario
            "email": auth_user["email"],
            "name": auth_user.get("display_name", "Test User"), # O el campo que uses en el token
            "type": "access", # Si usas tipos de token
            "exp": time.time() + 3600, # Timestamp de expiración (ej. 1 hora en el futuro)
            # Añade cualquier otro campo que tu función real verify_token/decode_jwt_token incluya
            # y que get_current_user pueda necesitar para obtener el usuario de la DB.
            "user_id_internal": auth_user["id"] # Asegúrate que esto coincida con lo que espera get_user_by_id si es llamado por get_current_user
        }


    @pytest.fixture
    def mock_auth(self, auth_user: dict, auth_user_payload: dict):
        """
        Mocks authentication inspired by test_auth.py.
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


    def test_chatbot_send_success(self, test_client: TestClient, mock_auth):
        """
        Test sending a successful message to the chatbot.
        This test now mocks 'process_message' which is assumed to handle the LangGraph logic.
        """
        expected_chatbot_response = "Esta es una respuesta del chatbot procesada"

        with patch('back_end.gym.routes.chatbot.process_message', new_callable=AsyncMock) as mock_process_message:
            mock_chat_response = MagicMock()
            mock_chat_response.content = expected_chatbot_response
            mock_process_message.return_value = mock_chat_response

            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Hola, necesito ayuda con mi rutina"},
                headers={"Authorization": "Bearer fake.jwt.token"} # El contenido del token no importa mucho aquí gracias al patch
            )

            assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert len(data["responses"]) > 0
            assert data["responses"][0]["role"] == "assistant"
            assert data["responses"][0]["content"] == expected_chatbot_response
            mock_process_message.assert_called_once_with(
                "google_123", 
                "Hola, necesito ayuda con mi rutina", 
                "fake.jwt.token" 
            )

    def test_chatbot_send_empty_message(self, test_client: TestClient, mock_auth):
        """Test sending an empty message to the chatbot."""
        response = test_client.post(
            "/api/chatbot/send",
            json={"message": ""}, 
            headers={"Authorization": "Bearer fake.jwt.token"}
        )

        assert response.status_code == 400, f"Expected status 400, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert "Message cannot be empty" in data.get("detail", "")

    def test_chatbot_send_unauthenticated(self, test_client: TestClient):
        """Test sending a message without authentication."""
        app.dependency_overrides.clear()

        response = test_client.post(
            "/api/chatbot/send",
            json={"message": "Test message"},
            follow_redirects=False 
        )

        assert response.status_code == 307, f"Expected status 307, got {response.status_code}. Response: {response.text}"
        assert "/login" in response.headers.get("Location", "")

    @pytest.mark.asyncio
    async def test_chatbot_streaming(self, test_client: TestClient, mock_auth):
        """
        Test streaming response from the chatbot (fallback path).
        """
        with patch('back_end.gym.routes.chatbot.CHATBOT_AVAILABLE', False), \
             patch('back_end.gym.routes.chatbot.llm') as mock_llm_in_route:
            
            async def mock_astream_generator(messages):
                chunks_content = ["Hola", " ", "mundo", " ", "desde", " ", "stream!"]
                for content_part in chunks_content:
                    mock_chunk = MagicMock()
                    mock_chunk.content = content_part
                    yield mock_chunk
            
            mock_llm_in_route.astream = mock_astream_generator

            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Hola stream", "stream": True},
                headers={"Authorization": "Bearer fake.jwt.token"}
            )

            assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"
            assert "text/event-stream" in response.headers["content-type"]

            streamed_content = response.text
            lines = streamed_content.strip().split('\n\n')
            actual_events = [json.loads(line.replace("data: ", "")) for line in lines if line.startswith("data: ") and line != "data: {}"]
            assert any(event.get("done") is True for event in actual_events), "Stream did not send 'done: True' event"
            reconstructed_message = ""
            for event in actual_events:
                if "content" in event and not event.get("done"): 
                    reconstructed_message = event["content"] 
            assert reconstructed_message == "Hola mundo desde stream!", f"Reconstructed message mismatch. Got: '{reconstructed_message}'"

    def test_chatbot_with_langgraph_integration(self, test_client: TestClient, mock_auth):
        """
        Test chatbot specifically when LangGraph integration is available and used.
        """
        expected_langgraph_response = "Respuesta procesada por LangGraph"
        with patch('back_end.gym.routes.chatbot.CHATBOT_AVAILABLE', True), \
             patch('back_end.gym.routes.chatbot.process_message', new_callable=AsyncMock) as mock_process_message:

            mock_chat_response = MagicMock()
            mock_chat_response.content = expected_langgraph_response
            mock_process_message.return_value = mock_chat_response

            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Dame mi rutina de hoy via LangGraph"},
                headers={"Authorization": "Bearer fake.jwt.token"}
            )

            assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert data["responses"][0]["role"] == "assistant"
            assert data["responses"][0]["content"] == expected_langgraph_response
            mock_process_message.assert_called_once_with(
                "google_123", 
                "Dame mi rutina de hoy via LangGraph", 
                "fake.jwt.token"
            )

    def test_chatbot_fallback_llm_when_langgraph_fails(self, test_client: TestClient, mock_auth):
        """
        Test fallback to basic LLM if LangGraph (process_message) raises an exception.
        """
        expected_fallback_response = "Respuesta del LLM de respaldo"
        with patch('back_end.gym.routes.chatbot.CHATBOT_AVAILABLE', True), \
             patch('back_end.gym.routes.chatbot.process_message', new_callable=AsyncMock) as mock_process_message, \
             patch('back_end.gym.routes.chatbot.llm') as mock_fallback_llm: 

            mock_process_message.side_effect = Exception("Simulated LangGraph error")
            mock_llm_response = MagicMock()
            mock_llm_response.content = expected_fallback_response
            mock_fallback_llm.invoke.return_value = mock_llm_response

            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Mensaje que causa error en LangGraph"},
                headers={"Authorization": "Bearer fake.jwt.token"}
            )

            assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert data["responses"][0]["content"] == expected_fallback_response
            mock_process_message.assert_called_once()
            mock_fallback_llm.invoke.assert_called_once()

    def test_chatbot_fallback_llm_when_langgraph_not_available(self, test_client: TestClient, mock_auth):
        """
        Test fallback to basic LLM if LangGraph is not available (CHATBOT_AVAILABLE=False).
        """
        expected_fallback_response = "Respuesta del LLM (LangGraph no disponible)"
        with patch('back_end.gym.routes.chatbot.CHATBOT_AVAILABLE', False), \
             patch('back_end.gym.routes.chatbot.llm') as mock_fallback_llm:

            mock_llm_response = MagicMock()
            mock_llm_response.content = expected_fallback_response
            mock_fallback_llm.invoke.return_value = mock_llm_response

            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Mensaje cuando LangGraph no está"},
                headers={"Authorization": "Bearer fake.jwt.token"}
            )

            assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"
            data = response.json()
            assert data["success"] is True
            assert data["responses"][0]["content"] == expected_fallback_response
            mock_fallback_llm.invoke.assert_called_once()
