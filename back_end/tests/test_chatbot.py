import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json

from back_end.gym.app_fastapi import app
from back_end.gym.middlewares import get_current_user


class TestChatbot:
    """Test suite for chatbot endpoints"""

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
        """Mock authentication"""
        app.dependency_overrides[get_current_user] = lambda: auth_user
        yield
        app.dependency_overrides.clear()

    def test_chatbot_send_success(self, test_client: TestClient, mock_auth):
        """Test sending message to chatbot"""
        mock_response = MagicMock()  
        mock_response.content = "Esta es una respuesta del chatbot"
        
        with patch('back_end.gym.config.llm') as mock_llm:
            mock_llm.invoke.return_value = mock_response
            
            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Hola, necesito ayuda con mi rutina"},
                headers={"Authorization": "Bearer fake_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["responses"]) > 0
            assert data["responses"][0]["role"] == "assistant"

    def test_chatbot_send_empty_message(self, test_client: TestClient, mock_auth):
        """Test sending empty message"""
        response = test_client.post(
            "/api/chatbot/send",
            json={"message": ""},
            headers={"Authorization": "Bearer fake_token"}
        )
        
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]

    def test_chatbot_send_unauthenticated(self, test_client: TestClient):
        """Test sending message without authentication"""
        app.dependency_overrides.clear()
        
        response = test_client.post(
            "/api/chatbot/send",
            json={"message": "Test message"}
        )
        
        assert response.status_code == 307  # Redirect to login

    @pytest.mark.asyncio
    async def test_chatbot_streaming(self, test_client: TestClient, mock_auth):
        """Test streaming response from chatbot"""
        with patch('back_end.gym.config.llm') as mock_llm:
            # Simular streaming
            async def mock_astream(messages):
                chunks = ["Hola", " ", "¿cómo", " ", "puedo", " ", "ayudarte?"]
                for chunk in chunks:
                    mock_chunk = MagicMock()
                    mock_chunk.content = chunk
                    yield mock_chunk
            
            mock_llm.astream = mock_astream
            
            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Hola", "stream": True},
                headers={"Authorization": "Bearer fake_token"}
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

    def test_chatbot_with_langgraph(self, test_client: TestClient, mock_auth):
        """Test chatbot with LangGraph integration"""
        with patch('fitness_chatbot.nodes.router_node.process_message') as mock_process:
            mock_response = MagicMock()
            mock_response.content = "Respuesta desde LangGraph"
            mock_process.return_value = mock_response
            
            response = test_client.post(
                "/api/chatbot/send",
                json={"message": "Dame mi rutina de hoy"},
                headers={"Authorization": "Bearer fake_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "LangGraph" in data["responses"][0]["content"]
