import pytest
from unittest.mock import Mock
from fastapi import Request
from supertracer.middleware.api_middleware import authenticate_request
from supertracer.types.options import ApiOptions
from supertracer.services.auth import AuthService

@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.headers = {}
    return request

@pytest.fixture
def mock_auth_service():
    service = Mock(spec=AuthService)
    # Ensure api_authenticate is present in the mock
    service.api_authenticate = Mock()
    return service

def test_api_disabled(mock_request, mock_auth_service):
    """Should allow request if API is disabled."""
    options = ApiOptions(api_enabled=False)
    assert authenticate_request(mock_request, mock_auth_service, options) is True

def test_no_auth_configured(mock_request, mock_auth_service):
    """Should allow request if API is enabled but no auth method is configured."""
    options = ApiOptions(api_enabled=True)
    assert authenticate_request(mock_request, mock_auth_service, options) is True

def test_missing_auth_header(mock_request, mock_auth_service):
    """Should deny request if auth is configured but header is missing."""
    options = ApiOptions(api_enabled=True, api_key="secret")
    
    assert authenticate_request(mock_request, mock_auth_service, options) is False

def test_valid_auth(mock_request, mock_auth_service):
    """Should allow request if auth header is valid."""
    options = ApiOptions(api_enabled=True, api_key="secret")
    mock_request.headers = {"Authorization": "secret"}
    mock_auth_service.api_authenticate.return_value = True
    
    assert authenticate_request(mock_request, mock_auth_service, options) is True
    mock_auth_service.api_authenticate.assert_called_with("secret")

def test_invalid_auth(mock_request, mock_auth_service):
    """Should deny request if auth header is invalid."""
    options = ApiOptions(api_enabled=True, api_key="secret")
    mock_request.headers = {"Authorization": "wrong"}
    mock_auth_service.api_authenticate.return_value = False
    
    assert authenticate_request(mock_request, mock_auth_service, options) is False
    mock_auth_service.api_authenticate.assert_called_with("wrong")

def test_auth_service_missing_method(mock_request):
    """Should allow request if auth service doesn't support API auth (fallback)."""
    class SimpleService:
        pass
    service = SimpleService()
    
    # Must configure auth so it passes the first check
    options = ApiOptions(api_enabled=True, api_key="secret")
    
    assert authenticate_request(mock_request, service, options) is True # type: ignore
