import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI
from nicegui import ui
from supertracer.connectors.base import BaseConnector
from supertracer.connectors.sqlite import SQLiteConnector
from supertracer.types.logs import Log
from supertracer.types.options import LoggerOptions, SupertracerOptions
from supertracer.ui.pages.logs_page import render_logs_page
from supertracer.ui.pages.request_detail_page import render_request_detail_page
from supertracer.logger import setup_logger
from supertracer.metrics import MetricsService
from supertracer.broadcaster import LogBroadcaster
from supertracer.middleware.logger_middleware import add_logger_middleware


class SuperTracer:
    def __init__(self, app: FastAPI, connector: Optional[BaseConnector] = None, options: Optional[SupertracerOptions] = None):
        self.app = app
        self.connector = connector if connector else SQLiteConnector("requests.db")
        self.options: SupertracerOptions = options if options else {}
        self.metrics_service = MetricsService(self.options.get('metrics_options'))
        self.broadcaster = LogBroadcaster()
        ui.run_with(self.app, mount_path="/supertracer")
        self._init_db()
        self._add_middleware()
        self._add_routes()
        
        # Setup logger for the application
        self.logger = setup_logger('supertracer', self.connector, self.broadcaster,
                                   level=self.options.get('logger_options', {}).get('level', logging.INFO),
                                   format_string=self.options.get('logger_options', {}).get('format', '%(levelname)s: %(message)s'))
    
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
        if name is None:
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
        self._add_nicegui_logs()

    def _add_nicegui_logs(self):
        """Add the /logs route with the new modular UI."""
        # Add dark theme CSS
        @ui.page('/logs')
        def logs_page():
            render_logs_page(self.connector.fetch_logs, self.metrics_service, self.broadcaster)

        @ui.page('/logs/{log_id}')
        def request_detail(log_id: int):
            render_request_detail_page(log_id, self.connector)
