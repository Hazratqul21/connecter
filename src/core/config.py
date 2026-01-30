from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os

class Settings(BaseSettings):
    APP_NAME: str = "Connecter Middleware"
    DEBUG_MODE: bool = False
    
    # Credentials
    # Credentials
    BINOTEL_API_KEY: str = "70206a-84faf4d"
    BINOTEL_API_SECRET: str = "e4a051-9d3c02-7cdb1a-a5d224-f8406eda"
    HELPDESKEDDY_URL: str = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"
    
    # AI & DB
    OPENAI_API_KEY: str = "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"
    
    # Support both standard and Vercel naming conventions
    SUPABASE_URL: str = Field(default_factory=lambda: os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "")
    SUPABASE_KEY: str = Field(default_factory=lambda: os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or "")

    class Config:
        # env_file = ".env" # Disabled as we are hardcoding/using environment
        pass

@lru_cache()
def get_settings():
    return Settings()
