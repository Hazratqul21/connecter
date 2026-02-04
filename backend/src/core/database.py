"""
Database Connection and Management Module
Handles Supabase client initialization and connection pooling
"""
from typing import Optional
from supabase import create_client, Client
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Global Supabase client instance (singleton pattern)
_supabase_client: Optional[Client] = None


def initialize_supabase() -> Optional[Client]:
    """
    Initialize Supabase client with connection validation
    
    Returns:
        Supabase client instance or None if credentials are missing
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    
    if not url or not key:
        logger.warning(
            "Supabase credentials not configured. "
            "Database features will be disabled."
        )
        return None
    
    try:
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}", exc_info=True)
        return None


def get_supabase() -> Optional[Client]:
    """
    Get the global Supabase client instance
    
    Returns:
        Supabase client or None if not initialized
    """
    if _supabase_client is None:
        return initialize_supabase()
    return _supabase_client


def close_supabase():
    """Close Supabase connection (cleanup)"""
    global _supabase_client
    if _supabase_client:
        # Supabase client doesn't have explicit close,
        # but we reset the singleton
        _supabase_client = None
        logger.info("Supabase client connection closed")
