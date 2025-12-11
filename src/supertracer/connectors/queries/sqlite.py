
CREATE_TABLE = """
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
  );
"""

INSERT_LOG = """
    INSERT INTO requests (
        content, timestamp, method, path, url, headers, log_level, status_code, duration_ms,
        client_ip, user_agent, request_query, request_body, response_headers, response_body,
        response_size_bytes, error_message, stack_trace
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
"""

FETCH_LOGS_BASE = """
    SELECT 
        id, content, timestamp, method, path, url, log_level, status_code, duration_ms, error_message
    FROM requests
    WHERE timestamp >= ?
"""

FETCH_LOG_BY_ID = """
    SELECT 
        id, content, timestamp, method, path, url, headers, log_level, status_code, duration_ms,
        client_ip, user_agent, request_query, request_body, response_headers, response_body,
        response_size_bytes, error_message, stack_trace
    FROM requests
    WHERE id = ?
"""

CLEANUP_OLDER_THAN = "DELETE FROM requests WHERE timestamp < ?"

CLEANUP_MAX_RECORDS = """
    DELETE FROM requests 
    WHERE id NOT IN (
        SELECT id FROM requests ORDER BY timestamp DESC, id DESC LIMIT ?
    )
"""
