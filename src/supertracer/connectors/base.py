from abc import ABC, abstractmethod
from typing import List, Optional
from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
from supertracer.types.options import RetentionOptions
from datetime import datetime

class BaseConnector(ABC):
    @abstractmethod
    def save_log(self, log: Log) -> int:
        """Save a log entry to the connector's storage. Returns the log ID."""
        pass

    @abstractmethod
    def fetch_logs(
        self, 
        filters: Optional[LogFilters] = None,
    ) -> List[Log]:
        """Fetch log entries from the connector's storage."""
        pass

    @abstractmethod
    def fetch_log(self, log_id: int) -> Optional[Log]:
        """Fetch a single log entry by ID."""
        pass
      
    @abstractmethod
    def connect(self) -> None:
        """Establish connection a database."""
        pass
      
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to a database."""
        pass
      
    @abstractmethod
    def init_db(self) -> None:
        """Initialize the database schema."""
        pass

    @abstractmethod
    def cleanup(self, retention_options: RetentionOptions) -> int:
        """Clean up old logs based on retention options. Returns number of deleted records."""
        pass
