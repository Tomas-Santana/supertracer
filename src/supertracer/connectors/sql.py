from abc import abstractmethod
from typing import List, Any
from supertracer.connectors.base import BaseConnector
from supertracer.types.logs import Log
from datetime import datetime
import json


class SQLConnector(BaseConnector):
    """Base SQL connector that handles common SQL operations.
    
    Child classes only need to implement:
    - get_connection_string() or connection setup
    - connect()
    - disconnect()
    """
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the database."""
        pass
    
    def init_db(self) -> None:
        """Initialize the logs table schema."""
        create_table_query = """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                method TEXT,
                url TEXT,
                headers TEXT,
                log_level TEXT,
                status_code INTEGER,
                duration_ms INTEGER
            )
        """
        self.execute(create_table_query)
        self.commit_transaction()
    
    def save_log(self, log: Log) -> None:
        """Save a log entry to the database."""
        insert_query = """
            INSERT INTO logs (content, timestamp, method, url, headers, log_level, status_code, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Convert datetime to timestamp
        timestamp = log['timestamp'].timestamp() if isinstance(log['timestamp'], datetime) else log['timestamp']
        
        # Serialize headers to JSON string
        headers_json = json.dumps(log.get('headers')) if log.get('headers') else None
        
        self.execute(
            insert_query,
            (
                log['content'],
                timestamp,
                log.get('method'),
                log.get('url'),
                headers_json,
                log.get('log_level'),
                log.get('status_code'),
                log.get('duration_ms')
            )
        )
        self.commit_transaction()
    
    def fetch_logs(self, limit: int = 100, from_timestamp: datetime = datetime.min) -> List[Log]:
        """Fetch log entries from the database."""
        # Use a safe minimum timestamp (Unix epoch start or later)
        if from_timestamp == datetime.min:
            timestamp_value = 0.0  # Unix epoch (1970-01-01)
        else:
            timestamp_value = from_timestamp.timestamp()
        
        select_query = """
            SELECT id, content, timestamp, method, url, headers, log_level, status_code, duration_ms
            FROM logs
            WHERE timestamp >= ?
            ORDER BY id DESC
            LIMIT ?
        """
        
        rows = self.query(select_query, (timestamp_value, limit))
        
        logs: List[Log] = []
        for row in rows:
            log: Log = {
                'id': row[0],
                'content': row[1],
                'timestamp': datetime.fromtimestamp(row[2]),
                'method': row[3],
                'url': row[4],
                'headers': json.loads(row[5]) if row[5] else None,
                'log_level': row[6],
                'status_code': row[7],
                'duration_ms': row[8]
            }
            logs.append(log)
        
        return logs
    
    @abstractmethod
    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute a query without returning results (INSERT, UPDATE, DELETE, DDL)."""
        pass
    
    @abstractmethod
    def query(self, query: str, params: tuple = ()) -> list:
        """Execute a query and return the results (SELECT)."""
        pass
    
    @abstractmethod
    def commit_transaction(self) -> None:
        """Commit the current database transaction."""
        pass
