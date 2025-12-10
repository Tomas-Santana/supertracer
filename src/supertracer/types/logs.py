from typing import Any, Dict, TypedDict, Optional
from datetime import datetime
    
class Log(TypedDict):
    id: int
    content: str
    timestamp: datetime
    method: Optional[str]
    path: Optional[str]
    url: Optional[str]
    headers: Optional[Dict[str, Any]]  # request_headers
    log_level: Optional[str]  # INFO, HTTP, WARN, ERROR, DEBUG
    status_code: Optional[int]  # HTTP response code
    duration_ms: Optional[int]  # Request duration in milliseconds
    client_ip: Optional[str]
    user_agent: Optional[str]
    request_query: Optional[Dict[str, Any]]
    request_body: Optional[Any]
    response_headers: Optional[Dict[str, Any]]
    response_body: Optional[Any]
    response_size_bytes: Optional[int]
    error_message: Optional[str]
    stack_trace: Optional[str]
    stack_trace: Optional[str]
    

    
