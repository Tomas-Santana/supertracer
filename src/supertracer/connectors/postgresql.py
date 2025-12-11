import psycopg2
import json
from datetime import datetime, timedelta
from typing import List, Optional, Any, Literal
from supertracer.connectors.sql import SQLConnector
from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
from supertracer.types.options import RetentionOptions
from supertracer.connectors.queries import postgresql as queries
import os

class PostgreSQLConnector(SQLConnector):
    """PostgreSQL implementation of the SQL connector.

    Args:
        host (str): Database host address.
        port (int): Database port number.
        database (str): Database name.
        user (str): Database user.
        password (str): Database user's password.
        sslmode (str): SSL mode for the connection.
    """
    
    def __init__(
        self, 
        host: str = "localhost",
        port: int = 5432,
        database: str = "supertracer",
        user: str = "postgres",
        password: str = "",
        sslmode: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] = "prefer"
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.sslmode = sslmode
        self.connection = None
        self.cursor = None
    
    def connect(self) -> None:
        """Establish connection to the PostgreSQL database."""
        self.connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            sslmode=self.sslmode
        )
        self.cursor = self.connection.cursor()
    
    def disconnect(self) -> None:
        """Close connection to the PostgreSQL database."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a query without returning results (INSERT, UPDATE, DELETE, DDL)."""
        if self.cursor is None:
            raise ConnectionError("Database is not connected")
            
        self.cursor.execute(query, params)
        # For INSERTs that return ID, we need to fetch it
        if query.strip().upper().startswith("INSERT") and "RETURNING" in query.upper():
            result = self.cursor.fetchone()
            return result[0] if result else None
        return None
    
    def query(self, query: str, params: tuple = ()) -> list:
        """Execute a query and return the results (SELECT)."""
        if self.cursor is None:
            raise ConnectionError("Database is not connected")
            
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def commit_transaction(self) -> None:
        """Commit the current database transaction."""
        if self.connection is None:
            raise ConnectionError("Database is not connected")
        self.connection.commit()

    def cleanup(self, retention_options: RetentionOptions) -> int:
        """Clean up old logs based on retention options using PostgreSQL syntax."""
        if not retention_options.enabled:
            return 0
            
        deleted_count = 0
        
        # 1. Delete older than X hours
        if retention_options.cleanup_older_than_hours > 0:
            cutoff_time = datetime.now() - timedelta(hours=retention_options.cleanup_older_than_hours)
            timestamp_val = cutoff_time.timestamp()
            
            self.execute(queries.CLEANUP_OLDER_THAN, (timestamp_val,))
            self.commit_transaction()
            
        # 2. Enforce max_records
        if retention_options.max_records > 0:
            # PostgreSQL syntax for keeping top N records
            self.execute(queries.CLEANUP_MAX_RECORDS, (retention_options.max_records,))
            self.commit_transaction()
            
        return deleted_count

    def init_db(self) -> None:
        """Initialize the requests table schema with PostgreSQL-specific syntax."""
        # Create table if not exists
        self.execute(queries.CREATE_TABLE)
        self.commit_transaction()
    
    def save_log(self, log: Log) -> int:
        """Save a log entry using PostgreSQL parameterized queries."""
        
        # Convert datetime to timestamp
        timestamp = log['timestamp'].timestamp() if isinstance(log['timestamp'], datetime) else log['timestamp']
        
        def to_json(val):
            return json.dumps(val) if val is not None else None
        
        log_id = self.execute(
            queries.INSERT_LOG,
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
        return log_id
    
    def fetch_logs(self, filters: Optional[LogFilters] = None) -> List[Log]:
        """Fetch log entries using PostgreSQL parameterized queries."""
        filters = filters or LogFilters()
        
        if filters.start_date == datetime.min:
            timestamp_value = 0.0
        else:
            timestamp_value = filters.start_date.timestamp() if filters and filters.start_date else 0.0
        
        query = queries.FETCH_LOGS_BASE
        params: List = [timestamp_value]

        if filters.end_date:
            query += " AND timestamp < %s"
            params.append(filters.end_date.timestamp())

        if filters.search_text:
            query += " AND content ILIKE %s"
            params.append(f"%{filters.search_text}%")
            
        if filters.endpoint:
            query += " AND url ILIKE %s"
            params.append(f"%{filters.endpoint}%")
            
        if filters.status_code:
            if filters.status_code.isdigit():
                 query += " AND status_code = %s"
                 params.append(int(filters.status_code))
            else:
                 wildcard_status = filters.status_code.replace('X', '_').replace('x', '_')
                 query += " AND CAST(status_code AS TEXT) LIKE %s"
                 params.append(wildcard_status)

        if filters.log_level and filters.log_level != "All Levels":
            query += " AND log_level = %s"
            params.append(filters.log_level)

        if filters.methods:
            query += " AND method IN %s"
            params.append(tuple(filters.methods))
            
        if filters.min_latency is not None:
            query += " AND duration_ms >= %s"
            params.append(filters.min_latency)
            
        if filters.max_latency is not None:
            query += " AND duration_ms <= %s"
            params.append(filters.max_latency)
            
        if filters.has_error:
            query += " AND (status_code >= 400 OR error_message IS NOT NULL)"

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(filters.limit)
        
        rows = self.query(query, tuple(params))
        
        logs = []
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
                'error_message': row[9],
                'stack_trace': None
            }
            logs.append(log)
        
        return logs

    def fetch_log(self, log_id: int) -> Optional[Log]:
        """Fetch a single log entry by ID."""
        
        rows = self.query(queries.FETCH_LOG_BY_ID, (log_id,))
        
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
