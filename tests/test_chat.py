import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import create_app
from app.services.agent_service import agent_service


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestChatService:
    """Test cases for AgentService."""

    def test_agent_service_initialization(self):
        """Test that agent service initializes correctly."""
        assert agent_service is not None
        assert hasattr(agent_service, 'llm')
        assert hasattr(agent_service, 'agent_executor')

    def test_agent_availability_check(self):
        """Test that agent availability is checked correctly."""
        availability = agent_service.is_available()
        assert isinstance(availability, bool)

    @pytest.mark.asyncio
    async def test_chat_with_no_agent(self):
        """Test chat behavior when agent is not available."""
        with patch.object(agent_service, 'is_available', return_value=False):
            query = "Test query"

            try:
                result = await agent_service.chat(query)
                assert isinstance(result, str)
            except Exception as e:
                assert "tidak tersedia" in str(e).lower()


class TestChatEndpoints:
    """Test cases for chat endpoints."""

    def test_chat_endpoint_success(self, client):
        """Test successful chat endpoint when agent is available."""
        chat_input = {
            "query": "Apa itu predictive maintenance?"
        }

        response = client.post("/api/v1/chat/", json=chat_input)

        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert isinstance(data["response"], str)
            assert len(data["response"]) > 0
        else:
            assert response.status_code == 503
            data = response.json()
            assert "tidak tersedia" in data["detail"].lower()

    def test_chat_endpoint_invalid_data(self, client):
        """Test chat endpoint with invalid data."""
        invalid_input = {
            "invalid_field": "test"
        }

        response = client.post("/api/v1/chat/", json=invalid_input)
        assert response.status_code == 422

    def test_chat_endpoint_empty_query(self, client):
        """Test chat endpoint with empty query."""
        empty_input = {
            "query": ""
        }

        response = client.post("/api/v1/chat/", json=empty_input)

        if response.status_code == 200:
            data = response.json()
            assert "response" in data
        else:
            assert response.status_code in [503, 422]

    def test_chat_status_endpoint(self, client):
        """Test chat status endpoint."""
        response = client.get("/api/v1/chat/status")

        assert response.status_code == 200
        data = response.json()

        assert "agent_available" in data
        assert "model" in data
        assert "tools_available" in data
        assert "example_queries" in data
        assert isinstance(data["agent_available"], bool)
        assert isinstance(data["tools_available"], list)
        assert isinstance(data["example_queries"], list)


class TestChatIntegration:
    """Integration tests for chat functionality."""

    def test_chat_with_maintenance_queries(self, client):
        """Test chat with typical maintenance queries."""
        maintenance_queries = [
            "Prediksi mesin M14860",
            "Mesin mana yang paling berisiko?",
            "Bagaimana cara mengecek status semua mesin?",
            "Apa penyebab kerusakan mesin jika suhu tinggi?",
            "Berikan rekomendasi maintenance untuk mesin dengan torsi tinggi"
        ]

        for query in maintenance_queries:
            chat_input = {"query": query}
            response = client.post("/api/v1/chat/", json=chat_input)

            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert isinstance(data["response"], str)
                assert len(data["response"]) > 0
            else:
                assert response.status_code == 503

    def test_chat_with_general_knowledge(self, client):
        """Test chat with general knowledge queries."""
        general_queries = [
            "Apa itu machine learning?",
            "Jelaskan tentang industrial IoT",
            "Bagaimana cara kerja sensor suhu?"
        ]

        for query in general_queries:
            chat_input = {"query": query}
            response = client.post("/api/v1/chat/", json=chat_input)

            if response.status_code == 200:
                data = response.json()
                assert "response" in data
                assert isinstance(data["response"], str)
            else:
                assert response.status_code == 503


@pytest.mark.asyncio
class TestAgentTools:
    """Test cases for agent tools functionality."""

    async def test_prediction_tool_structure(self):
        """Test that prediction tool has correct structure."""
        if not agent_service.agent_executor:
            pytest.skip("Agent not available")

        tools = agent_service.agent_executor.tools
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "predict_machine_failure",
            "get_machine_status",
            "get_all_machines_status",
            "get_high_risk_machines"
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])