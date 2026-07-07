"""Response models."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryResponse(BaseModel):
    """Query response model."""
    success: bool
    answer: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    pages: Optional[List[int]] = None
    error: Optional[str] = None
    agent: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "answer": "The refund policy allows returns within 30 days.",
                "sources": [
                    {"content": "Refunds are processed...", "page": 15}
                ],
                "pages": [15],
                "agent": "QA"
            }
        }


class DocumentResponse(BaseModel):
    """Document response model."""
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    pages: Optional[int] = None
    chunks: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None


class DocumentListResponse(BaseModel):
    """List of documents response."""
    success: bool
    documents: List[Dict[str, Any]]
    total: int


class SummarizeResponse(BaseModel):
    """Summarization response."""
    success: bool
    summary: Optional[str] = None
    summary_type: Optional[str] = None
    num_documents: Optional[int] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    environment: str
    uptime: Optional[float] = None


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User information response."""
    username: str
    email: Optional[str]
    full_name: Optional[str]
    created_at: datetime