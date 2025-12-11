import pytest
import logging
from unittest.mock import Mock, MagicMock
from supertracer.services.logger import DatabaseHandler, setup_logger
from supertracer.connectors.base import BaseConnector
from supertracer.services.broadcaster import LogBroadcaster

@pytest.fixture
def mock_connector():
    connector = Mock(spec=BaseConnector)
    connector.save_log.return_value = 123
    return connector

@pytest.fixture
def mock_broadcaster():
    return Mock(spec=LogBroadcaster)

def test_database_handler_emit(mock_connector, mock_broadcaster):
    handler = DatabaseHandler(mock_connector, mock_broadcaster)
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    handler.emit(record)
    
    # Check connector call
    mock_connector.save_log.assert_called_once()
    log_arg = mock_connector.save_log.call_args[0][0]
    assert log_arg['content'] == "Test message"
    assert log_arg['log_level'] == "INFO"
    # The log object is mutable and updated after save_log returns, so we see the new ID
    assert log_arg['id'] == 123 
    
    # Check broadcaster call
    mock_broadcaster.broadcast.assert_called_once()
    broadcast_arg = mock_broadcaster.broadcast.call_args[0][0]
    assert broadcast_arg['id'] == 123 # After save (mock return value)
    assert broadcast_arg['content'] == "Test message"

def test_database_handler_emit_exception(mock_connector):
    # Setup handler that fails
    mock_connector.save_log.side_effect = Exception("DB Error")
    handler = DatabaseHandler(mock_connector)
    
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Should not raise exception (logging handlers swallow exceptions by default via handleError)
    # We can mock handleError to verify it's called
    handler.handleError = Mock()
    handler.emit(record)
    
    handler.handleError.assert_called_once_with(record)

def test_setup_logger(mock_connector, mock_broadcaster):
    logger_name = "test_setup_logger"
    
    logger = setup_logger(
        name=logger_name,
        connector=mock_connector,
        broadcaster=mock_broadcaster,
        level=logging.DEBUG,
        format_string='%(message)s'
    )
    
    assert logger.name == logger_name
    assert logger.level == logging.DEBUG
    assert logger.propagate is False
    
    # Check handlers
    handlers = logger.handlers
    # Should have DatabaseHandler and StreamHandler
    assert len(handlers) >= 2 
    db_handler = next((h for h in handlers if isinstance(h, DatabaseHandler)), None)
    assert db_handler is not None
    assert db_handler.connector == mock_connector
    assert db_handler.broadcaster == mock_broadcaster

def test_setup_logger_removes_old_handlers(mock_connector):
    logger_name = "test_reload_logger"
    
    # First setup
    logger = setup_logger(logger_name, mock_connector)
    
    # Second setup (simulate reload)
    logger = setup_logger(logger_name, mock_connector)
    
    # Should not accumulate DatabaseHandlers
    db_handlers = [h for h in logger.handlers if isinstance(h, DatabaseHandler)]
    assert len(db_handlers) == 1
