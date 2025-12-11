import os
import logging
from typing import Optional, Callable
from nicegui import app, ui
from supertracer.types.options import ApiOptions, AuthOptions

logger = logging.getLogger("supertracer")

class AuthService:
    """
    Service to handle authentication for SuperTracer.
    Supports multiple authentication methods:
    1. Direct Username/Password
    2. Environment Variables
    3. Custom Authentication Function
    Also handles API key authentication.
    
    Args:
        options: Authentication options for UI access
        api_options: Authentication options for API key access
        
    """
    def __init__(self, options: Optional[AuthOptions] = None, api_options: Optional[ApiOptions] = None):
        if options is None:
            self.options = AuthOptions()
        else:
            self.options = options
            
        if api_options is None:
            self.api_options = ApiOptions()
        elif isinstance(api_options, dict):
            self.api_options = ApiOptions(**api_options)
        else:
            self.api_options = api_options

        self.enabled = self.options.auth_enabled
        self.api_enabled = self.api_options.api_enabled
        self._setup_auth_method()
        self._setup_api_key_method()


    def _setup_auth_method(self):
        if not self.enabled:
            return

        methods_count = 0
        self.auth_method: Optional[Callable[[str, str], bool]] = None

        # 1. Direct Username/Password
        if self.options.username and self.options.password:
            methods_count += 1
            self.auth_method = self._check_direct_auth

        # 2. Env Vars
        if self.options.username_env and self.options.password_env:
            methods_count += 1
            if self.auth_method is None:
                self.auth_method = self._check_env_auth

        # 3. Custom Function
        if self.options.auth_fn:
            methods_count += 1
            if self.auth_method is None:
                self.auth_method = self.options.auth_fn

        if methods_count > 1:
            logger.warning("Multiple authentication methods configured for SuperTracer. Using the highest priority one (Direct > Env > Function).")
            
      
    # API Key Auth
    
    def _setup_api_key_method(self):
        if not self.api_enabled:
            return

        methods_count = 0
        self.api_key_method: Optional[Callable[[str], bool]] = None

        # 1. Direct API Key
        if self.api_options.api_key:
            methods_count += 1
            self.api_key_method = self._check_direct_api_auth

        # 2. Env Var
        if self.api_options.api_key_env:
            methods_count += 1
            if self.api_key_method is None:
                self.api_key_method = self._check_env_api_auth

        # 3. Custom Function
        if self.api_options.api_auth_fn:
            methods_count += 1
            if self.api_key_method is None:
                self.api_key_method = self.api_options.api_auth_fn

        if methods_count > 1:
            logger.warning("Multiple API key authentication methods configured for SuperTracer. Using the highest priority one (Direct > Env > Function).")
            
    def _check_direct_api_auth(self, api_key: str) -> bool:
        return api_key == self.api_options.api_key

    def _check_env_api_auth(self, api_key: str) -> bool:
        env_key = os.environ.get(self.api_options.api_key_env or '')
        return api_key == env_key
      
    def api_authenticate(self, api_key: str) -> bool:
        if not self.api_enabled:
            return True
        if not self.api_key_method:
            return False
        return self.api_key_method(api_key)  
    
    def _check_direct_auth(self, username: str, password: str) -> bool:
        return (username == self.options.username and 
                password == self.options.password)

    def _check_env_auth(self, username: str, password: str) -> bool:
        env_user = os.environ.get(self.options.username_env or '')
        env_pass = os.environ.get(self.options.password_env or '')
        return username == env_user and password == env_pass

    def authenticate(self, username: str, password: str) -> bool:
        if not self.enabled:
            return True
        if not self.auth_method:
            return False
        return self.auth_method(username, password)

    def login(self, username: str):
        app.storage.user['authenticated'] = True
        app.storage.user['username'] = username

    def logout(self):
        app.storage.user['authenticated'] = False
        app.storage.user['username'] = None
        ui.navigate.to('/login')

    def is_authenticated(self) -> bool:
        if not self.enabled:
            return True
        return app.storage.user.get('authenticated', False)
