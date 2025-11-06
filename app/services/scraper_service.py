"""
Scraper service that wraps the GoogleMapsScraper class.
Provides high-level methods for scraping reviews and saving to MongoDB.
"""
import logging
from typing import List, Dict
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
    "most_relevant": 0,  # "Más útiles" - default sort order
    "newest": 1,         # "Más recientes" - sort by newest first
    "highest_rating": 2, # "Valoración más alta"
    "lowest_rating": 3   # "Valoración más baja"
}


def scrape_reviews(
    url: str,
    max_reviews: int = 100,
    sort_by: str = "newest"
) -> List[Dict]:
    """
    Scrape reviews from a Google Maps URL.

    Args:
        url: Google Maps URL
        max_reviews: Maximum number of reviews to scrape
        sort_by: Sort option (newest, most_relevant, highest_rating, lowest_rating)

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
            sort_result = scraper.sort_by(url, sort_index)

            if sort_result == -1:
                logger.warning(f"Failed to sort reviews by '{sort_by}'. Continuing with default sort order.")
            else:
                logger.info(f"Successfully sorted reviews by '{sort_by}'")

            # Get reviews with offset 0 and max_reviews limit
            logger.info(f"Fetching up to {max_reviews} reviews...")
            reviews = scraper.get_reviews(offset=0, max_reviews=max_reviews)

            logger.info(f"Successfully scraped {len(reviews)} reviews")

            # Save to MongoDB
            if reviews:
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
            review_id = review.get('id_review', 'unknown')
            logger.error(f"Error saving review {review_id}: {e}")
            logger.debug(f"Review data that failed: {review}")
            continue

    return saved_count
