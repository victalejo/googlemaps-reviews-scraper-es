"""
API endpoints for monitoring control and status.
Allows starting, stopping, and checking monitoring status.
"""
from fastapi import APIRouter, HTTPException, status
import logging

from app.models import MonitorStatusResponse
from app.scheduler import (
    get_scheduler_status,
    pause_monitoring,
    resume_monitoring,
    trigger_monitoring_now,
    update_monitoring_interval
)
from app.database import get_places_collection


logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# GET STATUS
# ============================================================================

@router.get("/status", response_model=MonitorStatusResponse)
async def get_monitoring_status():
    """
    Obtener el estado actual del sistema de monitoreo.

    Retorna:
    - **monitoring_active**: Si el monitoreo está activo
    - **total_places**: Total de lugares registrados
    - **enabled_places**: Lugares con monitoreo habilitado
    - **last_check**: Última vez que se ejecutó el monitoreo
    - **next_check**: Próxima ejecución programada
    """
    try:
        # Get scheduler status
        scheduler_status = get_scheduler_status()

        # Get places statistics
        places_collection = get_places_collection()
        total_places = places_collection.count_documents({})
        enabled_places = places_collection.count_documents({"monitoring_enabled": True})

        # Get last check time from most recently checked place
        last_checked = places_collection.find_one(
            {"last_check": {"$ne": None}},
            sort=[("last_check", -1)]
        )

        last_check = last_checked.get("last_check") if last_checked else None

        # Get next check time from scheduler
        next_check = None
        if scheduler_status["running"] and scheduler_status["jobs"]:
            job_info = scheduler_status["jobs"][0]
            next_check = job_info.get("next_run")

        return MonitorStatusResponse(
            monitoring_active=scheduler_status["running"],
            total_places=total_places,
            enabled_places=enabled_places,
            last_check=last_check,
            next_check=next_check
        )

    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado del monitoreo: {str(e)}"
        )


# ============================================================================
# START/STOP MONITORING
# ============================================================================

@router.post("/start")
async def start_monitoring():
    """
    Iniciar o reanudar el monitoreo automático.

    El monitoreo se ejecutará según el intervalo configurado.
    """
    try:
        success = resume_monitoring()

        if success:
            logger.info("Monitoring started/resumed via API")
            return {
                "message": "Monitoring started successfully",
                "status": get_scheduler_status()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start monitoring"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar monitoreo: {str(e)}"
        )


@router.post("/stop")
async def stop_monitoring():
    """
    Detener el monitoreo automático.

    El monitoreo se pausará hasta que se llame a /start nuevamente.
    """
    try:
        success = pause_monitoring()

        if success:
            logger.info("Monitoring stopped via API")
            return {
                "message": "Monitoring stopped successfully",
                "status": get_scheduler_status()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop monitoring"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al detener monitoreo: {str(e)}"
        )


# ============================================================================
# TRIGGER IMMEDIATE CHECK
# ============================================================================

@router.post("/check-now")
async def trigger_immediate_check():
    """
    Ejecutar una revisión inmediata de todos los lugares habilitados.

    No afecta el calendario de monitoreo programado.
    Útil para pruebas o actualizaciones bajo demanda.
    """
    try:
        logger.info("Immediate monitoring check triggered via API")

        result = trigger_monitoring_now()

        return {
            "message": "Monitoring check executed",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error triggering immediate check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar revisión inmediata: {str(e)}"
        )


# ============================================================================
# UPDATE INTERVAL
# ============================================================================

@router.put("/interval")
async def update_interval(minutes: int):
    """
    Actualizar el intervalo de monitoreo.

    - **minutes**: Nuevo intervalo en minutos (mínimo 5)

    El cambio se aplica inmediatamente.
    """
    if minutes < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El intervalo debe ser al menos 5 minutos"
        )

    try:
        success = update_monitoring_interval(minutes)

        if success:
            logger.info(f"Monitoring interval updated to {minutes} minutes via API")
            return {
                "message": f"Monitoring interval updated to {minutes} minutes",
                "interval_minutes": minutes,
                "status": get_scheduler_status()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update monitoring interval"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating monitoring interval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar intervalo: {str(e)}"
        )


# ============================================================================
# TEST WEBHOOK
# ============================================================================

@router.post("/test-webhook/{place_id}")
async def test_place_webhook(place_id: str):
    """
    Probar el webhook de un lugar específico.

    - **place_id**: ID del lugar

    Envía un webhook de prueba a la URL configurada del lugar.
    """
    from app.services.webhook_service import test_webhook

    try:
        # Get place
        places_collection = get_places_collection()
        place = places_collection.find_one({"place_id": place_id})

        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lugar con place_id={place_id} no encontrado"
            )

        webhook_url = place.get("webhook_url")

        if not webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El lugar no tiene una URL de webhook configurada"
            )

        # Test webhook
        result = await test_webhook(webhook_url)

        logger.info(f"Webhook test for place {place_id}: {result}")

        return {
            "place_id": place_id,
            "webhook_url": webhook_url,
            "test_result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook for place {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al probar webhook: {str(e)}"
        )
