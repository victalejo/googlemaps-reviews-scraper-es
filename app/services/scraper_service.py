"""
Scraper service that wraps the GoogleMapsScraper class.
Provides high-level methods for scraping reviews and saving to MongoDB.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path to import googlemaps module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from googlemaps import GoogleMapsScraper
from app.config import settings
from app.database import get_reviews_collection
from app.models import ReviewInDB


logger = logging.getLogger(__name__)


# Mapping for sort_by parameter
SORT_MAP = {
    "newest": 0,
    "most_relevant": 1,
    "highest_rating": 2,
    "lowest_rating": 3
}


def scrape_reviews(
    url: str,
    max_reviews: int = 100,
    sort_by: str = "newest",
    client_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    place_id: Optional[str] = None,
    save_to_db: bool = True
) -> List[Dict]:
    """
    Scrape reviews from a Google Maps URL.

    Args:
        url: Google Maps URL
        max_reviews: Maximum number of reviews to scrape
        sort_by: Sort option (newest, most_relevant, highest_rating, lowest_rating)
        client_id: Client ID (optional)
        branch_id: Branch ID (optional)
        place_id: Place ID (optional)
        save_to_db: Whether to save results to MongoDB

    Returns:
        List of review dictionaries

    Raises:
        Exception: If scraping fails
    """
    logger.info(f"Starting scraping for URL: {url}, max_reviews: {max_reviews}, sort_by: {sort_by}")

    reviews = []

    try:
        # Create scraper instance with context manager
        with GoogleMapsScraper(debug=not settings.headless_mode) as scraper:

            # Sort reviews
            sort_index = SORT_MAP.get(sort_by, 0)
            logger.info(f"Sorting by: {sort_by} (index: {sort_index})")
            scraper.sort_by(url, sort_index)

            # Get reviews with offset 0 and max_reviews limit
            logger.info(f"Fetching up to {max_reviews} reviews...")
            reviews = scraper.get_reviews(offset=0, max_reviews=max_reviews)

            logger.info(f"Successfully scraped {len(reviews)} reviews")

            # Enrich reviews with additional metadata
            for review in reviews:
                if client_id:
                    review['client_id'] = client_id
                if branch_id:
                    review['branch_id'] = branch_id
                if place_id:
                    review['place_id'] = place_id

                # Ensure notified_via_webhook is set
                review['notified_via_webhook'] = False
                review['webhook_sent_at'] = None

            # Save to MongoDB if requested
            if save_to_db and reviews:
                saved_count = save_reviews_to_db(reviews)
                logger.info(f"Saved {saved_count} reviews to MongoDB")

    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        raise Exception(f"Scraping failed: {str(e)}")

    return reviews


def save_reviews_to_db(reviews: List[Dict]) -> int:
    """
    Save reviews to MongoDB, avoiding duplicates.

    Args:
        reviews: List of review dictionaries

    Returns:
        Number of reviews saved (excluding duplicates)
    """
    if not reviews:
        return 0

    collection = get_reviews_collection()
    saved_count = 0

    for review in reviews:
        try:
            # Validate and create ReviewInDB model
            review_doc = ReviewInDB(**review)

            # Check if review already exists (by id_review)
            existing = collection.find_one({"id_review": review_doc.id_review})

            if existing:
                logger.debug(f"Review {review_doc.id_review} already exists, skipping")
                continue

            # Insert new review
            collection.insert_one(review_doc.dict())
            saved_count += 1
            logger.debug(f"Inserted review {review_doc.id_review}")

        except Exception as e:
            logger.error(f"Error saving review: {e}")
            continue

    return saved_count


def get_new_reviews_for_place(
    url: str,
    place_id: str,
    client_id: str,
    branch_id: str,
    last_review_id: Optional[str] = None
) -> List[Dict]:
    """
    Get only new reviews for a place (used in monitoring).
    Stops when it encounters an existing review.

    Args:
        url: Google Maps URL
        place_id: Place ID
        client_id: Client ID
        branch_id: Branch ID
        last_review_id: ID of the last known review

    Returns:
        List of new review dictionaries
    """
    logger.info(f"Checking for new reviews for place {place_id}")

    new_reviews = []
    collection = get_reviews_collection()

    try:
        with GoogleMapsScraper(debug=not settings.headless_mode) as scraper:

            # Always sort by newest for monitoring
            scraper.sort_by(url, 0)

            # Get reviews
            reviews = scraper.get_reviews(offset=0)

            # Process reviews until we find a duplicate
            for review in reviews:
                review_id = review.get('id_review')

                # Check if review already exists
                existing = collection.find_one({"id_review": review_id})

                if existing:
                    logger.info(f"Found existing review {review_id}, stopping")
                    break

                # Add metadata
                review['place_id'] = place_id
                review['client_id'] = client_id
                review['branch_id'] = branch_id
                review['notified_via_webhook'] = False
                review['webhook_sent_at'] = None

                new_reviews.append(review)

            logger.info(f"Found {len(new_reviews)} new reviews for place {place_id}")

    except Exception as e:
        logger.error(f"Error checking for new reviews: {e}", exc_info=True)
        raise

    return new_reviews


def scrape_place_info(url: str) -> Dict:
    """
    Scrape place information (not reviews).

    Args:
        url: Google Maps URL

    Returns:
        Dictionary with place information
    """
    logger.info(f"Scraping place info for URL: {url}")

    try:
        with GoogleMapsScraper(debug=not settings.headless_mode) as scraper:
            place_data = scraper.get_account(url)
            logger.info(f"Successfully scraped place info: {place_data.get('name', 'Unknown')}")
            return place_data

    except Exception as e:
        logger.error(f"Error scraping place info: {e}", exc_info=True)
        raise Exception(f"Failed to scrape place info: {str(e)}")
