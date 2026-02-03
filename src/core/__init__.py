"""
Connecter Middleware - Core Module
Contains configuration, database, logging, and utility functions
"""
__version__ = "2.0.0"

from .config import settings, get_settings
from .database import get_supabase, initialize_supabase
from .logging_config import setup_logging, get_logger

__all__ = [
    "settings",
    "get_settings",
    "get_supabase",
    "initialize_supabase",
    "setup_logging",
    "get_logger"
]
