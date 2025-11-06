"""
API endpoints for querying reviews from MongoDB.
Supports filtering, sorting, and pagination.
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List
import logging
import math

from app.models import (
    ReviewResponse,
    PaginatedReviewsResponse
)
from app.database import get_reviews_collection
from app.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# LIST REVIEWS (PAGINATED)
# ============================================================================

@router.get("/", response_model=PaginatedReviewsResponse)
async def list_reviews(
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    page_size: int = Query(100, ge=1, le=500, description="Tamaño de página (máx 500)"),
    min_rating: Optional[float] = Query(None, ge=1, le=5, description="Rating mínimo"),
    max_rating: Optional[float] = Query(None, ge=1, le=5, description="Rating máximo"),
    sort_by: str = Query("review_date", description="Campo para ordenar (review_date, rating, retrieval_date)"),
    sort_order: str = Query("desc", description="Orden: asc o desc")
):
    """
    Listar reseñas con paginación y filtros.

    **Filtros disponibles:**
    - **min_rating**: Rating mínimo (1-5)
    - **max_rating**: Rating máximo (1-5)

    **Paginación:**
    - **page**: Número de página (comienza en 1)
    - **page_size**: Registros por página (default: 100, max: 500)

    **Ordenamiento:**
    - **sort_by**: Campo para ordenar (review_date, rating, retrieval_date)
    - **sort_order**: Orden ascendente (asc) o descendente (desc)
    """
    collection = get_reviews_collection()

    # Build query filter
    query_filter = {}

    # Rating filters
    if min_rating is not None or max_rating is not None:
        query_filter["rating"] = {}
        if min_rating is not None:
            query_filter["rating"]["$gte"] = min_rating
        if max_rating is not None:
            query_filter["rating"]["$lte"] = max_rating

    # Validate sort parameters
    valid_sort_fields = ["review_date", "rating", "retrieval_date"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"sort_by debe ser uno de: {', '.join(valid_sort_fields)}"
        )

    sort_direction = -1 if sort_order.lower() == "desc" else 1

    try:
        # Get total count
        total_count = collection.count_documents(query_filter)

        # Calculate pagination
        skip = (page - 1) * page_size
        total_pages = math.ceil(total_count / page_size)

        # Query with pagination
        cursor = collection.find(query_filter).sort(sort_by, sort_direction).skip(skip).limit(page_size)
        reviews_data = list(cursor)

        # Convert to ReviewResponse models
        reviews = [ReviewResponse(**review) for review in reviews_data]

        logger.info(f"Listed {len(reviews)} reviews (page {page}/{total_pages}, filter: {query_filter})")

        return PaginatedReviewsResponse(
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            reviews=reviews
        )

    except Exception as e:
        logger.error(f"Error listing reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar reseñas: {str(e)}"
        )


# ============================================================================
# GET SINGLE REVIEW
# ============================================================================

@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str):
    """
    Obtener una reseña específica por su ID.

    - **review_id**: ID único de la reseña (id_review)
    """
    collection = get_reviews_collection()

    try:
        review = collection.find_one({"id_review": review_id})

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reseña con id_review={review_id} no encontrada"
            )

        return ReviewResponse(**review)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review {review_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la reseña: {str(e)}"
        )


# ============================================================================
# GET RECENT REVIEWS
# ============================================================================

@router.get("/recent/all")
async def get_recent_reviews(
    limit: int = Query(100, ge=1, le=500, description="Número de reseñas recientes")
):
    """
    Obtener las reseñas más recientes del sistema.

    - **limit**: Número de reseñas a retornar (max 500)

    Ordenadas por fecha de extracción (retrieval_date) descendente.
    Útil para monitorear nuevas reseñas en tiempo real.
    """
    collection = get_reviews_collection()

    try:
        # Query recent reviews
        cursor = collection.find({}).sort("retrieval_date", -1).limit(limit)
        reviews_data = list(cursor)

        # Convert to ReviewResponse models
        reviews = [ReviewResponse(**review) for review in reviews_data]

        logger.info(f"Retrieved {len(reviews)} recent reviews")

        return {
            "count": len(reviews),
            "reviews": reviews
        }

    except Exception as e:
        logger.error(f"Error getting recent reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener reseñas recientes: {str(e)}"
        )


# ============================================================================
# DELETE REVIEW
# ============================================================================

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: str):
    """
    Eliminar una reseña específica.

    - **review_id**: ID único de la reseña (id_review)

    ADVERTENCIA: Esta operación es irreversible.
    """
    collection = get_reviews_collection()

    try:
        result = collection.delete_one({"id_review": review_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reseña con id_review={review_id} no encontrada"
            )

        logger.info(f"Deleted review {review_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting review {review_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la reseña: {str(e)}"
        )
