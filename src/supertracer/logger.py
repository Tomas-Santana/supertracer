import logging
from typing import Optional
from datetime import datetime
from supertracer.connectors.base import BaseConnector
from supertracer.types.logs import Log
from supertracer.broadcaster import LogBroadcaster


class DatabaseHandler(logging.Handler):
    """Custom logging handler that saves logs to database using a connector."""
    
    def __init__(self, connector: BaseConnector, broadcaster: Optional[LogBroadcaster] = None, level=logging.NOTSET):
        super().__init__(level)
        self.connector = connector
        self.broadcaster = broadcaster
    
    def emit(self, record: logging.LogRecord) -> None:
        """Save log record to database."""
        try:
            # format the log message
            log_entry = self.format(record)
            
            # Map logging levels to our log_level names
            level_mapping = {
                logging.DEBUG: 'DEBUG',
                logging.INFO: 'INFO',
                logging.WARNING: 'WARN',
                logging.ERROR: 'ERROR',
                logging.CRITICAL: 'ERROR'
            }
            
            log: Log = {
                'id': 0,  # Will be auto-generated
                'content': log_entry,
                'timestamp': datetime.fromtimestamp(record.created),
                'method': None,
                'path': None,
                'url': None,
                'headers': None,
                'log_level': level_mapping.get(record.levelno, 'INFO'),
                'status_code': None,
                'duration_ms': None,
                'client_ip': None,
                'user_agent': None,
                'request_query': None,
                'request_body': None,
                'response_headers': None,
                'response_body': None,
                'response_size_bytes': None,
                'error_message': None,
                'stack_trace': None
            }
            
            self.connector.save_log(log)
            if self.broadcaster:
                self.broadcaster.broadcast(log)
        except Exception:
            self.handleError(record)


def setup_logger(
    name: str,
    connector: BaseConnector,
    broadcaster: Optional[LogBroadcaster] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Setup a logger that saves to database.
    
    Args:
        name: Logger name (usually __name__)
        connector: Database connector to use for saving logs
        broadcaster: Broadcaster to use for real-time updates
        level: Logging level (default: INFO)
        format_string: Custom format string (default: '%(levelname)s: %(message)s')
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing DatabaseHandlers to ensure we use the latest connector/broadcaster
    # This is crucial when reloading the app (e.g. uvicorn reload) where the logger persists
    # but the SuperTracer instance (and thus broadcaster) is recreated.
    for handler in list(logger.handlers):
        if isinstance(handler, DatabaseHandler):
            logger.removeHandler(handler)
    
    # Create database handler
    db_handler = DatabaseHandler(connector, broadcaster)
    
    # Set formatter
    if format_string is None:
        format_string = '%(levelname)s: %(message)s'
    formatter = logging.Formatter(format_string)
    db_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(db_handler)
    
    # Also add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger
