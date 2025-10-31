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
    mongodb_places_collection: str = "places"
    mongodb_reviews_collection: str = "reviews"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_queue_name: str = "scraping_tasks"

    # Scraping Configuration
    default_reviews_count: int = 100
    scraping_timeout: int = 300  # seconds
    headless_mode: bool = True
    chrome_driver_path: Optional[str] = None  # None = auto-detect

    # Monitoring Configuration
    default_check_interval: int = 60  # minutes
    enable_monitoring_on_startup: bool = True
    max_concurrent_scrapers: int = 3

    # Webhook Configuration
    webhook_timeout: int = 10  # seconds
    webhook_max_retries: int = 3
    webhook_retry_delay: int = 5  # seconds

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
