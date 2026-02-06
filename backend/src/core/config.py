"""
Centralized Configuration Module for Connecter Middleware
"""
from functools import lru_cache

class Settings:
    """Production configuration with hardcoded credentials"""
    
    APP_NAME: str = "Connecter Middleware (Binotel -> HDE)"
    APP_VERSION: str = "3.0.0"
    
    # Binotel WebSocket/API Credentials
    BINOTEL_WEB_KEY: str = "114e5e-5e61a64"
    BINOTEL_WEB_SECRET: str = "4e8039-d5385d-bfd84c-f07be4-771ce163"
    
    # HelpDeskEddy Integration
    HELPDESKEDDY_URL: str = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"
    
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
