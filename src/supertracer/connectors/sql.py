from abc import abstractmethod
from typing import Any, List, Optional
from supertracer.connectors.base import BaseConnector
from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
from supertracer.types.options import RetentionOptions
from datetime import datetime, timedelta
import json

class SQLConnector(BaseConnector):
    """Base SQL connector that handles common SQL operations.
    """
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the database."""
        pass
    
    @abstractmethod
    def init_db(self) -> None:
        """Initialize the requests table schema."""
        pass
    
    @abstractmethod
    def save_log(self, log: Log) -> int:
        """Save a log entry to the database."""
        pass
    
    @abstractmethod
    def fetch_logs(
        self, 
        filters: Optional[LogFilters] = None,
    ) -> List[Log]:
        """Fetch log entries from the database."""
        pass

    @abstractmethod
    def fetch_log(self, log_id: int) -> Optional[Log]:
        """Fetch a single log entry by ID."""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a query (INSERT, UPDATE, DELETE, DDL)."""
        pass
    
    @abstractmethod
    def query(self, query: str, params: tuple = ()) -> list:
        """Execute a query and return the results (SELECT)."""
        pass
    
    @abstractmethod
    def commit_transaction(self) -> None:
        """Commit the current database transaction."""
        pass
    
    @abstractmethod
    def cleanup(self, retention_options: RetentionOptions) -> int:
        """Clean up old logs based on retention options."""
        pass

