"""Structured logging configuration for the Email Agent."""
import logging
import sys
from contextvars import ContextVar
from typing import Optional
from pythonjsonlogger import jsonlogger


# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
broker_id_var: ContextVar[Optional[str]] = ContextVar("broker_id", default=None)
thread_id_var: ContextVar[Optional[str]] = ContextVar("thread_id", default=None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds contextual information.

    Includes: timestamp, level, service, broker_id, thread_id, request_id, message, extra fields
    """

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["service"] = "email-agent-backend"
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add context variables if available
        request_id = request_id_var.get()
        if request_id:
            log_record["request_id"] = request_id

        broker_id = broker_id_var.get()
        if broker_id:
            log_record["broker_id"] = broker_id

        thread_id = thread_id_var.get()
        if thread_id:
            log_record["thread_id"] = thread_id

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured JSON logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create handler with custom JSON formatter
    handler = logging.StreamHandler(sys.stdout)

    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(service)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log startup message
    root_logger.info(
        "Structured logging initialized",
        extra={"log_level": log_level, "service": "email-agent-backend"}
    )


def set_request_context(
    request_id: Optional[str] = None,
    broker_id: Optional[str] = None,
    thread_id: Optional[str] = None
) -> None:
    """
    Set contextual information for request logging.

    Args:
        request_id: Unique request identifier
        broker_id: Current broker ID
        thread_id: Email thread ID
    """
    if request_id:
        request_id_var.set(request_id)
    if broker_id:
        broker_id_var.set(broker_id)
    if thread_id:
        thread_id_var.set(thread_id)


def clear_request_context() -> None:
    """Clear contextual information after request."""
    request_id_var.set(None)
    broker_id_var.set(None)
    thread_id_var.set(None)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
