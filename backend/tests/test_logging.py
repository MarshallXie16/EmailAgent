"""Tests for structured logging configuration."""
import pytest
import logging
import json
from io import StringIO
from app.core.logging_config import (
    setup_logging,
    set_request_context,
    clear_request_context,
    get_logger,
    request_id_var,
    broker_id_var,
    thread_id_var,
)


@pytest.fixture
def log_output():
    """Capture log output."""
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    return stream, handler


def test_setup_logging():
    """Test logging setup."""
    setup_logging(log_level="DEBUG")
    logger = get_logger("test")
    assert logger.level == logging.DEBUG


def test_get_logger():
    """Test logger creation."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_set_request_context():
    """Test setting request context."""
    set_request_context(
        request_id="req-123",
        broker_id="broker-456",
        thread_id="thread-789"
    )

    assert request_id_var.get() == "req-123"
    assert broker_id_var.get() == "broker-456"
    assert thread_id_var.get() == "thread-789"


def test_clear_request_context():
    """Test clearing request context."""
    set_request_context(
        request_id="req-123",
        broker_id="broker-456",
        thread_id="thread-789"
    )

    clear_request_context()

    assert request_id_var.get() is None
    assert broker_id_var.get() is None
    assert thread_id_var.get() is None


def test_context_isolation():
    """Test that context variables are isolated."""
    # Set context
    set_request_context(request_id="req-1")
    assert request_id_var.get() == "req-1"

    # Clear and set new context
    clear_request_context()
    set_request_context(request_id="req-2")
    assert request_id_var.get() == "req-2"


def test_partial_context():
    """Test setting partial context."""
    set_request_context(request_id="req-123")
    assert request_id_var.get() == "req-123"
    assert broker_id_var.get() is None

    set_request_context(broker_id="broker-456")
    assert request_id_var.get() == "req-123"  # Should still be set
    assert broker_id_var.get() == "broker-456"


def test_logger_with_extra_fields():
    """Test logging with extra fields."""
    setup_logging(log_level="INFO")
    logger = get_logger("test")

    # Set context
    set_request_context(request_id="req-123", broker_id="broker-456")

    # Capture logs
    with pytest.LogCapture(level=logging.INFO) as log_capture:
        logger.info(
            "Test message",
            extra={"custom_field": "custom_value"}
        )

    # Verify log was captured
    assert len(log_capture.records) > 0


def test_logger_levels():
    """Test different log levels."""
    setup_logging(log_level="DEBUG")
    logger = get_logger("test")

    # All levels should work
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_exception_logging():
    """Test exception logging."""
    setup_logging(log_level="INFO")
    logger = get_logger("test")

    try:
        raise ValueError("Test error")
    except ValueError as e:
        # Should capture exception info
        logger.error("Error occurred", exc_info=True)


def test_log_level_filtering():
    """Test that log level filtering works."""
    setup_logging(log_level="WARNING")
    logger = get_logger("test")

    # DEBUG and INFO should not be logged
    assert logger.getEffectiveLevel() == logging.WARNING

    # Only WARNING and above should pass through
    logger.debug("Should not log")
    logger.info("Should not log")
    logger.warning("Should log")
    logger.error("Should log")


def test_multiple_loggers():
    """Test creating multiple loggers."""
    setup_logging()

    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    assert logger1.name == "module1"
    assert logger2.name == "module2"
    assert logger1 != logger2
