"""
RQ Worker launcher for processing scraping tasks.
Run this file to start a worker that processes background jobs.

Usage:
    python worker.py
"""
import logging
from redis import Redis
from rq import Worker, Queue

from app.config import settings


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Start RQ worker to process scraping tasks."""
    logger.info("Starting RQ Worker...")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"Queue: {settings.redis_queue_name}")

    # Connect to Redis
    redis_conn = Redis.from_url(settings.redis_url)

    # Test connection
    try:
        redis_conn.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return

    # Create queue
    queue = Queue(settings.redis_queue_name, connection=redis_conn)

    # Create and start worker
    worker = Worker(
        [queue],
        connection=redis_conn,
        name=f"worker-{settings.redis_queue_name}"
    )

    logger.info(f"Worker '{worker.name}' started and listening for jobs...")
    logger.info("Press Ctrl+C to stop")

    try:
        worker.work(with_scheduler=False)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
