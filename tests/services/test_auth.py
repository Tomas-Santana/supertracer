import pytest
import os
from unittest.mock import MagicMock, patch
from supertracer.services.auth import AuthService
from supertracer.types.options import AuthOptions, ApiOptions

# Mock nicegui app storage
@pytest.fixture
def mock_app():
    with patch('supertracer.services.auth.app') as mock:
        # Setup storage.user as a dictionary
        mock.storage.user = {}
        yield mock

@pytest.fixture
def mock_ui():
    with patch('supertracer.services.auth.ui') as mock:
        yield mock

def test_auth_disabled_by_default(mock_app):
    service = AuthService()
    assert service.enabled is False
    assert service.is_authenticated() is True
    assert service.authenticate("any", "any") is True

def test_direct_auth_success(mock_app):
    options = AuthOptions(
        auth_enabled=True,
        username="admin",
        password="password123"
    )
    service = AuthService(options=options)
    
    assert service.enabled is True
    # Initially not authenticated in storage
    assert service.is_authenticated() is False
    
    # Check credentials
    assert service.authenticate("admin", "password123") is True
    assert service.authenticate("admin", "wrong") is False

def test_env_auth_success(mock_app):
    with patch.dict(os.environ, {"TEST_USER": "env_admin", "TEST_PASS": "env_pass"}):
        options = AuthOptions(
            auth_enabled=True,
            username_env="TEST_USER",
            password_env="TEST_PASS"
        )
        service = AuthService(options=options)
        
        assert service.authenticate("env_admin", "env_pass") is True
        assert service.authenticate("admin", "password") is False

def test_custom_auth_fn(mock_app):
    def my_auth(u, p):
        return u == "custom" and p == "secret"
        
    options = AuthOptions(
        auth_enabled=True,
        auth_fn=my_auth
    )
    service = AuthService(options=options)
    
    assert service.authenticate("custom", "secret") is True
    assert service.authenticate("custom", "wrong") is False

def test_login_flow(mock_app):
    options = AuthOptions(auth_enabled=True, username="u", password="p")
    service = AuthService(options=options)
    
    # Verify initial state
    assert service.is_authenticated() is False
    
    # Perform login
    service.login("u")
    
    # Verify storage update
    assert mock_app.storage.user['authenticated'] is True
    assert mock_app.storage.user['username'] == "u"
    assert service.is_authenticated() is True

def test_logout_flow(mock_app, mock_ui):
    options = AuthOptions(auth_enabled=True, username="u", password="p")
    service = AuthService(options=options)
    
    # Setup logged in state
    mock_app.storage.user = {'authenticated': True, 'username': 'u'}
    
    service.logout()
    
    assert mock_app.storage.user['authenticated'] is False
    assert mock_app.storage.user['username'] is None
    mock_ui.navigate.to.assert_called_with('/login')

def test_api_auth_disabled_by_default():
    service = AuthService()
    assert service.api_enabled is False
    assert service.api_authenticate("any_key") is True

def test_api_key_direct():
    api_options = ApiOptions(
        api_enabled=True,
        api_key="secret-api-key"
    )
    service = AuthService(api_options=api_options)
    
    assert service.api_enabled is True
    assert service.api_authenticate("secret-api-key") is True
    assert service.api_authenticate("wrong-key") is False

def test_api_key_env():
    with patch.dict(os.environ, {"MY_API_KEY": "env-key-123"}):
        api_options = ApiOptions(
            api_enabled=True,
            api_key_env="MY_API_KEY"
        )
        service = AuthService(api_options=api_options)
        
        assert service.api_authenticate("env-key-123") is True
        assert service.api_authenticate("wrong") is False
