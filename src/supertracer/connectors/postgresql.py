import psycopg2
from supertracer.connectors.sql import SQLConnector


class PostgreSQLConnector(SQLConnector):
    """PostgreSQL implementation of the SQL connector."""
    
    def __init__(
        self, 
        host: str = "localhost",
        port: int = 5432,
        database: str = "supertracer",
        user: str = "postgres",
        password: str = ""
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
    
    def init_db(self) -> None:
        """Initialize the logs table schema with PostgreSQL-specific syntax."""
        create_table_query = """
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL,
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
    
    def save_log(self, log) -> None:
        """Save a log entry using PostgreSQL parameterized queries."""
        from datetime import datetime
        import json
        
        insert_query = """
            INSERT INTO logs (content, timestamp, method, url, headers, log_level, status_code, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
        from_timestamp=None,
        search_text: str = None,
        endpoint: str = None,
        status_code: str = None,
        log_level: str = None,
        start_date=None,
        end_date=None
    ):
        """Fetch log entries using PostgreSQL parameterized queries."""
        from datetime import datetime
        import json
        
        if from_timestamp is None:
            from_timestamp = datetime.min
            
        timestamp_value = from_timestamp.timestamp()
        
        query = """
            SELECT id, content, timestamp, method, url, headers, log_level, status_code, duration_ms
            FROM logs
            WHERE timestamp >= %s
        """
        params = [timestamp_value]

        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date.timestamp())
            
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date.timestamp())

        if search_text:
            query += " AND content ILIKE %s"
            params.append(f"%{search_text}%")
            
        if endpoint:
            query += " AND url ILIKE %s"
            params.append(f"%{endpoint}%")
            
        if status_code:
            if status_code.isdigit():
                 query += " AND status_code = %s"
                 params.append(int(status_code))
            else:
                 wildcard_status = status_code.replace('X', '%').replace('x', '%')
                 query += " AND CAST(status_code AS TEXT) LIKE %s"
                 params.append(f"{wildcard_status}%")

        if log_level and log_level != "All Levels":
            query += " AND log_level = %s"
            params.append(log_level)

        query += " ORDER BY id DESC LIMIT %s"
        params.append(limit)
        
        rows = self.query(query, tuple(params))
        
        logs = []
        for row in rows:
            log = {
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
    
    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute a query without returning results (INSERT, UPDATE, DELETE, DDL)."""
        self.cursor.execute(query, params)
    
    def query(self, query: str, params: tuple = ()) -> list:
        """Execute a query and return the results (SELECT)."""
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def commit_transaction(self) -> None:
        """Commit the current database transaction."""
        self.connection.commit()
    
    def connect(self) -> None:
        """Establish connection to the PostgreSQL database."""
        self.connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
        self.cursor = self.connection.cursor()
    
    def disconnect(self) -> None:
        """Close connection to the PostgreSQL database."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
