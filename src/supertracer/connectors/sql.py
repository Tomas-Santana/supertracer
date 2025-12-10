from abc import abstractmethod
from typing import Any, List, Optional
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
        """Initialize the requests table schema."""
        create_table_query = """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                timestamp REAL NOT NULL,
                method TEXT,
                path TEXT,
                url TEXT,
                headers TEXT,
                log_level TEXT,
                status_code INTEGER,
                duration_ms INTEGER,
                client_ip TEXT,
                user_agent TEXT,
                request_query TEXT,
                request_body TEXT,
                response_headers TEXT,
                response_body TEXT,
                response_size_bytes INTEGER,
                error_message TEXT,
                stack_trace TEXT
            )
        """
        self.execute(create_table_query)
        self.commit_transaction()
    
    def save_log(self, log: Log) -> int:
        """Save a log entry to the database."""
        insert_query = """
            INSERT INTO requests (
                content, timestamp, method, path, url, headers, log_level, status_code, duration_ms,
                client_ip, user_agent, request_query, request_body, response_headers, response_body,
                response_size_bytes, error_message, stack_trace
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """
        
        # Convert datetime to timestamp
        timestamp = log['timestamp'].timestamp() if isinstance(log['timestamp'], datetime) else log['timestamp']
        
        # Serialize JSON fields
        def to_json(val):
            return json.dumps(val) if val is not None else None

        res = self.execute(
            insert_query,
            (
                log.get('content'),
                timestamp,
                log.get('method'),
                log.get('path'),
                log.get('url'),
                to_json(log.get('headers')),
                log.get('log_level'),
                log.get('status_code'),
                log.get('duration_ms'),
                log.get('client_ip'),
                log.get('user_agent'),
                to_json(log.get('request_query')),
                to_json(log.get('request_body')),
                to_json(log.get('response_headers')),
                to_json(log.get('response_body')),
                log.get('response_size_bytes'),
                log.get('error_message'),
                log.get('stack_trace')
            )
        )
        self.commit_transaction()
        return res
    
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
        select_query = """
            SELECT 
                id, content, timestamp, method, path, url, headers, log_level, status_code, duration_ms,
                client_ip, user_agent, request_query, request_body, response_headers, response_body,
                response_size_bytes, error_message, stack_trace
            FROM requests
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
                'content': row[1] or "",
                'timestamp': datetime.fromtimestamp(row[2]),
                'method': row[3],
                'path': row[4],
                'url': row[5],
                'headers': json.loads(row[6]) if row[6] else None,
                'log_level': row[7],
                'status_code': row[8],
                'duration_ms': row[9],
                'client_ip': row[10],
                'user_agent': row[11],
                'request_query': json.loads(row[12]) if row[12] else None,
                'request_body': json.loads(row[13]) if row[13] else None,
                'response_headers': json.loads(row[14]) if row[14] else None,
                'response_body': json.loads(row[15]) if row[15] else None,
                'response_size_bytes': row[16],
                'error_message': row[17],
                'stack_trace': row[18]
            }
            logs.append(log)
        
        return logs

    def fetch_log(self, log_id: int) -> Optional[Log]:
        """Fetch a single log entry by ID."""
        select_query = """
            SELECT 
                id, content, timestamp, method, path, url, headers, log_level, status_code, duration_ms,
                client_ip, user_agent, request_query, request_body, response_headers, response_body,
                response_size_bytes, error_message, stack_trace
            FROM requests
            WHERE id = ?
        """
        
        rows = self.query(select_query, (log_id,))
        
        if not rows:
            return None
            
        row = rows[0]
        log: Log = {
            'id': row[0],
            'content': row[1] or "",
            'timestamp': datetime.fromtimestamp(row[2]),
            'method': row[3],
            'path': row[4],
            'url': row[5],
            'headers': json.loads(row[6]) if row[6] else None,
            'log_level': row[7],
            'status_code': row[8],
            'duration_ms': row[9],
            'client_ip': row[10],
            'user_agent': row[11],
            'request_query': json.loads(row[12]) if row[12] else None,
            'request_body': json.loads(row[13]) if row[13] else None,
            'response_headers': json.loads(row[14]) if row[14] else None,
            'response_body': json.loads(row[15]) if row[15] else None,
            'response_size_bytes': row[16],
            'error_message': row[17],
            'stack_trace': row[18]
        }
        return log
    
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
