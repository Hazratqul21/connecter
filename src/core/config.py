from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Connecter Middleware"
    DEBUG_MODE: bool = False
    
    # Credentials
    BINOTEL_API_KEY: str = "70206a-84faf4d"
    BINOTEL_API_SECRET: str = "e4a051-9d3c02-7cdb1a-a5d224-f8406eda"
    HELPDESKEDDY_URL: str = "https://qwatt.helpdeskeddy.com/api/v2/telephony/calls/DyJmRuiZTsqsXyRsegJR"
    
    # AI & DB
    OPENAI_API_KEY: str = "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"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    class Config:
        # env_file = ".env" # Disabled as we are hardcoding
        pass

@lru_cache()
def get_settings():
    return Settings()
