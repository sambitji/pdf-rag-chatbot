"""Vector similarity search."""
from typing import List, Tuple
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from utils.logger import get_logger

logger = get_logger(__name__)


class VectorSearch:
    """Perform vector similarity search."""
    
    def __init__(self, vector_store: Chroma):
        """Initialize vector search."""
        self.vector_store = vector_store
        logger.info("Initialized vector search")
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: dict = None
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results
            filter_dict: Metadata filters
            
        Returns:
            List of relevant documents
        """
        try:
            logger.debug(f"Vector search: '{query}' (k={k})")
            
            if filter_dict:
                docs = self.vector_store.similarity_search(
                    query,
                    k=k,
                    filter=filter_dict
                )
            else:
                docs = self.vector_store.similarity_search(query, k=k)
            
            logger.info(f"Found {len(docs)} relevant documents")
            return docs
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def search_with_scores(
        self,
        query: str,
        k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Search with similarity scores."""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.info(f"Found {len(results)} results with scores")
            return results
        except Exception as e:
            logger.error(f"Vector search with scores error: {e}")
            return []
    
    def search_by_vector(
        self,
        embedding: List[float],
        k: int = 5
    ) -> List[Document]:
        """Search using embedding vector."""
        try:
            docs = self.vector_store.similarity_search_by_vector(embedding, k=k)
            return docs
        except Exception as e:
            logger.error(f"Search by vector error: {e}")
            return []