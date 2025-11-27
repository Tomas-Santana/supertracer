from abc import ABC, abstractmethod
from typing import List
from supertracer.types.logs import Log
from datetime import datetime

class BaseConnector(ABC):
    @abstractmethod
    def save_log(self, log: Log) -> None:
        """Save a log entry to the connector's storage."""
        pass

    @abstractmethod
    def fetch_logs(self, limit: int = 100, from_timestamp: datetime = datetime.min) -> List[Log]:
        """Fetch log entries from the connector's storage."""
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
