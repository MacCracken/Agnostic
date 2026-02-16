"""
Structured logging configuration for the Agentic QA Team System.

Reads ``LOG_FORMAT`` (``"json"`` or ``"text"``, default ``"text"``) and
``LOG_LEVEL`` (default ``"INFO"``) from environment variables.  When
``structlog`` is installed and ``LOG_FORMAT=json``, produces JSON log
lines; otherwise falls back to stdlib ``logging`` with a service-name
prefix.
"""

from __future__ import annotations

import logging
import os

LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def configure_logging(service_name: str) -> logging.Logger:
    """Configure and return a logger for *service_name*.

    * ``LOG_FORMAT=json`` + structlog installed → JSON structured output.
    * Otherwise → stdlib plain-text with ``[service_name]`` prefix.
    """
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    if STRUCTLOG_AVAILABLE and LOG_FORMAT == "json":
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Always configure stdlib logging so third-party libraries behave
    logging.basicConfig(
        level=level,
        format=f"%(asctime)s [{service_name}] %(levelname)s %(name)s: %(message)s",
        force=True,
    )

    return logging.getLogger(service_name)
