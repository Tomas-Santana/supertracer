from typing import Any, Dict, TypedDict, Optional
from datetime import datetime
    
class Log(TypedDict):
    id: int
    content: str
    timestamp: datetime
    method: Optional[str]
    url: Optional[str]
    headers: Optional[Dict[str, Any]]
    log_level: Optional[str]  # INFO, HTTP, WARN, ERROR, DEBUG
    status_code: Optional[int]  # HTTP response code
    duration_ms: Optional[int]  # Request duration in milliseconds
    

    
