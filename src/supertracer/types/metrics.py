from typing import TypedDict, List, Optional, Dict
from datetime import datetime

class MetricRecord(TypedDict):
    timestamp: datetime
    method: str
    path: str
    status_code: int
    duration_ms: float
    error_msg: Optional[str]

class SummaryStats(TypedDict):
    total_requests: int
    total_errors: int
    requests_per_min: float
    uptime: str

class TimelineData(TypedDict, total=False):
    times: List[str]
    counts: List[int]

class PerformanceData(TypedDict, total=False):
    times: List[str]
    latencies: List[float]

class EndpointCount(TypedDict):
    path: str
    count: int

class EndpointLatency(TypedDict):
    path: str
    avg_latency: float

MethodDistribution = Dict[str, int]
StatusDistribution = Dict[str, int]
