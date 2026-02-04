"""
Professional Logging Configuration for Connecter Middleware
Provides structured logging with proper formatting and levels
"""
import logging
import sys
from datetime import datetime
from typing import Optional
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'call_id'):
            log_data["call_id"] = record.call_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
            
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(debug_mode: bool = False) -> logging.Logger:
    """
    Configure application-wide logging
    
    Args:
        debug_mode: If True, sets logging level to DEBUG
        
    Returns:
        Configured root logger
    """
    level = logging.DEBUG if debug_mode else logging.INFO
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Use structured formatter for production, simple for debug
    if debug_mode:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = StructuredFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom adapter to add contextual information to logs"""
    
    def process(self, msg, kwargs):
        # Add extra context to log records
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra'].update(self.extra)
        return msg, kwargs
