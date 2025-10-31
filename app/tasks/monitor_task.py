"""
Task for monitoring places and detecting new reviews.
Sends webhook notifications when new reviews are found.
"""
import logging
from datetime import datetime
from typing import Dict, Any
import asyncio

from app.database import get_places_collection, get_reviews_collection
from app.services.scraper_service import get_new_reviews_for_place, save_reviews_to_db
from app.services.webhook_service import notify_new_reviews
from app.config import settings


logger = logging.getLogger(__name__)


async def monitor_place_async(place_data: Dict) -> Dict[str, Any]:
    """
    Monitor a single place for new reviews (async version).

    Args:
        place_data: Place document from MongoDB

    Returns:
        Dictionary with monitoring results
    """
    place_id = place_data.get('place_id')
    client_id = place_data.get('client_id')
    branch_id = place_data.get('branch_id')
    url = place_data.get('url')
    webhook_url = place_data.get('webhook_url')
    place_name = place_data.get('name')

    logger.info(f"Monitoring place {place_id} ({place_name}) for client {client_id}, branch {branch_id}")

    result = {
        "place_id": place_id,
        "client_id": client_id,
        "branch_id": branch_id,
        "status": "success",
        "new_reviews_count": 0,
        "webhook_sent": False,
        "error": None,
        "checked_at": datetime.utcnow().isoformat()
    }

    try:
        # Get new reviews
        new_reviews = get_new_reviews_for_place(
            url=url,
            place_id=place_id,
            client_id=client_id,
            branch_id=branch_id
        )

        result["new_reviews_count"] = len(new_reviews)

        # If new reviews found, save and notify
        if new_reviews:
            logger.info(f"Found {len(new_reviews)} new reviews for place {place_id}")

            # Save to MongoDB
            saved_count = save_reviews_to_db(new_reviews)
            logger.info(f"Saved {saved_count} new reviews to MongoDB")

            # Send webhook notification
            webhook_success = await notify_new_reviews(
                place_id=place_id,
                client_id=client_id,
                branch_id=branch_id,
                webhook_url=webhook_url,
                place_name=place_name,
                place_url=url,
                new_reviews=new_reviews
            )

            result["webhook_sent"] = webhook_success

            if not webhook_success:
                logger.warning(f"Failed to send webhook for place {place_id}")
                result["error"] = "Webhook delivery failed"
        else:
            logger.info(f"No new reviews found for place {place_id}")

        # Update place's last_check timestamp
        places_collection = get_places_collection()
        places_collection.update_one(
            {"place_id": place_id},
            {
                "$set": {
                    "last_check": datetime.utcnow(),
                    "last_review_count": get_total_review_count(place_id)
                }
            }
        )

    except Exception as e:
        logger.error(f"Error monitoring place {place_id}: {e}", exc_info=True)
        result["status"] = "error"
        result["error"] = str(e)

    return result


def monitor_place(place_data: Dict) -> Dict[str, Any]:
    """
    Monitor a single place for new reviews (sync version for RQ).

    Args:
        place_data: Place document from MongoDB

    Returns:
        Dictionary with monitoring results
    """
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(monitor_place_async(place_data))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in sync monitor_place: {e}")
        return {
            "place_id": place_data.get('place_id'),
            "status": "error",
            "error": str(e)
        }


async def monitor_all_places_async() -> Dict[str, Any]:
    """
    Monitor all enabled places for new reviews (async version).

    Returns:
        Dictionary with overall monitoring results
    """
    logger.info("Starting monitoring cycle for all enabled places")

    places_collection = get_places_collection()

    # Get all places with monitoring enabled
    places = list(places_collection.find({"monitoring_enabled": True}))

    if not places:
        logger.info("No places with monitoring enabled")
        return {
            "status": "success",
            "total_places": 0,
            "successful": 0,
            "failed": 0,
            "total_new_reviews": 0,
            "results": []
        }

    logger.info(f"Monitoring {len(places)} places")

    results = []
    successful = 0
    failed = 0
    total_new_reviews = 0

    # Process each place
    for place in places:
        result = await monitor_place_async(place)
        results.append(result)

        if result["status"] == "success":
            successful += 1
            total_new_reviews += result["new_reviews_count"]
        else:
            failed += 1

    summary = {
        "status": "success",
        "total_places": len(places),
        "successful": successful,
        "failed": failed,
        "total_new_reviews": total_new_reviews,
        "checked_at": datetime.utcnow().isoformat(),
        "results": results
    }

    logger.info(f"Monitoring cycle completed: {successful} successful, {failed} failed, {total_new_reviews} new reviews")

    return summary


def monitor_all_places() -> Dict[str, Any]:
    """
    Monitor all enabled places for new reviews (sync version for RQ/scheduler).

    Returns:
        Dictionary with overall monitoring results
    """
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(monitor_all_places_async())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in monitor_all_places: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


def get_total_review_count(place_id: str) -> int:
    """
    Get total number of reviews for a place.

    Args:
        place_id: Place ID

    Returns:
        Total review count
    """
    try:
        reviews_collection = get_reviews_collection()
        count = reviews_collection.count_documents({"place_id": place_id})
        return count
    except Exception as e:
        logger.error(f"Error counting reviews for place {place_id}: {e}")
        return 0
