import sqlite3
from supertracer.connectors.sql import SQLConnector


class SQLiteConnector(SQLConnector):
    """SQLite implementation of the SQL connector."""
    
    def __init__(self, db_path: str = "supertracer.db"):
        super().__init__()
        self.db_path = db_path
        
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
        """Establish connection to the SQLite database."""
        self.connection = sqlite3.connect(
            self.db_path, 
            check_same_thread=False  # Allow usage across multiple threads
        )
        self.cursor = self.connection.cursor()
    
    def disconnect(self) -> None:
        """Close connection to the SQLite database."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
