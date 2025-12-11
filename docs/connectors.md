# Connectors

Connectors are the bridge between SuperTracer and your storage backend. They handle saving logs, retrieving them for the dashboard, and performing cleanup tasks.

SuperTracer comes with three built-in connectors:

- [MemoryConnector](#memoryconnector) (Default)
- [SQLiteConnector](#sqliteconnector)
- [PostgreSQLConnector](#postgresqlconnector)

You can also [create your own connector](#creating-a-custom-connector) to support other databases or storage services.

---

## Built-in Connectors

### MemoryConnector

The `MemoryConnector` stores logs in a Python list in memory. It is the default connector if none is specified.

**Pros:**
- Zero configuration.
- Very fast.
- No external dependencies.

**Cons:**
- Logs are lost when the application restarts.
- Not suitable for production with high traffic or long retention needs.

**Usage:**

```python
from supertracer import SuperTracer, MemoryConnector

# Explicitly using MemoryConnector (same as default)
tracer = SuperTracer(app, connector=MemoryConnector())
```

### SQLiteConnector

The `SQLiteConnector` stores logs in a local SQLite database file.

**Pros:**
- Persistent storage.
- No separate database server required.
- Good for development and small to medium applications.

**Cons:**
- File-based locking can limit concurrency in very high-traffic apps.

**Usage:**

```python
from supertracer import SuperTracer, SQLiteConnector

# Stores logs in 'requests.db' in the current directory
connector = SQLiteConnector(db_path="requests.db")
tracer = SuperTracer(app, connector=connector)
```

### PostgreSQLConnector

The `PostgreSQLConnector` stores logs in a PostgreSQL database.

**Pros:**
- High performance and concurrency.
- Scalable for production workloads.
- Robust data integrity.
- Supports SSL connections.

**Cons:**
- Requires a running PostgreSQL server.
- Requires `psycopg2` (installed automatically with supertracer).

**Usage:**

```python
from supertracer import SuperTracer, PostgreSQLConnector

# Using a connection string
connector = PostgreSQLConnector(
    host="localhost",
    port=5432,
    database="supertracer_db",
    user="your_username",
    password="your_password",
    sslmode="prefer"
)

tracer = SuperTracer(app, connector=connector)
```

---

## Creating a Custom Connector

To create a custom connector, you need to inherit from the `BaseConnector` class and implement its abstract methods.

### 1. Import BaseConnector

```python
from supertracer import BaseConnector, Log, LogFilters, RetentionOptions
from typing import List, Optional
```

### 2. Implement the Class

```python
class MyCustomConnector(BaseConnector):
    def __init__(self, connection_info: str):
        self.connection_info = connection_info
        # Initialize your client here

    def connect(self) -> None:
        """Establish connection to the storage backend."""
        print(f"Connecting to {self.connection_info}...")

    def disconnect(self) -> None:
        """Close connection."""
        print("Disconnecting...")

    def init_db(self) -> None:
        """Initialize tables or collections if they don't exist."""
        # e.g., CREATE TABLE IF NOT EXISTS...
        pass

    def save_log(self, log: Log) -> int:
        """Save a log entry and return its ID."""
        # Save 'log' dictionary to your storage
        # Return the new ID
        return 123

    def fetch_logs(self, filters: Optional[LogFilters] = None) -> List[Log]:
        """Fetch logs matching the filters."""
        # Query your storage based on 'filters'
        return []

    def fetch_log(self, log_id: int) -> Optional[Log]:
        """Fetch a single log by ID."""
        # Return the log dict or None
        return None

    def cleanup(self, retention_options: RetentionOptions) -> int:
        """Delete old logs based on retention options."""
        # Implement cleanup logic
        return 0
```

### 3. Use Your Connector

```python
from supertracer import SuperTracer

my_connector = MyCustomConnector("my-db-host")
tracer = SuperTracer(app, connector=my_connector)
```
