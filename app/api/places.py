"""
API endpoints for managing places to monitor.
CRUD operations for Google Maps locations.
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
import logging

from app.models import (
    PlaceCreate,
    PlaceUpdate,
    PlaceResponse,
    PlaceInDB
)
from app.database import get_places_collection


logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# CREATE
# ============================================================================

@router.post("/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
async def create_place(place: PlaceCreate):
    """
    Registrar un nuevo lugar para monitoreo.

    - **client_id**: ID del cliente
    - **branch_id**: ID de la sucursal
    - **url**: URL de Google Maps
    - **webhook_url**: URL donde se enviarán notificaciones
    - **name**: Nombre del lugar (opcional)
    - **check_interval_minutes**: Intervalo de chequeo (default: 60 min)
    - **monitoring_enabled**: Habilitar monitoreo (default: true)
    """
    collection = get_places_collection()

    # Create place document
    place_doc = PlaceInDB(**place.dict())

    try:
        # Check if place with same URL already exists for this client/branch
        existing = collection.find_one({
            "client_id": place_doc.client_id,
            "branch_id": place_doc.branch_id,
            "url": place_doc.url
        })

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un lugar registrado con esta URL para client_id={place.client_id} y branch_id={place.branch_id}"
            )

        # Insert into MongoDB
        result = collection.insert_one(place_doc.dict())

        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el lugar"
            )

        logger.info(f"Created place {place_doc.place_id} for client {place.client_id}, branch {place.branch_id}")

        return PlaceResponse(**place_doc.dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating place: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el lugar: {str(e)}"
        )


# ============================================================================
# READ
# ============================================================================

@router.get("/", response_model=List[PlaceResponse])
async def list_places(
    client_id: Optional[str] = Query(None, description="Filtrar por client_id"),
    branch_id: Optional[str] = Query(None, description="Filtrar por branch_id"),
    monitoring_enabled: Optional[bool] = Query(None, description="Filtrar por estado de monitoreo"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar")
):
    """
    Listar todos los lugares registrados.

    Soporta filtros opcionales:
    - **client_id**: Filtrar por cliente
    - **branch_id**: Filtrar por sucursal
    - **monitoring_enabled**: Filtrar por estado de monitoreo
    - **skip**: Paginación - registros a omitir
    - **limit**: Paginación - máximo de registros
    """
    collection = get_places_collection()

    # Build query filter
    query_filter = {}
    if client_id:
        query_filter["client_id"] = client_id
    if branch_id:
        query_filter["branch_id"] = branch_id
    if monitoring_enabled is not None:
        query_filter["monitoring_enabled"] = monitoring_enabled

    try:
        # Query with pagination
        cursor = collection.find(query_filter).skip(skip).limit(limit).sort("created_at", -1)
        places = list(cursor)

        logger.info(f"Listed {len(places)} places with filter {query_filter}")

        return [PlaceResponse(**place) for place in places]

    except Exception as e:
        logger.error(f"Error listing places: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar lugares: {str(e)}"
        )


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(place_id: str):
    """
    Obtener un lugar específico por su ID.

    - **place_id**: ID único del lugar
    """
    collection = get_places_collection()

    try:
        place = collection.find_one({"place_id": place_id})

        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lugar con place_id={place_id} no encontrado"
            )

        return PlaceResponse(**place)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting place {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el lugar: {str(e)}"
        )


# ============================================================================
# UPDATE
# ============================================================================

@router.put("/{place_id}", response_model=PlaceResponse)
async def update_place(place_id: str, place_update: PlaceUpdate):
    """
    Actualizar un lugar existente.

    - **place_id**: ID único del lugar
    - Solo se actualizan los campos proporcionados (parcial)
    """
    collection = get_places_collection()

    try:
        # Build update document (only include provided fields)
        update_doc = {k: v for k, v in place_update.dict(exclude_unset=True).items() if v is not None}

        if not update_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
            )

        # Add updated_at timestamp
        update_doc["updated_at"] = datetime.utcnow()

        # Update in MongoDB
        result = collection.find_one_and_update(
            {"place_id": place_id},
            {"$set": update_doc},
            return_document=True
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lugar con place_id={place_id} no encontrado"
            )

        logger.info(f"Updated place {place_id}: {update_doc}")

        return PlaceResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating place {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el lugar: {str(e)}"
        )


# ============================================================================
# DELETE
# ============================================================================

@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(place_id: str):
    """
    Eliminar un lugar.

    - **place_id**: ID único del lugar
    - También elimina todas las reseñas asociadas
    """
    places_collection = get_places_collection()

    try:
        # Delete place
        result = places_collection.delete_one({"place_id": place_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lugar con place_id={place_id} no encontrado"
            )

        # TODO: Optionally delete associated reviews
        # from app.database import get_reviews_collection
        # reviews_collection = get_reviews_collection()
        # reviews_collection.delete_many({"place_id": place_id})

        logger.info(f"Deleted place {place_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting place {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el lugar: {str(e)}"
        )


# ============================================================================
# STATS
# ============================================================================

@router.get("/{place_id}/stats")
async def get_place_stats(place_id: str):
    """
    Obtener estadísticas de un lugar.

    - **place_id**: ID único del lugar
    - Retorna: total de reseñas, última actualización, rating promedio, etc.
    """
    places_collection = get_places_collection()

    try:
        # Get place
        place = places_collection.find_one({"place_id": place_id})

        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lugar con place_id={place_id} no encontrado"
            )

        # Get review stats from MongoDB
        from app.database import get_reviews_collection
        reviews_collection = get_reviews_collection()

        pipeline = [
            {"$match": {"place_id": place_id}},
            {"$group": {
                "_id": None,
                "total_reviews": {"$sum": 1},
                "average_rating": {"$avg": "$rating"},
                "latest_review": {"$max": "$review_date"},
                "oldest_review": {"$min": "$review_date"}
            }}
        ]

        result = list(reviews_collection.aggregate(pipeline))
        stats = result[0] if result else {}

        return {
            "place_id": place_id,
            "place_name": place.get("name"),
            "monitoring_enabled": place.get("monitoring_enabled"),
            "last_check": place.get("last_check"),
            "total_reviews": stats.get("total_reviews", 0),
            "average_rating": round(stats.get("average_rating", 0.0), 2) if stats.get("average_rating") else None,
            "latest_review_date": stats.get("latest_review"),
            "oldest_review_date": stats.get("oldest_review")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for place {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )
