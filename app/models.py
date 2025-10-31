"""
Pydantic models for request/response validation and MongoDB documents.
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class SortBy(str, Enum):
    """Sort options for Google Maps reviews."""
    NEWEST = "newest"
    MOST_RELEVANT = "most_relevant"
    HIGHEST_RATING = "highest_rating"
    LOWEST_RATING = "lowest_rating"


class JobStatus(str, Enum):
    """Status of scraping job."""
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"


# ============================================================================
# PLACE MODELS (Lugares a Monitorear)
# ============================================================================

class PlaceCreate(BaseModel):
    """Model for creating a new place to monitor."""
    client_id: str = Field(..., description="ID del cliente")
    branch_id: str = Field(..., description="ID de la sucursal")
    url: str = Field(..., description="URL de Google Maps del lugar")
    webhook_url: HttpUrl = Field(..., description="URL del webhook para notificaciones")
    name: Optional[str] = Field(None, description="Nombre del lugar (opcional)")
    check_interval_minutes: int = Field(60, ge=5, le=10080, description="Intervalo de chequeo en minutos (5 min - 7 días)")
    monitoring_enabled: bool = Field(True, description="Habilitar monitoreo automático")

    @validator('url')
    def validate_google_maps_url(cls, v):
        """Validate that the URL is a Google Maps URL."""
        if not v or 'google.com/maps' not in v.lower():
            raise ValueError('La URL debe ser de Google Maps')
        return v


class PlaceUpdate(BaseModel):
    """Model for updating an existing place."""
    webhook_url: Optional[HttpUrl] = None
    name: Optional[str] = None
    check_interval_minutes: Optional[int] = Field(None, ge=5, le=10080)
    monitoring_enabled: Optional[bool] = None


class PlaceInDB(BaseModel):
    """Model representing a place in MongoDB."""
    place_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    branch_id: str
    url: str
    webhook_url: str
    name: Optional[str] = None
    monitoring_enabled: bool = True
    check_interval_minutes: int = 60
    last_check: Optional[datetime] = None
    last_review_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlaceResponse(BaseModel):
    """Response model for place."""
    place_id: str
    client_id: str
    branch_id: str
    url: str
    webhook_url: str
    name: Optional[str]
    monitoring_enabled: bool
    check_interval_minutes: int
    last_check: Optional[datetime]
    last_review_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# REVIEW MODELS (Reseñas)
# ============================================================================

class ReviewInDB(BaseModel):
    """Model representing a review in MongoDB."""
    id_review: str  # Unique review ID
    place_id: str
    client_id: str
    branch_id: str
    caption: str
    relative_date: str
    review_date: datetime
    retrieval_date: datetime
    rating: float
    username: str
    n_review_user: Optional[int] = None
    n_photo_user: Optional[int] = None
    url_user: Optional[str] = None
    notified_via_webhook: bool = False
    webhook_sent_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReviewResponse(BaseModel):
    """Response model for review."""
    id_review: str
    place_id: Optional[str] = None
    client_id: Optional[str] = None
    branch_id: Optional[str] = None
    caption: str
    relative_date: str
    review_date: datetime
    retrieval_date: datetime
    rating: float
    username: str
    n_review_user: Optional[int] = None
    n_photo_user: Optional[int] = None
    url_user: Optional[str] = None
    notified_via_webhook: bool = False

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedReviewsResponse(BaseModel):
    """Paginated response for reviews."""
    total: int
    page: int
    page_size: int
    total_pages: int
    reviews: List[ReviewResponse]


# ============================================================================
# SCRAPING MODELS
# ============================================================================

class ScrapingRequest(BaseModel):
    """Request model for starting a scraping job."""
    url: str = Field(..., description="URL de Google Maps")
    max_reviews: int = Field(100, ge=1, le=1000, description="Número máximo de reseñas a extraer")
    sort_by: SortBy = Field(SortBy.NEWEST, description="Criterio de ordenamiento")
    client_id: Optional[str] = Field(None, description="ID del cliente (opcional)")
    branch_id: Optional[str] = Field(None, description="ID de la sucursal (opcional)")
    save_to_db: bool = Field(True, description="Guardar resultados en MongoDB")

    @validator('url')
    def validate_google_maps_url(cls, v):
        """Validate that the URL is a Google Maps URL."""
        if not v or 'google.com/maps' not in v.lower():
            raise ValueError('La URL debe ser de Google Maps')
        return v


class ScrapingJobResponse(BaseModel):
    """Response model for scraping job creation."""
    job_id: str
    status: JobStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScrapingStatusResponse(BaseModel):
    """Response model for scraping job status."""
    job_id: str
    status: JobStatus
    progress: Optional[str] = None
    error: Optional[str] = None
    result_available: bool = False
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScrapingResultResponse(BaseModel):
    """Response model for scraping job result."""
    job_id: str
    status: JobStatus
    reviews_count: int
    reviews: List[ReviewResponse]
    error: Optional[str] = None


# ============================================================================
# WEBHOOK MODELS
# ============================================================================

class WebhookPayload(BaseModel):
    """Payload sent to webhook endpoints."""
    event: str = "new_reviews"
    client_id: str
    branch_id: str
    place_id: str
    place_name: Optional[str]
    place_url: str
    new_reviews_count: int
    reviews: List[ReviewResponse]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# MONITORING MODELS
# ============================================================================

class MonitorStatusResponse(BaseModel):
    """Response model for monitoring status."""
    monitoring_active: bool
    total_places: int
    enabled_places: int
    last_check: Optional[datetime]
    next_check: Optional[datetime]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# HEALTH CHECK MODELS
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    mongodb: bool
    redis: bool
    error: Optional[str] = None
