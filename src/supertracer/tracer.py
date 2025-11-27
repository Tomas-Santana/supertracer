import time
import json
import os
import logging
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from nicegui import ui
from supertracer.connectors.base import BaseConnector
from supertracer.connectors.sqlite import SQLiteConnector
from supertracer.types.logs import Log
from supertracer.types.options import LoggerOptions, SupertracerOptions
from supertracer.ui.pages.logs_page import render_logs_page
from supertracer.logger import setup_logger


class SuperTracer:
    def __init__(self, app: FastAPI, connector: Optional[BaseConnector] = None, options: Optional[SupertracerOptions] = None):
        self.app = app
        self.connector = connector if connector else SQLiteConnector("requests.db")
        self.options = options if options else {}
        ui.run_with(self.app, mount_path="/supertracer")
        self._init_db()
        self._add_middleware()
        self._add_routes()
        
        # Setup logger for the application
        self.logger = setup_logger('supertracer', self.connector, 
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
        return setup_logger(name, self.connector, 
                            level=options.get('level', logging.INFO) if options else logging.INFO,
                            format_string=options.get('format') if options else '%(levelname)s: %(message)s')

    def _init_db(self):
        self.connector.connect()
        self.connector.init_db()

    def _add_middleware(self):
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next: Callable):
            # Capture request details
            method = request.method
            url = str(request.url)
            headers = dict(request.headers)
            start_time = time.time()

            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Save to DB after processing
            try:
                log: Log = {
                    'id': 0,  # Will be auto-generated
                    'content': f"{method} {url}",
                    'timestamp': datetime.now(),
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'log_level': 'HTTP',
                    'status_code': response.status_code,
                    'duration_ms': duration_ms
                }
                self.connector.save_log(log)
            except Exception as e:
                print(f"SuperTracer Error: {e}")

            return response

    def _add_routes(self):
        self._add_nicegui_logs()

    def _fetch_logs(self) -> List[Dict[str, Any]]:
        """Fetch logs and convert to UI-friendly format."""
        logs = self.connector.fetch_logs(limit=100)
        
        # Sample data for demonstration - replace with real mapping
        log_types = ['INFO', 'HTTP', 'WARN', 'ERROR', 'DEBUG']
        status_codes = [200, 404, 500]
        
        formatted_logs = []
        for i, log in enumerate(logs):
            # Extract endpoint path from URL
            endpoint = None
            if log.get('url'):
                from urllib.parse import urlparse
                parsed = urlparse(log.get('url'))
                endpoint = parsed.path or '/'
            
            formatted_log = {
                'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'type': log.get('log_level') or ('HTTP' if log.get('method') else log_types[i % len(log_types)]),
                'details': log['content'],
                'method': log.get('method'),
                'endpoint': endpoint,
                'status_code': log.get('status_code') or 200,
                'duration': f"{log.get('duration_ms') or (i * 15) % 1000}ms"
            }
            formatted_logs.append(formatted_log)
        
        return formatted_logs

    def _add_nicegui_logs(self):
        """Add the /logs route with the new modular UI."""
        # Add dark theme CSS
        @ui.page('/logs')
        def logs_page():
            logs_data = self._fetch_logs()
            render_logs_page(logs_data)