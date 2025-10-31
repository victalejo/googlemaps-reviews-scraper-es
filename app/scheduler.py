"""
APScheduler configuration for periodic monitoring tasks.
Runs monitoring jobs on configured intervals.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
import logging
from datetime import datetime

from app.tasks.monitor_task import monitor_all_places
from app.config import settings


logger = logging.getLogger(__name__)


# Global scheduler instance
_scheduler: BackgroundScheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create scheduler instance."""
    global _scheduler

    if _scheduler is None:
        # Configure job stores and executors
        jobstores = {
            'default': MemoryJobStore()
        }

        # Create scheduler
        _scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone='UTC'
        )

        logger.info("APScheduler instance created")

    return _scheduler


def start_scheduler():
    """
    Start the scheduler and add monitoring jobs.
    Should be called on application startup.
    """
    scheduler = get_scheduler()

    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    try:
        # Add monitoring job
        scheduler.add_job(
            func=monitor_all_places,
            trigger=IntervalTrigger(minutes=settings.default_check_interval),
            id='monitor_all_places',
            name='Monitor all enabled places for new reviews',
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,  # Combine missed executions into one
            misfire_grace_time=300  # 5 minutes grace time
        )

        # Start scheduler
        scheduler.start()

        logger.info(f"Scheduler started with monitoring interval: {settings.default_check_interval} minutes")
        logger.info(f"Next monitoring run: {scheduler.get_job('monitor_all_places').next_run_time}")

    except Exception as e:
        logger.error(f"Error starting scheduler: {e}", exc_info=True)
        raise


def stop_scheduler():
    """
    Stop the scheduler.
    Should be called on application shutdown.
    """
    scheduler = get_scheduler()

    if not scheduler.running:
        logger.warning("Scheduler is not running")
        return

    try:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


def pause_monitoring():
    """Pause the monitoring job without stopping the scheduler."""
    scheduler = get_scheduler()

    try:
        scheduler.pause_job('monitor_all_places')
        logger.info("Monitoring job paused")
        return True
    except Exception as e:
        logger.error(f"Error pausing monitoring: {e}")
        return False


def resume_monitoring():
    """Resume the monitoring job."""
    scheduler = get_scheduler()

    try:
        scheduler.resume_job('monitor_all_places')
        logger.info("Monitoring job resumed")
        return True
    except Exception as e:
        logger.error(f"Error resuming monitoring: {e}")
        return False


def trigger_monitoring_now():
    """
    Trigger an immediate monitoring run.
    Does not interfere with scheduled runs.
    """
    try:
        logger.info("Triggering immediate monitoring run")
        result = monitor_all_places()
        logger.info(f"Immediate monitoring completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in immediate monitoring: {e}")
        return {"status": "error", "error": str(e)}


def get_scheduler_status() -> dict:
    """
    Get current scheduler status and job information.

    Returns:
        Dictionary with scheduler status
    """
    scheduler = get_scheduler()

    status = {
        "running": scheduler.running,
        "jobs": []
    }

    if scheduler.running:
        jobs = scheduler.get_jobs()

        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "paused": job.next_run_time is None
            }
            status["jobs"].append(job_info)

    return status


def update_monitoring_interval(minutes: int):
    """
    Update the monitoring interval.

    Args:
        minutes: New interval in minutes (minimum 5)
    """
    if minutes < 5:
        raise ValueError("Monitoring interval must be at least 5 minutes")

    scheduler = get_scheduler()

    try:
        # Remove existing job
        scheduler.remove_job('monitor_all_places')

        # Add new job with updated interval
        scheduler.add_job(
            func=monitor_all_places,
            trigger=IntervalTrigger(minutes=minutes),
            id='monitor_all_places',
            name='Monitor all enabled places for new reviews',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300
        )

        logger.info(f"Monitoring interval updated to {minutes} minutes")
        return True

    except Exception as e:
        logger.error(f"Error updating monitoring interval: {e}")
        return False
