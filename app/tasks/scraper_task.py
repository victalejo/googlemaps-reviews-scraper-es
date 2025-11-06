"""
RQ (Redis Queue) tasks for asynchronous scraping operations.
These tasks are executed by worker processes.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from rq import get_current_job

from app.services.scraper_service import scrape_reviews
from app.config import settings


logger = logging.getLogger(__name__)


def scrape_reviews_task(
    url: str,
    max_reviews: int = 100,
    sort_by: str = "newest"
) -> Dict[str, Any]:
    """
    RQ task for scraping reviews asynchronously.

    This function will be executed by an RQ worker process.

    Args:
        url: Google Maps URL
        max_reviews: Maximum number of reviews to scrape
        sort_by: Sort option (newest, most_relevant, highest_rating, lowest_rating)

    Returns:
        Dictionary with results:
        {
            "status": "success" | "error",
            "reviews_count": int,
            "reviews": List[Dict],
            "error": str (if error),
            "started_at": datetime,
            "finished_at": datetime
        }
    """
    job = get_current_job()
    started_at = datetime.utcnow()

    logger.info(f"[Job {job.id}] Starting scrape_reviews_task for URL: {url}")

    try:
        # Update job meta with progress
        job.meta['status'] = 'processing'
        job.meta['progress'] = 'Initializing scraper...'
        job.meta['started_at'] = started_at.isoformat()
        job.save_meta()

        # Execute scraping
        reviews = scrape_reviews(
            url=url,
            max_reviews=max_reviews,
            sort_by=sort_by
        )

        finished_at = datetime.utcnow()
        duration = (finished_at - started_at).total_seconds()

        logger.info(f"[Job {job.id}] Scraping completed successfully. "
                   f"Found {len(reviews)} reviews in {duration:.2f}s")

        # Update job meta with success
        job.meta['status'] = 'completed'
        job.meta['progress'] = f'Completed: {len(reviews)} reviews'
        job.meta['finished_at'] = finished_at.isoformat()
        job.save_meta()

        return {
            "status": "success",
            "reviews_count": len(reviews),
            "reviews": reviews,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": duration
        }

    except Exception as e:
        finished_at = datetime.utcnow()
        duration = (finished_at - started_at).total_seconds()

        error_msg = str(e)
        logger.error(f"[Job {job.id}] Scraping failed: {error_msg}", exc_info=True)

        # Update job meta with error
        job.meta['status'] = 'failed'
        job.meta['error'] = error_msg
        job.meta['finished_at'] = finished_at.isoformat()
        job.save_meta()

        return {
            "status": "error",
            "reviews_count": 0,
            "reviews": [],
            "error": error_msg,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": duration
        }


def on_success_callback(job, connection, result, *args, **kwargs):
    """
    Callback executed when a job completes successfully.
    Can be used for logging, notifications, etc.
    """
    logger.info(f"[Job {job.id}] Success callback - {result.get('reviews_count', 0)} reviews")


def on_failure_callback(job, connection, type, value, traceback):
    """
    Callback executed when a job fails.
    Can be used for logging, alerting, etc.
    """
    logger.error(f"[Job {job.id}] Failure callback - {value}")
