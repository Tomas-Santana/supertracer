import logging
import os
import asyncio
from typing import Optional, List, Dict, Any, Union
from fastapi import FastAPI
from nicegui import ui
from supertracer.connectors.base import BaseConnector
from supertracer.connectors.memory import MemoryConnector
from supertracer.types.logs import Log
from supertracer.types.options import LoggerOptions, SupertracerOptions
from supertracer.ui.pages.logs_page import render_logs_page
from supertracer.ui.pages.request_detail_page import render_request_detail_page
from supertracer.ui.pages.login_page import render_login_page
from supertracer.services.logger import setup_logger
from supertracer.services.metrics import MetricsService
from supertracer.services.auth import AuthService
from supertracer.services.broadcaster import LogBroadcaster
from supertracer.services.api import APIService
from supertracer.services.cleanup import CleanupService
from supertracer.services.json_options import JSONOptionsService
from supertracer.middleware.logger_middleware import add_logger_middleware


class SuperTracer:
    def __init__(self, 
        app: FastAPI, 
        connector: Optional[BaseConnector] = None, 
        options: Optional[Union[SupertracerOptions, str]] = None
        ):
        self.app = app
        
        self._setup_options(options)

        self.connector = connector if connector else MemoryConnector()

        self.metrics_service = MetricsService(self.options.metrics_options)
        self.auth_service = AuthService(self.options.auth_options, self.options.api_options)
        self.broadcaster = LogBroadcaster()
        
        
        self.logger = setup_logger('supertracer', 
                                   self.connector, 
                                   self.broadcaster,
                                   level=self.options.logger_options.level,
                                   format_string=self.options.logger_options.format)
        self._setup_ui()
        self._init_db()
        self._add_middleware()
        self._add_routes()
        self._add_api_routes()
        
        self.cleanup = CleanupService(self.app, self.connector, self.options.retention_options, self.logger)
         
    def _setup_options(self, options: Optional[SupertracerOptions | str]):
        if options is None:
            # Try loading from default file
            loaded_options = JSONOptionsService.load_from_file()
            self.options = loaded_options if loaded_options else SupertracerOptions()
        elif isinstance(options, str):
            loaded_options = JSONOptionsService.load_from_file(options)
            if loaded_options is None:
                 raise ValueError(f"Configuration file not found: {options}")
            self.options = loaded_options
        elif isinstance(options, dict):
            try:
                self.options = SupertracerOptions(**options)
            except Exception as e:
                raise ValueError(f"Invalid SupertracerOptions: {e}")
        else:
            self.options = options
               
    def _setup_ui(self):
        
        auth_options = self.options.auth_options
        storage_secret = auth_options.storage_secret or 'supertracer_secret'
        if auth_options.storage_secret_env:
            storage_secret = os.getenv(auth_options.storage_secret_env, storage_secret)
            
        ui.run_with(self.app, mount_path="/supertracer", storage_secret=storage_secret)
    
    def get_logger(self, name: Optional[str] = None, options: Optional[LoggerOptions] = None) -> logging.Logger:
        """Get a logger instance that saves to the database.
        
        
        Args:
            name: Logger name (if None, returns the default supertracer logger)
        
        Returns:
            Logger instance configured to save to database
        
        ## Notes:
        
            If you do not have access to the SuperTracer instance, you can get the logger via:
            
            ```python
            >>> import logging
            
             >>> logger = logging.getLogger('supertracer') 
             >>> # or any other name (if you have created it using supertracer.create_logger or get_logger)
        ```
        
        Example:
        ```python
            >>> tracer = SuperTracer(app)
            >>> logger = tracer.get_logger('my_module')
            >>> logger.info("Processing request")
            >>> logger.error("An error occurred")
        ```
            
        
        """
        if name is None or name == 'supertracer':
            return self.logger
            
        if options is None:
            logger_opts = LoggerOptions()
        elif isinstance(options, dict):
            logger_opts = LoggerOptions(**options)
        else:
            logger_opts = options
            
        return setup_logger(name, self.connector, self.broadcaster,
                            level=logger_opts.level,
                            format_string=logger_opts.format)

    def create_logger(self, name: str, options: Optional[LoggerOptions] = None) -> None:
        """Create and configure a new logger that saves to the database.
        
        This is useful if you want to create multiple loggers with different names
        and configurations.
        
        Args:
            name: Logger name
            options: LoggerOptions instance or dict to configure the logger
        """
        self.get_logger(name, options)
    
    def _init_db(self):
        self.connector.connect()
        self.connector.init_db()

    def _add_middleware(self):
        add_logger_middleware(self.options, self.connector, self.broadcaster, self.metrics_service, self.app)
        

    def _add_routes(self):
        self._add_pages()
        
    def _add_api_routes(self):
        if not self.auth_service.api_enabled:
            return
        
        api_service = APIService(self.auth_service, self.metrics_service, self.connector)
        self.app.include_router(api_service.router)

    def _add_pages(self):
        """Add the /logs route with the new modular UI."""
        
        @ui.page('/login')
        def login_page():
            ui.query('.nicegui-content').classes('p-0')
            if self.auth_service.is_authenticated():
                ui.navigate.to('/logs')
                return
            render_login_page(self.auth_service)

        @ui.page('/logs')
        def logs_page():
            ui.query('.nicegui-content').classes('p-0')
            if not self.auth_service.is_authenticated():
                ui.navigate.to('/login')
                return
            render_logs_page(self.connector, self.metrics_service, self.broadcaster, self.auth_service)

        @ui.page('/logs/{log_id}')
        def request_detail(log_id: int):
            ui.query('.nicegui-content').classes('p-0')
            if not self.auth_service.is_authenticated():
                ui.navigate.to('/login')
                return
            render_request_detail_page(log_id, self.connector, self.auth_service)
