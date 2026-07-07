"""Request models."""
from pydantic import BaseModel, Field
from typing import Optional, List


class ConfigMixin:
    """Compatibility mixin for Pydantic v2 settings."""

    model_config = {
        "json_schema_extra": {
            "example": {}
        }
    }


class QueryRequest(BaseModel, ConfigMixin):
    """Query request model."""
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    use_memory: bool = Field(True, description="Use conversation memory")
    top_k: int = Field(5, ge=1, le=20, description="Number of results")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What is the refund policy?",
                "session_id": "user123",
                "use_memory": True,
                "top_k": 5
            }
        }


class DocumentUploadRequest(BaseModel, ConfigMixin):
    """Document upload metadata."""
    filename: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class SummarizeRequest(BaseModel, ConfigMixin):
    """Summarization request."""
    query: Optional[str] = None
    summary_type: str = Field("concise", pattern="^(concise|detailed|bullet_points)$")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "Summarize the company policy on remote work",
                "summary_type": "bullet_points"
            }
        }
    }


class CompareRequest(BaseModel, ConfigMixin):
    """Comparison request."""
    query: str
    document_ids: Optional[List[str]] = None
    comparison_aspects: Optional[List[str]] = None


class LoginRequest(BaseModel, ConfigMixin):
    """Login request."""
    username: str
    password: str


class UserCreate(BaseModel, ConfigMixin):
    """User creation request."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: Optional[str] = None
    full_name: Optional[str] = None