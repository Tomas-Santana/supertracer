import pytest
from datetime import datetime, timedelta
from supertracer.connectors.memory import MemoryConnector
from supertracer.connectors.sqlite import SQLiteConnector
from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
from supertracer.types.options import RetentionOptions

# Fixture to run tests against multiple connector implementations
@pytest.fixture(params=["memory", "sqlite"])
def connector(request):
    conn = None
    if request.param == "memory":
        conn = MemoryConnector()
        conn.connect() # No-op but good to call
    elif request.param == "sqlite":
        # Use in-memory SQLite database for testing
        conn = SQLiteConnector(db_path=":memory:")
        conn.connect()
        conn.init_db()
    
    assert conn is not None, "Connector should be initialized"
    
    yield conn 
    
    conn.disconnect() 

def create_sample_log(
    content="Test log", 
    level="INFO", 
    status=200, 
    method="GET", 
    timestamp=None
) -> Log:
    if timestamp is None:
        timestamp = datetime.now()
        
    return {
        "id": 0, # Will be ignored/overwritten by connector
        "content": content,
        "timestamp": timestamp,
        "method": method,
        "path": "/test",
        "url": "http://localhost/test",
        "headers": {"content-type": "application/json"},
        "log_level": level,
        "status_code": status,
        "duration_ms": 100,
        "client_ip": "127.0.0.1",
        "user_agent": "pytest",
        "request_query": {},
        "request_body": {},
        "response_headers": {},
        "response_body": {},
        "response_size_bytes": 100,
        "error_message": None,
        "stack_trace": None
    }

def test_save_and_fetch_log(connector):
    log = create_sample_log(content="Unique Content 123")
    log_id = connector.save_log(log)
    
    assert log_id is not None
    
    fetched_log = connector.fetch_log(log_id)
    assert fetched_log is not None
    assert fetched_log["content"] == "Unique Content 123"
    assert fetched_log["id"] == log_id
    # Check timestamp preservation (allowing for small precision loss in DBs)
    assert abs((fetched_log["timestamp"] - log["timestamp"]).total_seconds()) < 1.0

def test_fetch_logs_pagination(connector):
    # Create 5 logs
    for i in range(5):
        connector.save_log(create_sample_log(content=f"Log {i}"))
        
    # Fetch all
    filters = LogFilters(limit=10)
    logs = connector.fetch_logs(filters)
    assert len(logs) == 5
    
    # Fetch limit 2
    filters = LogFilters(limit=2)
    logs = connector.fetch_logs(filters)
    assert len(logs) == 2
    # Should be the most recent ones (Log 4 and Log 3)
    assert "Log 4" in logs[0]["content"]

def test_fetch_logs_filtering(connector):
    connector.save_log(create_sample_log(content="Error occurred", level="ERROR", status=500))
    connector.save_log(create_sample_log(content="Success operation", level="INFO", status=200))
    
    # Filter by level
    filters = LogFilters(log_level="ERROR")
    logs = connector.fetch_logs(filters)
    assert len(logs) == 1
    assert logs[0]["log_level"] == "ERROR"
    
    # Filter by status code
    filters = LogFilters(status_code="200")
    logs = connector.fetch_logs(filters)
    assert len(logs) == 1
    assert logs[0]["status_code"] == 200
    
    # Filter by search text
    filters = LogFilters(search_text="Success")
    logs = connector.fetch_logs(filters)
    assert len(logs) == 1
    assert "Success" in logs[0]["content"]

def test_cleanup_max_records(connector):
    # Create 10 logs
    for i in range(10):
        connector.save_log(create_sample_log(content=f"Log {i}"))
        
    # Set retention to keep only 5
    options = RetentionOptions(
        enabled=True,
        max_records=5,
        cleanup_older_than_hours=0,
        cleanup_interval_minutes=60
    )
    
    connector.cleanup(options)
    
    logs = connector.fetch_logs(LogFilters(limit=100))
    assert len(logs) == 5
    # Should keep the newest ones (5-9)
    contents = [l["content"] for l in logs]
    assert "Log 9" in contents
    assert "Log 0" not in contents

def test_cleanup_older_than(connector):
    old_date = datetime.now() - timedelta(hours=25)
    new_date = datetime.now()
    
    connector.save_log(create_sample_log(content="Old Log", timestamp=old_date))
    connector.save_log(create_sample_log(content="New Log", timestamp=new_date))
    
    # Set retention to delete older than 24 hours
    options = RetentionOptions(
        enabled=True,
        max_records=0,
        cleanup_older_than_hours=24,
        cleanup_interval_minutes=60
    )
    
    connector.cleanup(options)
    
    logs = connector.fetch_logs(LogFilters(limit=100))
    assert len(logs) == 1
    assert logs[0]["content"] == "New Log"
