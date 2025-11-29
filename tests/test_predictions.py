import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import create_app
from app.services.prediction_service import prediction_service
from app.schemas.prediction import PredictionInputSchema


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_input():
    """Sample input data for prediction."""
    return {
        "air_temperature": 298.5,
        "process_temperature": 308.8,
        "rotational_speed": 1550,
        "torque": 45.5,
        "tool_wear": 120
    }


class TestPredictionService:
    """Test cases for PredictionService."""

    def test_predict_with_normal_data(self, sample_input):
        """Test prediction with normal sensor data."""
        input_data = PredictionInputSchema(**sample_input)
        result = prediction_service.predict(input_data)

        assert result.machine_status in ["Normal", "Warning", "Failure"]
        assert 0.0 <= result.probability <= 1.0
        assert isinstance(result.message, str)
        assert len(result.message) > 0

    def test_predict_with_high_risk_data(self):
        """Test prediction with high-risk sensor data."""
        high_risk_input = {
            "air_temperature": 310.0,
            "process_temperature": 320.0,
            "rotational_speed": 2000,
            "torque": 80.0,
            "tool_wear": 300
        }

        input_data = PredictionInputSchema(**high_risk_input)
        result = prediction_service.predict(input_data)

        assert result.machine_status in ["Warning", "Failure"]
        assert result.probability >= 0.6

    def test_predict_with_low_risk_data(self):
        """Test prediction with low-risk sensor data."""
        low_risk_input = {
            "air_temperature": 290.0,
            "process_temperature": 295.0,
            "rotational_speed": 1000,
            "torque": 20.0,
            "tool_wear": 50
        }

        input_data = PredictionInputSchema(**low_risk_input)
        result = prediction_service.predict(input_data)

        assert result.machine_status == "Normal"
        assert result.probability <= 0.5

    def test_model_loading(self):
        """Test that model is loaded correctly (or fallback is used)."""
        assert prediction_service.feature_columns is not None
        assert len(prediction_service.feature_columns) > 0


class TestPredictionEndpoints:
    """Test cases for prediction endpoints."""

    def test_predict_endpoint_success(self, client, sample_input):
        """Test successful prediction endpoint."""
        response = client.post("/api/v1/prediction/predict", json=sample_input)

        assert response.status_code == 200
        data = response.json()

        assert "machine_status" in data
        assert "probability" in data
        assert "message" in data
        assert data["machine_status"] in ["Normal", "Warning", "Failure"]
        assert 0.0 <= data["probability"] <= 1.0

    def test_predict_endpoint_invalid_data(self, client):
        """Test prediction endpoint with invalid data."""
        invalid_input = {
            "air_temperature": -100,
            "process_temperature": "invalid",
            "rotational_speed": 1550,
            "torque": 45.5,
            "tool_wear": 120
        }

        response = client.post("/api/v1/prediction/predict", json=invalid_input)
        assert response.status_code == 422

    def test_predict_endpoint_missing_data(self, client):
        """Test prediction endpoint with missing required fields."""
        incomplete_input = {
            "air_temperature": 298.5,
        }

        response = client.post("/api/v1/prediction/predict", json=incomplete_input)
        assert response.status_code == 422

    def test_model_status_endpoint(self, client):
        """Test model status endpoint."""
        response = client.get("/api/v1/prediction/model-status")

        assert response.status_code == 200
        data = response.json()

        assert "model_loaded" in data
        assert "model_path" in data
        assert "feature_columns" in data
        assert "message" in data


class TestHealthEndpoints:
    """Test cases for health and root endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert "Predictive Maintenance BE Server is running!" in data["message"]
        assert "version" in data
        assert "endpoints" in data

    def test_favicon_endpoint(self, client):
        """Test favicon endpoint returns 204."""
        response = client.get("/favicon.ico")
        assert response.status_code == 204


class TestMachineServiceIntegration:
    """Test cases for machine service integration."""

    def test_machine_service_initialization(self):
        """Test that machine service initializes correctly."""
        from app.services.machine_service import machine_service

        assert machine_service.machines is not None
        assert len(machine_service.machines) > 0

    def test_machine_status_generation(self):
        """Test that machine status can be generated."""
        from app.services.machine_service import machine_service

        machine_id = machine_service.settings.MACHINE_IDS[0]
        status = machine_service.get_machine_status(machine_id)

        assert status is not None
        assert status.machine_id == machine_id
        assert status.sensor_data is not None
        assert status.status in ["Normal", "Warning", "Failure"]
        assert 0.0 <= status.failure_probability <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])