import logging
from typing import Optional
from datetime import datetime
from supertracer.connectors.base import BaseConnector
from supertracer.types.logs import Log


class DatabaseHandler(logging.Handler):
    """Custom logging handler that saves logs to database using a connector."""
    
    def __init__(self, connector: BaseConnector, level=logging.NOTSET):
        super().__init__(level)
        self.connector = connector
    
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
                'url': None,
                'headers': None,
                'log_level': level_mapping.get(record.levelno, 'INFO'),
                'status_code': None,
                'duration_ms': None
            }
            
            self.connector.save_log(log)
        except Exception:
            self.handleError(record)


def setup_logger(
    name: str,
    connector: BaseConnector,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Setup a logger that saves to database.
    
    Args:
        name: Logger name (usually __name__)
        connector: Database connector to use for saving logs
        level: Logging level (default: INFO)
        format_string: Custom format string (default: '%(levelname)s: %(message)s')
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if already configured to avoid duplicates
    if logger.handlers:
        return logger
    
    # Create database handler
    db_handler = DatabaseHandler(connector)
    
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
