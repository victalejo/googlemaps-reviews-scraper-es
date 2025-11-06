"""
Main FastAPI application for Google Maps Reviews Scraper API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import initialize_database, close_connections, test_connections
from app.models import HealthCheckResponse


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    try:
        # Initialize database connections and indexes
        initialize_database()

        # Test connections
        status = test_connections()
        if not status["mongodb"] or not status["redis"]:
            logger.warning(f"Connection test failed: {status['error']}")
            logger.warning("API will start anyway. Connections will be retried automatically.")
        else:
            logger.info("All database connections successful")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.warning("API will start anyway. Some features may not work until connections are established.")
        # Don't raise - allow API to start even if databases are temporarily unavailable

    yield

    # Shutdown
    logger.info("Shutting down application...")

    try:
        # Close database connections
        close_connections()

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para scraping de reseñas de Google Maps",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Verifies connectivity to MongoDB and Redis.
    """
    status = test_connections()

    return HealthCheckResponse(
        status="healthy" if (status["mongodb"] and status["redis"]) else "unhealthy",
        mongodb=status["mongodb"],
        redis=status["redis"],
        error=status.get("error")
    )


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

from app.api import scraping, reviews
app.include_router(scraping.router, prefix="/api/scraping", tags=["Scraping"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "detail": str(exc) if settings.debug else "An error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
