"""
Pydantic models for request/response validation and MongoDB documents.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


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
# REVIEW MODELS (Reseñas)
# ============================================================================

class ReviewInDB(BaseModel):
    """Model representing a review in MongoDB."""
    id_review: str  # Unique review ID from Google Maps
    caption: Optional[str] = None  # Optional - some reviews may not have text
    relative_date: Optional[str] = None  # Optional - may fail to extract
    review_date: datetime
    retrieval_date: datetime
    rating: Optional[float] = None  # Optional - may fail to extract
    username: Optional[str] = None  # Optional - may fail to extract
    n_review_user: Optional[int] = None
    n_photo_user: Optional[int] = None
    url_user: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReviewResponse(BaseModel):
    """Response model for review."""
    id_review: str
    caption: Optional[str] = None  # Optional - some reviews may not have text
    relative_date: Optional[str] = None  # Optional - may fail to extract
    review_date: datetime
    retrieval_date: datetime
    rating: Optional[float] = None  # Optional - may fail to extract
    username: Optional[str] = None  # Optional - may fail to extract
    n_review_user: Optional[int] = None
    n_photo_user: Optional[int] = None
    url_user: Optional[str] = None

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
# HEALTH CHECK MODELS
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    mongodb: bool
    redis: bool
    error: Optional[str] = None
