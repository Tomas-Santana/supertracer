from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
import threading

from supertracer.connectors.base import BaseConnector
from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
from supertracer.types.options import RetentionOptions

class MemoryConnector(BaseConnector):
    """In-memory implementation of the connector.
    
    Uses a list for storage and a dictionary for O(1) ID lookups.
    Thread-safe using RLock.
    """
    
    def __init__(self):
        self._logs: List[Log] = []
        self._logs_by_id: Dict[int, Log] = {}
        self._next_id: int = 1
        self._lock = threading.RLock()
        
    def connect(self) -> None:
        """Establish connection (no-op for memory)."""
        pass
        
    def disconnect(self) -> None:
        """Close connection (clear data)."""
        with self._lock:
            self._logs.clear()
            self._logs_by_id.clear()
            
    def init_db(self) -> None:
        """Initialize the database (no-op)."""
        pass
        
    def save_log(self, log: Log) -> int:
        """Save a log entry to memory."""
        with self._lock:
            log_id = self._next_id
            self._next_id += 1
            
            # Create a copy to avoid mutation issues and ensure ID is set
            new_log = log.copy()
            new_log['id'] = log_id
            
            # Ensure timestamp is datetime
            if not isinstance(new_log['timestamp'], datetime):
                 if isinstance(new_log['timestamp'], (int, float)):
                     new_log['timestamp'] = datetime.fromtimestamp(new_log['timestamp'])
            
            self._logs.append(new_log)
            self._logs_by_id[log_id] = new_log
            return log_id

    def fetch_logs(self, filters: Optional[LogFilters] = None) -> List[Log]:
        """Fetch log entries from memory with filtering."""
        with self._lock:
            # If no filters, return the last N logs (most recent)
            if not filters:
                # Return reversed slice for most recent first
                return list(reversed(self._logs[-20:]))

            filtered_logs = []
            limit = filters.limit
            
            # Pre-process filters for speed
            start_date = filters.start_date
            end_date = filters.end_date
            search_text = filters.search_text.lower() if filters.search_text else None
            endpoint = filters.endpoint.lower() if filters.endpoint else None
            status_code = filters.status_code
            log_level = filters.log_level
            methods = set(filters.methods) if filters.methods else None
            min_latency = filters.min_latency
            max_latency = filters.max_latency
            has_error = filters.has_error
            
            # Iterate in reverse order (newest first)
            # We assume insertion order roughly correlates with timestamp
            for log in reversed(self._logs):
                # Date filters
                if start_date and log['timestamp'] < start_date:
                    continue
                if end_date and log['timestamp'] >= end_date:
                    continue
                    
                # Text search
                if search_text:
                    content = (log.get('content') or "").lower()
                    if search_text not in content:
                        continue
                        
                # Endpoint
                if endpoint:
                    url = (log.get('url') or "").lower()
                    if endpoint not in url:
                        continue
                        
                # Status Code
                if status_code:
                    log_status = str(log.get('status_code') or "")
                    if status_code.isdigit():
                        if log_status != status_code:
                            continue
                    else:
                        # Handle wildcards like 2XX
                        pattern = status_code.lower().replace('x', '')
                        if not log_status.startswith(pattern):
                            continue

                # Log Level
                if log_level and log_level != 'All Levels':
                    if log.get('log_level') != log_level:
                        continue
                        
                # Methods
                if methods:
                    if log.get('method') not in methods:
                        continue
                        
                # Latency
                duration = log.get('duration_ms') or 0
                if min_latency is not None and duration < min_latency:
                    continue
                if max_latency is not None and duration > max_latency:
                    continue
                    
                # Error
                if has_error:
                    is_error = (log.get('status_code') or 0) >= 400 or bool(log.get('error_message'))
                    if not is_error:
                        continue
                
                filtered_logs.append(log)
                
                if len(filtered_logs) >= limit:
                    break
            
            return filtered_logs

    def fetch_log(self, log_id: int) -> Optional[Log]:
        """Fetch a single log entry by ID."""
        with self._lock:
            return self._logs_by_id.get(log_id)

    def cleanup(self, retention_options: RetentionOptions) -> int:
        """Clean up old logs based on retention options."""
        if not retention_options.enabled:
            return 0
            
        with self._lock:
            initial_count = len(self._logs)
            original_logs = self._logs
            
            # 1. Delete older than X hours
            if retention_options.cleanup_older_than_hours > 0:
                cutoff_time = datetime.now() - timedelta(hours=retention_options.cleanup_older_than_hours)
                self._logs = [log for log in self._logs if log['timestamp'] >= cutoff_time]
                
            # 2. Enforce max_records
            if retention_options.max_records > 0 and len(self._logs) > retention_options.max_records:
                # Keep the last N records
                self._logs = self._logs[-retention_options.max_records:]
                
            # Rebuild index if changed
            if len(self._logs) < initial_count:
                self._logs_by_id = {log['id']: log for log in self._logs}
                
            return initial_count - len(self._logs)
