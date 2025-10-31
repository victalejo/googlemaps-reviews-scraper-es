"""
Database connections and initialization for MongoDB and Redis.
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from redis import Redis
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


# Global MongoDB client
_mongodb_client: Optional[MongoClient] = None
_redis_client: Optional[Redis] = None


def get_mongodb_client() -> MongoClient:
    """Get or create MongoDB client instance."""
    global _mongodb_client
    if _mongodb_client is None:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        _mongodb_client = MongoClient(settings.mongodb_url)
    return _mongodb_client


def get_database() -> Database:
    """Get MongoDB database instance."""
    client = get_mongodb_client()
    return client[settings.mongodb_db]


def get_places_collection() -> Collection:
    """Get places collection."""
    db = get_database()
    return db[settings.mongodb_places_collection]


def get_reviews_collection() -> Collection:
    """Get reviews collection."""
    db = get_database()
    return db[settings.mongodb_reviews_collection]


def get_redis_client() -> Redis:
    """Get or create Redis client instance."""
    global _redis_client
    if _redis_client is None:
        logger.info(f"Connecting to Redis at {settings.redis_url}")
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def initialize_database():
    """
    Initialize database collections and create indexes.
    Should be called on application startup.
    """
    logger.info("Initializing database...")

    # Get collections
    places_collection = get_places_collection()
    reviews_collection = get_reviews_collection()

    # Create indexes for places collection
    logger.info("Creating indexes for places collection...")
    places_collection.create_index("place_id", unique=True)
    places_collection.create_index("client_id")
    places_collection.create_index("branch_id")
    places_collection.create_index([("client_id", ASCENDING), ("branch_id", ASCENDING)])
    places_collection.create_index("monitoring_enabled")
    places_collection.create_index("last_check")
    places_collection.create_index("created_at", direction=DESCENDING)

    # Create indexes for reviews collection
    logger.info("Creating indexes for reviews collection...")
    reviews_collection.create_index("id_review", unique=True)
    reviews_collection.create_index("place_id")
    reviews_collection.create_index("client_id")
    reviews_collection.create_index("branch_id")
    reviews_collection.create_index([("client_id", ASCENDING), ("branch_id", ASCENDING)])
    reviews_collection.create_index([("place_id", ASCENDING), ("review_date", DESCENDING)])
    reviews_collection.create_index("review_date", direction=DESCENDING)
    reviews_collection.create_index("retrieval_date", direction=DESCENDING)
    reviews_collection.create_index("rating")
    reviews_collection.create_index("notified_via_webhook")

    # Compound index for pagination queries
    reviews_collection.create_index([
        ("place_id", ASCENDING),
        ("retrieval_date", DESCENDING)
    ])

    logger.info("Database initialization completed successfully")


def close_connections():
    """
    Close all database connections.
    Should be called on application shutdown.
    """
    global _mongodb_client, _redis_client

    if _mongodb_client is not None:
        logger.info("Closing MongoDB connection...")
        _mongodb_client.close()
        _mongodb_client = None

    if _redis_client is not None:
        logger.info("Closing Redis connection...")
        _redis_client.close()
        _redis_client = None


def test_connections() -> dict:
    """
    Test database connections.
    Returns dict with connection status.
    """
    status = {
        "mongodb": False,
        "redis": False,
        "error": None
    }

    try:
        # Test MongoDB
        client = get_mongodb_client()
        client.admin.command('ping')
        status["mongodb"] = True
        logger.info("MongoDB connection: OK")
    except Exception as e:
        status["error"] = f"MongoDB error: {str(e)}"
        logger.error(f"MongoDB connection failed: {e}")

    try:
        # Test Redis
        redis_client = get_redis_client()
        redis_client.ping()
        status["redis"] = True
        logger.info("Redis connection: OK")
    except Exception as e:
        if status["error"]:
            status["error"] += f" | Redis error: {str(e)}"
        else:
            status["error"] = f"Redis error: {str(e)}"
        logger.error(f"Redis connection failed: {e}")

    return status
