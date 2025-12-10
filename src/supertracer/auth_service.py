import os
import logging
from typing import Optional, Callable
from nicegui import app, ui
from supertracer.types.options import AuthOptions

logger = logging.getLogger("supertracer")

class AuthService:
    def __init__(self, options: Optional[AuthOptions] = None):
        self.options = options or {}
        self.enabled = self._is_auth_enabled()
        self._setup_auth_method()

    def _is_auth_enabled(self) -> bool:
        return bool(self.options)

    def _setup_auth_method(self):
        if not self.enabled:
            return

        methods_count = 0
        self.auth_method: Optional[Callable[[str, str], bool]] = None

        # 1. Direct Username/Password
        if self.options.get('username') and self.options.get('password'):
            methods_count += 1
            self.auth_method = self._check_direct_auth

        # 2. Env Vars
        if self.options.get('username_env') and self.options.get('password_env'):
            methods_count += 1
            if self.auth_method is None:
                self.auth_method = self._check_env_auth

        # 3. Custom Function
        if self.options.get('auth_fn'):
            methods_count += 1
            if self.auth_method is None:
                self.auth_method = self.options.get('auth_fn')

        if methods_count > 1:
            logger.warning("Multiple authentication methods configured for SuperTracer. Using the highest priority one (Direct > Env > Function).")

    def _check_direct_auth(self, username, password) -> bool:
        return (username == self.options.get('username') and 
                password == self.options.get('password'))

    def _check_env_auth(self, username, password) -> bool:
        env_user = os.environ.get(self.options.get('username_env', ''))
        env_pass = os.environ.get(self.options.get('password_env', ''))
        return username == env_user and password == env_pass

    def authenticate(self, username, password) -> bool:
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
