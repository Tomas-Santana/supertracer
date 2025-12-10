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
    
    def fetch_logs(
        self, 
        limit: int = 100, 
        from_timestamp: datetime = datetime.min,
        search_text: str = None,
        endpoint: str = None,
        status_code: str = None,
        log_level: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        methods: List[str] = None,
        min_latency: int = None,
        max_latency: int = None,
        has_error: bool = False
    ) -> List[Log]:
        """Fetch log entries from the database."""
        # Use a safe minimum timestamp (Unix epoch start or later)
        if from_timestamp == datetime.min:
            timestamp_value = 0.0  # Unix epoch (1970-01-01)
        else:
            timestamp_value = from_timestamp.timestamp()
        
        query = """
            SELECT id, content, timestamp, method, url, headers, log_level, status_code, duration_ms
            FROM logs
            WHERE timestamp >= ?
        """
        params = [timestamp_value]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.timestamp())
            
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.timestamp())

        if search_text:
            query += " AND content LIKE ?"
            params.append(f"%{search_text}%")
            
        if endpoint:
            query += " AND url LIKE ?"
            params.append(f"%{endpoint}%")
            
        if status_code:
            # Handle status code filtering
            # If it's a specific number, exact match
            # If it contains wildcards or partial, use LIKE on string cast
            if status_code.isdigit():
                 query += " AND status_code = ?"
                 params.append(int(status_code))
            else:
                 # Replace X with % for SQL wildcard if user uses 2XX style
                 wildcard_status = status_code.replace('X', '%').replace('x', '%')
                 query += " AND CAST(status_code AS TEXT) LIKE ?"
                 params.append(f"{wildcard_status}%")

        if log_level and log_level != "All Levels":
            query += " AND log_level = ?"
            params.append(log_level)

        if methods and len(methods) > 0:
            placeholders = ','.join(['?'] * len(methods))
            query += f" AND method IN ({placeholders})"
            params.extend(methods)

        if min_latency is not None:
            query += " AND duration_ms >= ?"
            params.append(min_latency)

        if max_latency is not None:
            query += " AND duration_ms <= ?"
            params.append(max_latency)

        if has_error:
            query += " AND status_code >= 400"

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        rows = self.query(query, tuple(params))
        
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
