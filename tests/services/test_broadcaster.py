import pytest
from unittest.mock import Mock
from supertracer.services.broadcaster import LogBroadcaster
from supertracer.types.logs import Log

@pytest.fixture
def broadcaster():
    return LogBroadcaster()

@pytest.fixture
def sample_log():
    return {
        "id": 1,
        "content": "Test Log",
        "timestamp": "2023-01-01T00:00:00",
    }

def test_subscribe(broadcaster, sample_log):
    callback = Mock()
    broadcaster.subscribe(callback)
    
    broadcaster.broadcast(sample_log)
    
    callback.assert_called_once_with(sample_log)

def test_unsubscribe(broadcaster, sample_log):
    callback = Mock()
    broadcaster.subscribe(callback)
    broadcaster.unsubscribe(callback)
    
    broadcaster.broadcast(sample_log)
    
    callback.assert_not_called()

def test_multiple_subscribers(broadcaster, sample_log):
    callback1 = Mock()
    callback2 = Mock()
    
    broadcaster.subscribe(callback1)
    broadcaster.subscribe(callback2)
    
    broadcaster.broadcast(sample_log)
    
    callback1.assert_called_once_with(sample_log)
    callback2.assert_called_once_with(sample_log)

def test_subscriber_exception_handling(broadcaster, sample_log):
    # One subscriber raises an exception, others should still receive the log
    bad_callback = Mock(side_effect=Exception("Boom!"))
    good_callback = Mock()
    
    broadcaster.subscribe(bad_callback)
    broadcaster.subscribe(good_callback)
    
    # Should not raise exception
    broadcaster.broadcast(sample_log)
    
    bad_callback.assert_called_once()
    good_callback.assert_called_once_with(sample_log)

def test_unsubscribe_non_existent(broadcaster):
    # Should not raise error
    callback = Mock()
    broadcaster.unsubscribe(callback)
