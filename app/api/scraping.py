"""
API endpoints for scraping operations.
Handles asynchronous scraping jobs using RQ (Redis Queue).
"""
from fastapi import APIRouter, HTTPException, status
from rq import Queue
from rq.job import Job
import logging

from app.models import (
    ScrapingRequest,
    ScrapingJobResponse,
    ScrapingStatusResponse,
    ScrapingResultResponse,
    ReviewResponse,
    JobStatus
)
from app.database import get_redis_client
from app.config import settings
from app.tasks.scraper_task import scrape_reviews_task


logger = logging.getLogger(__name__)
router = APIRouter()


def get_queue() -> Queue:
    """Get RQ queue instance."""
    redis_conn = get_redis_client()
    return Queue(settings.redis_queue_name, connection=redis_conn)


# ============================================================================
# START SCRAPING
# ============================================================================

@router.post("/start", response_model=ScrapingJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scraping(request: ScrapingRequest):
    """
    Iniciar un trabajo de scraping asíncrono.

    El scraping se ejecuta en background. Usa los endpoints de status y result
    para monitorear el progreso y obtener los resultados.

    - **url**: URL de Google Maps
    - **max_reviews**: Número máximo de reseñas (1-1000)
    - **sort_by**: Criterio de ordenamiento (newest, most_relevant, highest_rating, lowest_rating)

    Retorna:
    - **job_id**: ID del trabajo para consultar status/result
    - **status**: Estado inicial (queued)
    """
    try:
        # Get RQ queue
        queue = get_queue()

        # Enqueue scraping task
        job = queue.enqueue(
            scrape_reviews_task,
            url=request.url,
            max_reviews=request.max_reviews,
            sort_by=request.sort_by.value,
            job_timeout=settings.scraping_timeout,
            result_ttl=3600  # Keep result for 1 hour
        )

        logger.info(f"Enqueued scraping job {job.id} for URL: {request.url}")

        return ScrapingJobResponse(
            job_id=job.id,
            status=JobStatus.QUEUED,
            message="Scraping job queued successfully. Use /api/scraping/status/{job_id} to check progress."
        )

    except Exception as e:
        logger.error(f"Error enqueueing scraping job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scraping: {str(e)}"
        )


# ============================================================================
# CHECK STATUS
# ============================================================================

@router.get("/status/{job_id}", response_model=ScrapingStatusResponse)
async def get_scraping_status(job_id: str):
    """
    Consultar el estado de un trabajo de scraping.

    - **job_id**: ID del trabajo retornado por /start

    Estados posibles:
    - **queued**: En cola, esperando a ser procesado
    - **started**: En ejecución
    - **finished**: Completado exitosamente
    - **failed**: Falló con error
    """
    try:
        # Get job from Redis
        redis_conn = get_redis_client()
        job = Job.fetch(job_id, connection=redis_conn)

        # Determine status
        if job.is_queued:
            job_status = JobStatus.QUEUED
        elif job.is_started:
            job_status = JobStatus.STARTED
        elif job.is_finished:
            job_status = JobStatus.FINISHED
        elif job.is_failed:
            job_status = JobStatus.FAILED
        else:
            job_status = JobStatus.QUEUED

        # Get progress from job meta
        progress = job.meta.get('progress', None)
        error = None
        if job.is_failed:
            error = str(job.exc_info) if job.exc_info else "Unknown error"

        return ScrapingStatusResponse(
            job_id=job_id,
            status=job_status,
            progress=progress,
            error=error,
            result_available=job.is_finished,
            created_at=job.created_at,
            started_at=job.started_at,
            ended_at=job.ended_at
        )

    except Exception as e:
        logger.error(f"Error fetching job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or expired"
        )


# ============================================================================
# GET RESULT
# ============================================================================

@router.get("/result/{job_id}", response_model=ScrapingResultResponse)
async def get_scraping_result(job_id: str):
    """
    Obtener el resultado de un trabajo de scraping completado.

    - **job_id**: ID del trabajo

    Solo disponible si el job está en estado 'finished'.
    Los resultados se mantienen por 1 hora después de completarse.
    """
    try:
        # Get job from Redis
        redis_conn = get_redis_client()
        job = Job.fetch(job_id, connection=redis_conn)

        # Check if job is finished
        if not job.is_finished and not job.is_failed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not finished yet. Current status: {job.get_status()}"
            )

        # Get result
        result = job.result

        if job.is_failed:
            return ScrapingResultResponse(
                job_id=job_id,
                status=JobStatus.FAILED,
                reviews_count=0,
                reviews=[],
                error=result.get('error', 'Unknown error') if isinstance(result, dict) else str(job.exc_info)
            )

        # Parse successful result
        reviews_count = result.get('reviews_count', 0)
        reviews_data = result.get('reviews', [])

        # Convert to ReviewResponse models
        reviews = [ReviewResponse(**review) for review in reviews_data]

        return ScrapingResultResponse(
            job_id=job_id,
            status=JobStatus.FINISHED,
            reviews_count=reviews_count,
            reviews=reviews,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job result for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or result expired"
        )


# ============================================================================
# CANCEL JOB
# ============================================================================

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_scraping_job(job_id: str):
    """
    Cancelar un trabajo de scraping en cola.

    - **job_id**: ID del trabajo

    Solo se pueden cancelar trabajos en estado 'queued'.
    Los trabajos en ejecución no se pueden cancelar.
    """
    try:
        # Get job from Redis
        redis_conn = get_redis_client()
        job = Job.fetch(job_id, connection=redis_conn)

        # Check if job can be cancelled
        if job.is_started or job.is_finished:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job in status: {job.get_status()}"
            )

        # Cancel job
        job.cancel()
        logger.info(f"Cancelled job {job_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )


# ============================================================================
# WORKER STATUS
# ============================================================================

@router.get("/workers/status")
async def get_workers_status():
    """
    Obtener información sobre los workers activos.

    Útil para debugging y monitoreo del sistema.
    """
    try:
        redis_conn = get_redis_client()
        queue = Queue(settings.redis_queue_name, connection=redis_conn)

        # Get workers
        from rq import Worker
        workers = Worker.all(connection=redis_conn)

        workers_info = []
        for worker in workers:
            workers_info.append({
                "name": worker.name,
                "state": worker.get_state(),
                "current_job": worker.get_current_job_id(),
                "successful_jobs": worker.successful_job_count,
                "failed_jobs": worker.failed_job_count,
                "total_working_time": worker.total_working_time
            })

        return {
            "total_workers": len(workers),
            "workers": workers_info,
            "queue_name": queue.name,
            "queued_jobs": queue.count,
            "started_jobs": len(queue.started_job_registry),
            "finished_jobs": len(queue.finished_job_registry),
            "failed_jobs": len(queue.failed_job_registry)
        }

    except Exception as e:
        logger.error(f"Error getting workers status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workers status: {str(e)}"
        )
