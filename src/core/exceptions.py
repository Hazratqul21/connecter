"""
Centralized Error Handling and Custom Exceptions
Provides consistent error responses across the middleware
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ConnecterException(Exception):
    """Base exception for all Connecter middleware errors"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class WebhookValidationError(ConnecterException):
    """Raised when webhook payload validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class BinotelAPIError(ConnecterException):
    """Raised when Binotel API communication fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


class HelpDeskEddyError(ConnecterException):
    """Raised when HelpDeskEddy API communication fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


class AIProcessingError(ConnecterException):
    """Raised when AI processing (transcription/analysis) fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class DatabaseError(ConnecterException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )
