from collections import deque, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Deque
import statistics

from supertracer.types.options import MetricsOptions
from supertracer.types.metrics import (
    MetricRecord, SummaryStats, TimelineData, PerformanceData, 
    EndpointCount, EndpointLatency, MethodDistribution, StatusDistribution
)

class MetricsService:
    def __init__(self, options: Optional[MetricsOptions] = None):
        self.options = options or {}
        self.history_limit = self.options.get('history_limit', 1000)
        self.enabled = self.options.get('enabled', True)
        
        # In-memory storage
        self.requests_history: Deque[MetricRecord] = deque(maxlen=self.history_limit)
        self.errors_history: Deque[MetricRecord] = deque(maxlen=5) # Keep last 5 errors
        
        # Aggregated counters (lifetime of the process)
        self.total_requests = 0
        self.total_errors = 0
        self.start_time = datetime.now()
        
        # Helper for top endpoints
        self.endpoint_counts: Counter[str] = Counter()
        self.endpoint_latencies: Dict[str, List[float]] = {}

    def record_request(self, id: int, method: str, path: str, status_code: int, duration_ms: float, error_msg: Optional[str] = None):
        if not self.enabled:
            return

        now = datetime.now()
        
        record: MetricRecord = {
            "id": id,
            'timestamp': now,
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'error_msg': error_msg
        }
        
        self.requests_history.append(record)
        self.total_requests += 1
        
        self.endpoint_counts[path] += 1
        if path not in self.endpoint_latencies:
            self.endpoint_latencies[path] = []
        self.endpoint_latencies[path].append(duration_ms)
        # Keep latency history per endpoint limited to avoid memory leak if not using deque there
        # For simplicity, let's just keep last 100 latencies per endpoint for avg calc
        if len(self.endpoint_latencies[path]) > 100:
            self.endpoint_latencies[path].pop(0)

        if status_code >= 400:
            self.total_errors += 1
            if error_msg or status_code >= 500:
                 self.errors_history.append(record)

    def get_summary_stats(self) -> SummaryStats:
        now = datetime.now()
        uptime = now - self.start_time
        
        # Calculate rate (requests per minute) based on recent history
        if len(self.requests_history) > 1:
            oldest = self.requests_history[0]['timestamp']
            time_diff = (now - oldest).total_seconds() / 60.0
            rate = len(self.requests_history) / time_diff if time_diff > 0 else 0
        else:
            rate = 0

        return {
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'requests_per_min': round(rate, 2),
            'uptime': str(uptime).split('.')[0] # Format HH:MM:SS
        }

    def get_method_distribution(self) -> MethodDistribution:
        counts = Counter(r['method'] for r in self.requests_history)
        return dict(counts)

    def get_status_distribution(self) -> StatusDistribution:
        # Group by 2xx, 3xx, 4xx, 5xx
        dist = {'2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0, 'Other': 0}
        for r in self.requests_history:
            code = r['status_code']
            if 200 <= code < 300: dist['2xx'] += 1
            elif 300 <= code < 400: dist['3xx'] += 1
            elif 400 <= code < 500: dist['4xx'] += 1
            elif 500 <= code < 600: dist['5xx'] += 1
            else: dist['Other'] += 1
        return dist

    def get_timeline_data(self) -> TimelineData:
        # Group requests (and errors) by minute for the last hour (or based on history)
        if not self.requests_history:
            return {'times': [], 'counts': [], 'error_counts': []}

        buckets: Dict[str, int] = {}
        error_buckets: Dict[str, int] = {}

        for r in self.requests_history:
            ts = r['timestamp'].strftime('%H:%M')
            buckets[ts] = buckets.get(ts, 0) + 1
            if r['status_code'] >= 400:
                error_buckets[ts] = error_buckets.get(ts, 0) + 1
            else:
                error_buckets.setdefault(ts, 0)
            
        sorted_times = sorted(buckets.keys())
        return {
            'times': sorted_times,
            'counts': [buckets.get(t, 0) for t in sorted_times],
            'error_counts': [error_buckets.get(t, 0) for t in sorted_times]
        }

    def get_performance_data(self) -> PerformanceData:
        # Average latency over time (bucketed by minute)
        if not self.requests_history:
            return {'times': [], 'latencies': []}

        buckets: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        
        for r in self.requests_history:
            ts = r['timestamp'].strftime('%H:%M')
            buckets[ts] = buckets.get(ts, 0) + r['duration_ms']
            counts[ts] = counts.get(ts, 0) + 1
            
        sorted_times = sorted(buckets.keys())
        return {
            'times': sorted_times,
            'latencies': [round(buckets[t] / counts[t], 2) for t in sorted_times]
        }

    def get_top_endpoints(self, limit=5) -> List[EndpointCount]:
        # Return list of {path, count}
        return [{'path': path, 'count': count} for path, count in self.endpoint_counts.most_common(limit)]

    def get_slow_endpoints(self, limit=5) -> List[EndpointLatency]:
        # Calculate avg latency for each endpoint
        avgs = []
        for path, latencies in self.endpoint_latencies.items():
            if latencies:
                avg = sum(latencies) / len(latencies)
                avgs.append({'path': path, 'avg_latency': round(avg, 2)})
        
        # Sort by latency desc
        return sorted(avgs, key=lambda x: x['avg_latency'], reverse=True)[:limit]

    def get_recent_errors(self, limit=10) -> List[MetricRecord]:
        # Return last N errors
        # Convert deque to list, reverse to get newest first, slice
        errors = list(self.errors_history)
        errors.reverse()
        return errors[:limit]
