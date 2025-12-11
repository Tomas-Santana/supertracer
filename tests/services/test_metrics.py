import pytest
from datetime import datetime, timedelta
from time import sleep
from supertracer.services.metrics import MetricsService
from supertracer.types.options import MetricsOptions

@pytest.fixture
def metrics_service():
    options = MetricsOptions(enabled=True, history_limit=100)
    return MetricsService(options=options)

def test_record_request(metrics_service):
    metrics_service.record_request(
        id=1,
        method="GET",
        path="/api/test",
        status_code=200,
        duration_ms=50.0
    )
    
    assert metrics_service.total_requests == 1
    assert len(metrics_service.requests_history) == 1
    assert metrics_service.requests_history[0]['path'] == "/api/test"

def test_record_error(metrics_service):
    metrics_service.record_request(
        id=1,
        method="GET",
        path="/api/error",
        status_code=500,
        duration_ms=10.0,
        error_msg="Internal Server Error"
    )
    
    assert metrics_service.total_errors == 1
    assert len(metrics_service.errors_history) == 1
    assert metrics_service.errors_history[0]['error_msg'] == "Internal Server Error"

def test_summary_stats(metrics_service):
    # Record some requests
    metrics_service.record_request(1, "GET", "/test", 200, 10)
    metrics_service.record_request(2, "POST", "/test", 201, 20)
    metrics_service.record_request(3, "GET", "/error", 500, 30)
    
    stats = metrics_service.get_summary_stats()
    
    assert stats['total_requests'] == 3
    assert stats['total_errors'] == 1
    # Rate calculation depends on time diff, which might be 0 in fast tests
    # Just check keys exist
    assert 'requests_per_min' in stats
    assert 'uptime' in stats

def test_method_distribution(metrics_service):
    metrics_service.record_request(1, "GET", "/1", 200, 10)
    metrics_service.record_request(2, "GET", "/2", 200, 10)
    metrics_service.record_request(3, "POST", "/3", 200, 10)
    
    dist = metrics_service.get_method_distribution()
    
    assert dist['GET'] == 2
    assert dist['POST'] == 1

def test_status_distribution(metrics_service):
    metrics_service.record_request(1, "GET", "/1", 200, 10)
    metrics_service.record_request(2, "GET", "/2", 404, 10)
    metrics_service.record_request(3, "GET", "/3", 500, 10)
    
    dist = metrics_service.get_status_distribution()
    
    assert dist['2xx'] == 1
    assert dist['4xx'] == 1
    assert dist['5xx'] == 1
    assert dist['3xx'] == 0

def test_top_endpoints(metrics_service):
    # 3 requests to /api/popular
    for i in range(3):
        metrics_service.record_request(i, "GET", "/api/popular", 200, 10)
    
    # 1 request to /api/rare
    metrics_service.record_request(4, "GET", "/api/rare", 200, 10)
    
    top = metrics_service.get_top_endpoints(limit=2)
    
    assert len(top) == 2
    assert top[0]['path'] == "/api/popular"
    assert top[0]['count'] == 3
    assert top[1]['path'] == "/api/rare"
    assert top[1]['count'] == 1

def test_slow_endpoints(metrics_service):
    # Fast endpoint
    metrics_service.record_request(1, "GET", "/fast", 200, 10)
    metrics_service.record_request(2, "GET", "/fast", 200, 20) # Avg 15
    
    # Slow endpoint
    metrics_service.record_request(3, "GET", "/slow", 200, 100)
    metrics_service.record_request(4, "GET", "/slow", 200, 200) # Avg 150
    
    slow = metrics_service.get_slow_endpoints(limit=2)
    
    assert len(slow) == 2
    assert slow[0]['path'] == "/slow"
    assert slow[0]['avg_latency'] == 150.0
    assert slow[1]['path'] == "/fast"
    assert slow[1]['avg_latency'] == 15.0

def test_history_limit(metrics_service):
    # Set small limit for testing
    metrics_service.history_limit = 5
    metrics_service.requests_history = metrics_service.requests_history.__class__(maxlen=5)
    
    for i in range(10):
        metrics_service.record_request(i, "GET", "/test", 200, 10)
        
    assert len(metrics_service.requests_history) == 5
    # Should have the last 5 (ids 5-9)
    assert metrics_service.requests_history[0]['id'] == 5
    assert metrics_service.requests_history[-1]['id'] == 9

def test_disabled_metrics():
    options = MetricsOptions(enabled=False)
    service = MetricsService(options=options)
    
    service.record_request(1, "GET", "/test", 200, 10)
    
    assert service.total_requests == 0
    assert len(service.requests_history) == 0
