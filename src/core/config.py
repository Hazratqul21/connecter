"""
Centralized Configuration Module for Connecter Middleware
All credentials are hardcoded for production stability
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Production configuration with hardcoded credentials"""
    
    # Application Settings
    APP_NAME: str = "Connecter Middleware v2.0"
    APP_VERSION: str = "2.0.0"
    DEBUG_MODE: bool = False
    
    # Binotel API Credentials (Hardcoded for Production)
    BINOTEL_API_KEY: str = "70206a-84faf4d"
    BINOTEL_API_SECRET: str = "e4a051-9d3c02-7cdb1a-a5d224-f8406eda"
    BINOTEL_BASE_URL: str = "https://api.binotel.ua/api/2.0"
    
    # HelpDeskEddy Credentials (Hardcoded for Production)
    HELPDESKEDDY_URL: str = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"
    HELPDESKEDDY_TIMEOUT: int = 10
    
    # OpenAI API Credentials (Hardcoded for Production)
    OPENAI_API_KEY: str = "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"
    OPENAI_MODEL_WHISPER: str = "whisper-1"
    OPENAI_MODEL_GPT: str = "gpt-4o-mini"
    
    # Supabase Configuration (Support multiple environment variable formats)
    SUPABASE_URL: str = Field(
        default_factory=lambda: (
            os.getenv("SUPABASE_URL") or 
            os.getenv("NEXT_PUBLIC_SUPABASE_URL") or 
            ""
        )
    )
    SUPABASE_KEY: str = Field(
        default_factory=lambda: (
            os.getenv("SUPABASE_KEY") or 
            os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
            os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or 
            ""
        )
    )
    
    # Processing Configuration
    MAX_AUDIO_SIZE_MB: int = 25
    AUDIO_DOWNLOAD_TIMEOUT: int = 30
    AI_PROCESSING_TIMEOUT: int = 120
    
    # Webhook Configuration
    WEBHOOK_TIMEOUT: int = 5
    MAX_WEBHOOK_RETRIES: int = 3
    
    # Valid Event Types for Processing
    VALID_EVENT_TYPES: list = [
        "apiCallCompleted",
        "callCompleted", 
        "incomingCallCompleted",
        "outgoingCallCompleted"
    ]
    
    class Config:
        # We're using hardcoded values, but keeping Config for future flexibility
        case_sensitive = True
        

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)"""
    return Settings()


# Export settings instance for direct import
settings = get_settings()
