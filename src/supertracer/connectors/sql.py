from abc import abstractmethod
from typing import Any, List, Optional
from supertracer.connectors.base import BaseConnector
from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
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
        filters: Optional[LogFilters] = None,
    ) -> List[Log]:
        """Fetch log entries from the database."""
        # Use a safe minimum timestamp (Unix epoch start or later)
        filters = filters or LogFilters()
        if filters.start_date == datetime.min:
            timestamp_value = 0.0  # Unix epoch (1970-01-01)
        else:
            timestamp_value = filters.start_date.timestamp() if filters and filters.start_date else 0.0
        select_query = """
            SELECT 
                id, content, timestamp, method, path, url, log_level, status_code, duration_ms, error_message
            FROM requests
            WHERE timestamp >= ?
        """
        params: List = [timestamp_value]

        if filters.end_date:
            select_query += " AND timestamp < ?"
            params.append(filters.end_date.timestamp())

        if filters.search_text:
            select_query += " AND content LIKE ?"
            params.append(f"%{filters.search_text}%")
            
        if filters.endpoint:
            select_query += " AND url LIKE ?"
            params.append(f"%{filters.endpoint}%")
            
        if filters.status_code:
            # Handle status code filtering
            # If it's a specific number, exact match
            # If it contains wildcards or partial, use LIKE on string cast
            if filters.status_code.isdigit():
                select_query += " AND status_code = ?"
                params.append(int(filters.status_code))
            else:
                # Handle 2XX, 4XX etc or partial matches
                pattern = filters.status_code.replace('X', '_').replace('x', '_')
                select_query += " AND CAST(status_code AS TEXT) LIKE ?"
                params.append(pattern)

        if filters.log_level and filters.log_level != 'All Levels':
            select_query += " AND log_level = ?"
            params.append(filters.log_level)
            
        if filters.methods:
            placeholders = ','.join(['?'] * len(filters.methods))
            select_query += f" AND method IN ({placeholders})"
            params.extend(filters.methods)
            
        if filters.min_latency is not None:
            select_query += " AND duration_ms >= ?"
            params.append(filters.min_latency)
            
        if filters.max_latency is not None:
            select_query += " AND duration_ms <= ?"
            params.append(filters.max_latency)
            
        if filters.has_error:
            select_query += " AND (status_code >= 400 OR error_message IS NOT NULL)"

        select_query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(filters.limit)
        
        rows = self.query(select_query, tuple(params))
        logs: List[Log] = []
        for row in rows:
            log: Log = {
                'id': row[0],
                'content': row[1] or "",
                'timestamp': datetime.fromtimestamp(row[2]),
                'method': row[3],
                'path': row[4],
                'url': row[5],
                'headers': None,
                'log_level': row[6],
                'status_code': row[7],
                'duration_ms': row[8],
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
