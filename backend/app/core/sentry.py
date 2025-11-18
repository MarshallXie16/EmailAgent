"""Sentry error tracking configuration."""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings


def init_sentry() -> None:
    """
    Initialize Sentry error tracking.

    Only initializes if SENTRY_DSN is configured and environment is not development.
    """
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    environment = getattr(settings, 'ENVIRONMENT', 'development')

    if not sentry_dsn:
        # Sentry not configured, skip initialization
        return

    if environment == 'development':
        # Don't send errors from development environment
        return

    # Configure Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=get_traces_sample_rate(environment),
        profiles_sample_rate=get_profiles_sample_rate(environment),

        # Integrations
        integrations=[
            # FastAPI integration for HTTP request tracking
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[500, 599],
            ),
            # Celery integration for background task tracking
            CeleryIntegration(
                monitor_beat_tasks=True,
                exclude_beat_tasks=[],
            ),
            # SQLAlchemy integration for database query tracking
            SqlalchemyIntegration(),
            # Redis integration for cache tracking
            RedisIntegration(),
            # Logging integration
            LoggingIntegration(
                level=None,  # Don't capture logs (we use structured logging)
                event_level=None,  # Don't create events from logs
            ),
        ],

        # Performance monitoring
        enable_tracing=True,

        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII by default
        max_breadcrumbs=50,

        # Release tracking
        release=get_release_version(),

        # Error filtering
        before_send=before_send_filter,
        before_send_transaction=before_send_transaction_filter,
    )


def get_traces_sample_rate(environment: str) -> float:
    """
    Get transaction sampling rate based on environment.

    Args:
        environment: Environment name (production, staging, etc.)

    Returns:
        Sample rate (0.0 to 1.0)
    """
    rates = {
        'production': 0.1,  # 10% of transactions
        'staging': 0.5,     # 50% of transactions
        'testing': 1.0,     # 100% of transactions
    }
    return rates.get(environment, 0.1)


def get_profiles_sample_rate(environment: str) -> float:
    """
    Get profiling sampling rate based on environment.

    Args:
        environment: Environment name (production, staging, etc.)

    Returns:
        Sample rate (0.0 to 1.0)
    """
    rates = {
        'production': 0.01,  # 1% of transactions
        'staging': 0.1,      # 10% of transactions
        'testing': 0.5,      # 50% of transactions
    }
    return rates.get(environment, 0.01)


def get_release_version() -> str:
    """
    Get current release version for tracking.

    Returns:
        Release version string
    """
    # Try to get version from environment variable
    import os
    version = os.getenv('GIT_COMMIT_SHA', os.getenv('VERSION', 'unknown'))
    return f"email-agent-backend@{version}"


def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry.

    Args:
        event: Sentry event data
        hint: Additional context

    Returns:
        Modified event or None to drop
    """
    # Filter out specific errors that we don't want to track
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Ignore common non-critical errors
        ignored_errors = [
            'TimeoutError',
            'asyncio.TimeoutError',
            'CancelledError',
            'asyncio.CancelledError',
        ]

        if exc_type.__name__ in ignored_errors:
            return None

    # Add custom context
    event.setdefault('tags', {})
    event['tags']['service'] = 'email-agent-backend'

    return event


def before_send_transaction_filter(event, hint):
    """
    Filter transactions before sending to Sentry.

    Args:
        event: Sentry transaction event
        hint: Additional context

    Returns:
        Modified event or None to drop
    """
    # Filter out health check transactions
    if event.get('transaction') in ['/health', '/']:
        return None

    return event


def set_user_context(user_id: str, email: str = None) -> None:
    """
    Set user context for Sentry events.

    Args:
        user_id: User/broker ID
        email: User email (optional)
    """
    sentry_sdk.set_user({
        'id': user_id,
        'email': email,
    })


def set_context(key: str, value: dict) -> None:
    """
    Set custom context for Sentry events.

    Args:
        key: Context key
        value: Context data
    """
    sentry_sdk.set_context(key, value)


def capture_exception(error: Exception, **kwargs) -> None:
    """
    Manually capture an exception to Sentry.

    Args:
        error: Exception to capture
        **kwargs: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_tag(key, value)
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = 'info', **kwargs) -> None:
    """
    Manually capture a message to Sentry.

    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context as tags
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_tag(key, value)
        sentry_sdk.capture_message(message, level=level)
