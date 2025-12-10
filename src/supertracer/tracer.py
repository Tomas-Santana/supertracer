import logging
import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI
from nicegui import ui
from supertracer.connectors.base import BaseConnector
from supertracer.connectors.sqlite import SQLiteConnector
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
from supertracer.middleware.logger_middleware import add_logger_middleware


class SuperTracer:
    def __init__(self, app: FastAPI, connector: Optional[BaseConnector] = None, options: Optional[SupertracerOptions] = None):
        self.app = app
        self.connector = connector if connector else SQLiteConnector("requests.db")
        self.options: SupertracerOptions = options if options else {}
        self.metrics_service = MetricsService(self.options.get('metrics_options'))
        self.auth_service = AuthService(self.options.get('auth_options'), self.options.get('api_options'))
        self.broadcaster = LogBroadcaster()
        
        
        self.logger = setup_logger('supertracer', 
                                   self.connector, 
                                   self.broadcaster,
                                   level=self.options.get('logger_options', {}).get('level', logging.INFO),
                                   format_string=self.options.get('logger_options', {}).get('format', '%(message)s'))
        self._setup_ui()
        self._init_db()
        self._add_middleware()
        self._add_routes()
        self._add_api_routes()
                
    def _setup_ui(self):
        
        auth_options = self.options.get('auth_options', {})
        storage_secret = auth_options.get('storage_secret', 'supertracer_secret')
        storage_secret = storage_secret or os.getenv(auth_options.get('storage_secret_env', 'supertracer_secret'))
        ui.run_with(self.app, mount_path="/supertracer", storage_secret=storage_secret)
    
    def get_logger(self, name: Optional[str] = None, options: Optional[LoggerOptions] = None) -> logging.Logger:
        """Get a logger instance that saves to the database.
        
        Args:
            name: Logger name (if None, returns the default supertracer logger)
        
        Returns:
            Logger instance configured to save to database
        
        Example:
            >>> tracer = SuperTracer(app)
            >>> logger = tracer.get_logger('my_module')
            >>> logger.info("Processing request")
            >>> logger.error("An error occurred")
        """
        if name is None or name == 'supertracer':
            return self.logger
        return setup_logger(name, self.connector, self.broadcaster,
                            level=options.get('level', logging.INFO) if options else logging.INFO,
                            format_string=options.get('format') if options else '%(levelname)s: %(message)s')

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
        
        api_service = APIService(self.auth_service, self.connector)
        self.app.include_router(api_service.router)


    def _add_pages(self):
        """Add the /logs route with the new modular UI."""
        
        @ui.page('/login')
        def login_page():
            if self.auth_service.is_authenticated():
                ui.navigate.to('/logs')
                return
            render_login_page(self.auth_service)

        @ui.page('/logs')
        def logs_page():
            if not self.auth_service.is_authenticated():
                ui.navigate.to('/login')
                return
            render_logs_page(self.connector, self.metrics_service, self.broadcaster, self.auth_service)

        @ui.page('/logs/{log_id}')
        def request_detail(log_id: int):
            if not self.auth_service.is_authenticated():
                ui.navigate.to('/login')
                return
            render_request_detail_page(log_id, self.connector, self.auth_service)
