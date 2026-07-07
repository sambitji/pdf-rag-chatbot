"""Custom exception handlers."""


class RAGSystemError(Exception):
    """Base exception for RAG system."""
    pass


class DocumentProcessingError(RAGSystemError):
    """Error during document processing."""
    pass


class EmbeddingError(RAGSystemError):
    """Error during embedding generation."""
    pass


class RetrievalError(RAGSystemError):
    """Error during retrieval."""
    pass


class LLMError(RAGSystemError):
    """Error with LLM."""
    pass


class ValidationError(RAGSystemError):
    """Validation error."""
    pass


class DatabaseError(RAGSystemError):
    """Database error."""
    pass


class CacheError(RAGSystemError):
    """Cache error."""
    pass


class AuthenticationError(RAGSystemError):
    """Authentication error."""
    pass


class RateLimitError(RAGSystemError):
    """Rate limit exceeded."""
    pass