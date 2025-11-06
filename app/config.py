"""
Configuration settings for the Google Maps Reviews Scraper API.
Uses Pydantic Settings for environment variable management.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Google Maps Reviews Scraper API"
    app_version: str = "1.0.0"
    debug: bool = False

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017/"
    mongodb_db: str = "googlemaps"
    mongodb_reviews_collection: str = "reviews"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_queue_name: str = "scraping_tasks"

    # Scraping Configuration
    default_reviews_count: int = 100
    scraping_timeout: int = 900  # seconds (increased from 300 to handle large scraping jobs)
    headless_mode: bool = True
    chrome_driver_path: Optional[str] = None  # None = auto-detect

    # Pagination
    default_page_size: int = 100
    max_page_size: int = 500

    # Logging
    log_level: str = "INFO"
    log_file: str = "api.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures we only create one instance.
    """
    return Settings()


# Export settings instance
settings = get_settings()
