"""Embedding generation module."""
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from utils.config import config
from utils.logger import get_logger
from utils.error_handlers import EmbeddingError

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize embedding generator."""
        self.model = model or config.embedding_model
        try:
            self.embeddings = OpenAIEmbeddings(
                model=self.model,
                openai_api_key=config.openai_api_key
            )
            logger.info(f"Initialized embedding generator with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise EmbeddingError(f"Embedding initialization failed: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents."""
        try:
            logger.debug(f"Embedding {len(texts)} documents")
            embeddings = self.embeddings.embed_documents(texts)
            logger.info(f"Successfully embedded {len(texts)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise EmbeddingError(f"Document embedding failed: {e}")
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a query."""
        try:
            logger.debug(f"Embedding query: {text[:50]}...")
            embedding = self.embeddings.embed_query(text)
            logger.info("Successfully embedded query")
            return embedding
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise EmbeddingError(f"Query embedding failed: {e}")
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        dimensions = {
            'text-embedding-3-small': 1536,
            'text-embedding-3-large': 3072,
            'text-embedding-ada-002': 1536
        }
        return dimensions.get(self.model, 1536)