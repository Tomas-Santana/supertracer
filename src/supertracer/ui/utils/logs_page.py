from supertracer.types.logs import Log
from supertracer.types.filters import LogFilters
from typing import Dict, Any

def match_log_filters(log: Log, filters: LogFilters) -> bool:
    """Checks if a log entry matches the given filters."""
    if filters.search_text:
        if filters.search_text.lower() not in log.get('content', '').lower():
            print("No match for search_text")
            return False
    if filters.endpoint:
        if filters.endpoint not in (log.get('path') or ''):
            print("No match for endpoint")
            return False
    if filters.status_code:
        if log.get('status_code') != filters.status_code:
            print("No match for status_code")
            return False
    if filters.log_level and filters.log_level != "All Levels":
        if log.get('log_level') != filters.log_level:
            print("No match for log_level")
            return False
    if filters.methods:
        if log.get('method') not in filters.methods:
            print("No match for methods")
            return False
    if filters.min_latency is not None:
        if (log.get('duration_ms') or 0) < filters.min_latency:
            print("No match for min_latency")
            return False
    if filters.max_latency is not None:
        if (log.get('duration_ms') or 0) > filters.max_latency:
            print("No match for max_latency")
            return False
    if filters.has_error is not None:
        has_error = bool(log.get('error_message'))
        if has_error != filters.has_error:
            print("No match for has_error")
            return False
    if filters.start_date:
        if log.get('timestamp') and log['timestamp'] < filters.start_date:
            print("No match for start_date")
            return False
    if filters.end_date:
        if log.get('timestamp') and log['timestamp'] > filters.end_date:
            print("No match for end_date")
            return False
    return True
  
def format_log_entry(log: Log) -> Dict[str, Any]:
  """Formats a log entry for display in the logs table."""
  return {
      'id': log.get('id'),
      'timestamp': log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if log.get('timestamp') else '',
      'method': log.get('method') or '',
      'path': log.get('path') or '',
      'status_code': log.get('status_code') or '',
      'log_level': log.get('log_level') or '',
      'duration_ms': log.get('duration_ms') or '',
      'client_ip': log.get('client_ip') or '',
      'error_message': log.get('error_message') or ''
  }
