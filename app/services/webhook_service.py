"""
Webhook service for sending HTTP notifications.
Handles delivery, retries, and error handling.
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

from app.models import WebhookPayload, ReviewResponse
from app.config import settings
from app.database import get_reviews_collection


logger = logging.getLogger(__name__)


async def send_webhook(
    webhook_url: str,
    payload: WebhookPayload,
    max_retries: int = None,
    timeout: int = None
) -> bool:
    """
    Send a webhook notification with retry logic.

    Args:
        webhook_url: Destination URL
        payload: Webhook payload to send
        max_retries: Number of retries (default from settings)
        timeout: Request timeout in seconds (default from settings)

    Returns:
        True if successful, False otherwise
    """
    if max_retries is None:
        max_retries = settings.webhook_max_retries

    if timeout is None:
        timeout = settings.webhook_timeout

    # Convert payload to dict
    payload_dict = payload.dict()

    # Log the attempt
    logger.info(f"Sending webhook to {webhook_url} for {payload.new_reviews_count} new reviews")

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    webhook_url,
                    json=payload_dict,
                    headers={"Content-Type": "application/json"}
                )

                # Check if successful (2xx status code)
                if 200 <= response.status_code < 300:
                    logger.info(f"Webhook sent successfully to {webhook_url} (status: {response.status_code})")
                    return True
                else:
                    logger.warning(f"Webhook returned status {response.status_code}: {response.text[:200]}")

        except httpx.TimeoutException:
            logger.warning(f"Webhook timeout to {webhook_url} (attempt {attempt + 1}/{max_retries + 1})")
        except httpx.RequestError as e:
            logger.warning(f"Webhook request error to {webhook_url}: {e} (attempt {attempt + 1}/{max_retries + 1})")
        except Exception as e:
            logger.error(f"Unexpected error sending webhook to {webhook_url}: {e}")

        # Wait before retry (except on last attempt)
        if attempt < max_retries:
            await asyncio.sleep(settings.webhook_retry_delay)

    logger.error(f"Failed to send webhook to {webhook_url} after {max_retries + 1} attempts")
    return False


async def notify_new_reviews(
    place_id: str,
    client_id: str,
    branch_id: str,
    webhook_url: str,
    place_name: Optional[str],
    place_url: str,
    new_reviews: List[Dict]
) -> bool:
    """
    Send webhook notification for new reviews.

    Args:
        place_id: Place ID
        client_id: Client ID
        branch_id: Branch ID
        webhook_url: Destination webhook URL
        place_name: Name of the place (optional)
        place_url: Google Maps URL
        new_reviews: List of new review dictionaries

    Returns:
        True if webhook sent successfully
    """
    if not new_reviews:
        logger.debug(f"No new reviews for place {place_id}, skipping webhook")
        return True

    try:
        # Convert reviews to ReviewResponse models
        reviews = [ReviewResponse(**review) for review in new_reviews]

        # Create webhook payload
        payload = WebhookPayload(
            event="new_reviews",
            client_id=client_id,
            branch_id=branch_id,
            place_id=place_id,
            place_name=place_name,
            place_url=place_url,
            new_reviews_count=len(reviews),
            reviews=reviews
        )

        # Send webhook
        success = await send_webhook(webhook_url, payload)

        # Mark reviews as notified if successful
        if success:
            await mark_reviews_as_notified(new_reviews)

        return success

    except Exception as e:
        logger.error(f"Error preparing webhook notification: {e}", exc_info=True)
        return False


async def mark_reviews_as_notified(reviews: List[Dict]) -> int:
    """
    Mark reviews as notified via webhook in MongoDB.

    Args:
        reviews: List of review dictionaries

    Returns:
        Number of reviews marked
    """
    collection = get_reviews_collection()
    marked_count = 0

    try:
        review_ids = [review.get('id_review') for review in reviews if review.get('id_review')]

        if not review_ids:
            return 0

        # Update all reviews in one operation
        result = collection.update_many(
            {"id_review": {"$in": review_ids}},
            {
                "$set": {
                    "notified_via_webhook": True,
                    "webhook_sent_at": datetime.utcnow()
                }
            }
        )

        marked_count = result.modified_count
        logger.info(f"Marked {marked_count} reviews as notified")

    except Exception as e:
        logger.error(f"Error marking reviews as notified: {e}")

    return marked_count


def send_webhook_sync(webhook_url: str, payload: WebhookPayload) -> bool:
    """
    Synchronous version of send_webhook (for use in non-async contexts).

    Args:
        webhook_url: Destination URL
        payload: Webhook payload

    Returns:
        True if successful
    """
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_webhook(webhook_url, payload))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in sync webhook send: {e}")
        return False


async def test_webhook(webhook_url: str) -> Dict[str, any]:
    """
    Test a webhook URL with a sample payload.

    Args:
        webhook_url: URL to test

    Returns:
        Dictionary with test results
    """
    logger.info(f"Testing webhook URL: {webhook_url}")

    # Create test payload
    test_payload = WebhookPayload(
        event="test",
        client_id="test_client",
        branch_id="test_branch",
        place_id="test_place",
        place_name="Test Place",
        place_url="https://google.com/maps/test",
        new_reviews_count=0,
        reviews=[]
    )

    try:
        async with httpx.AsyncClient(timeout=settings.webhook_timeout) as client:
            start_time = datetime.utcnow()
            response = await client.post(
                webhook_url,
                json=test_payload.dict(),
                headers={"Content-Type": "application/json"}
            )
            end_time = datetime.utcnow()

            duration = (end_time - start_time).total_seconds()

            return {
                "success": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "response_time_seconds": duration,
                "response_body": response.text[:500] if response.text else None,
                "error": None
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "status_code": None,
            "response_time_seconds": settings.webhook_timeout,
            "response_body": None,
            "error": "Timeout"
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "status_code": None,
            "response_time_seconds": None,
            "response_body": None,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "response_time_seconds": None,
            "response_body": None,
            "error": str(e)
        }
