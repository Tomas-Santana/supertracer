import pytest
from unittest.mock import Mock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from supertracer.services.api import APIService
from supertracer.services.auth import AuthService
from supertracer.services.metrics import MetricsService
from supertracer.connectors.base import BaseConnector
from supertracer.types.options import ApiOptions
from supertracer.types.filters import LogFilters

@pytest.fixture
def mock_auth():
    auth = MagicMock(spec=AuthService)
    auth.api_enabled = True
    # Configure api_options to require auth
    auth.api_options = ApiOptions(api_enabled=True, api_key="secret")
    # Setup api_authenticate to behave correctly based on the key
    def check_auth(key):
        return key == "secret"
    auth.api_authenticate.side_effect = check_auth
    return auth

@pytest.fixture
def mock_metrics():
    metrics = MagicMock(spec=MetricsService)
    metrics.get_summary.return_value = {"status": "ok"}
    return metrics

@pytest.fixture
def mock_connector():
    connector = MagicMock(spec=BaseConnector)
    connector.fetch_logs.return_value = []
    connector.fetch_log.return_value = None
    return connector

@pytest.fixture
def api_client(mock_auth, mock_metrics, mock_connector):
    service = APIService(mock_auth, mock_metrics, mock_connector)
    app = FastAPI()
    app.include_router(service.router)
    return TestClient(app)

def test_status_endpoint_unauthorized(api_client):
    """Should return 401 if no auth header provided."""
    response = api_client.get("/supertracer-api/api/v1/status")
    assert response.status_code == 401

def test_status_endpoint_authorized(api_client):
    """Should return 200 if correct auth header provided."""
    response = api_client.get(
        "/supertracer-api/api/v1/status",
        headers={"Authorization": "secret"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

from datetime import datetime

@pytest.fixture
def sample_log():
    return {
        "id": 1,
        "content": "test",
        "timestamp": datetime.now(),
        "method": "GET",
        "path": "/test",
        "url": "http://test/test",
        "headers": {},
        "log_level": "INFO",
        "status_code": 200,
        "duration_ms": 100,
        "client_ip": "127.0.0.1",
        "user_agent": "test",
        "request_query": {},
        "request_body": {},
        "response_headers": {},
        "response_body": {},
        "response_size_bytes": 0,
        "error_message": None,
        "stack_trace": None
    }

def test_get_logs_endpoint(api_client, mock_connector, sample_log):
    """Should call connector.fetch_logs."""
    mock_connector.fetch_logs.return_value = [sample_log]
    
    response = api_client.get(
        "/supertracer-api/api/v1/logs",
        headers={"Authorization": "secret"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["content"] == "test"
    assert mock_connector.fetch_logs.called

def test_get_log_detail_endpoint(api_client, mock_connector, sample_log):
    """Should call connector.fetch_log."""
    mock_connector.fetch_log.return_value = sample_log
    
    response = api_client.get(
        "/supertracer-api/api/v1/logs/1",
        headers={"Authorization": "secret"}
    )
    
    assert response.status_code == 200
    assert response.json()["content"] == "test"
    mock_connector.fetch_log.assert_called_with(1)

def test_metrics_endpoint(api_client, mock_metrics):
    """Should call metrics.get_summary."""
    mock_metrics.get_summary.return_value = {"requests": 100}
    
    response = api_client.get(
        "/supertracer-api/api/v1/metrics",
        headers={"Authorization": "secret"}
    )
    
    assert response.status_code == 200
    assert response.json()["requests"] == 100
    assert mock_metrics.get_summary.called

def test_routes_not_added_if_disabled():
    """Should not add routes if api_enabled is False."""
    auth = MagicMock(spec=AuthService)
    auth.api_enabled = False
    metrics = MagicMock(spec=MetricsService)
    connector = MagicMock(spec=BaseConnector)
    
    service = APIService(auth, metrics, connector)
    
    # Router should be empty (or at least have no routes from _add_routes)
    assert len(service.router.routes) == 0
