"""
Simple configuration settings for SII integration service.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "SII Integration Service"
    VERSION: str = "2.0.0"
    DEBUG: bool = True

    # SII Configuration
    SII_HEADLESS: bool = True  # Run browser in headless mode
    SII_TIMEOUT: int = 30  # Timeout for Selenium operations

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
