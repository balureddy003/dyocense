"""
Logging configuration for Dyocense v4.0

Supports both development (pretty console logs) and production (JSON structured logs for Loki).
"""

import logging
import sys
from typing import Any

from backend.config import settings


def setup_logging(name: str = __name__) -> logging.Logger:
    """
    Configure logging for the application.
    
    Development: Human-readable console logs
    Production: Structured JSON logs for Loki
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if settings.ENABLE_JSON_LOGGING:
        # JSON formatter for production (Loki-compatible)
        try:
            import json_log_formatter
            
            class CustomJSONFormatter(json_log_formatter.JSONFormatter):
                def json_record(self, message: str, extra: dict, record: logging.LogRecord) -> dict:
                    """Create JSON log record"""
                    return {
                        "timestamp": self.formatTime(record),
                        "level": record.levelname,
                        "logger": record.name,
                        "message": message,
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno,
                        **extra,
                    }
            
            formatter = CustomJSONFormatter()
        except ImportError:
            # Fallback to simple JSON if json-log-formatter not installed
            formatter = logging.Formatter(
                '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger
