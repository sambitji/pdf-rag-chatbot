"""BM25 keyword search."""
from typing import List
from rank_bm25 import BM25Okapi
import numpy as np
from langchain.schema import Document
from utils.logger import get_logger

logger = get_logger(__name__)


class BM25Search:
    """Perform BM25 keyword search."""
    
    def __init__(self, documents: List[Document]):
        """
        Initialize BM25 search.
        
        Args:
            documents: Corpus of documents
        """
        self.documents = documents
        
        # Tokenize corpus
        self.tokenized_corpus = [
            doc.page_content.lower().split()
            for doc in documents
        ]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        logger.info(f"Initialized BM25 search with {len(documents)} documents")
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search using BM25.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of relevant documents
        """
        try:
            logger.debug(f"BM25 search: '{query}' (k={k})")
            
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get scores
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[-k:][::-1]
            
            # Return documents
            results = [self.documents[i] for i in top_indices if scores[i] > 0]
            
            logger.info(f"Found {len(results)} relevant documents")
            return results
            
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
            return []
    
    def get_scores(self, query: str) -> np.ndarray:
        """Get BM25 scores for query."""
        tokenized_query = query.lower().split()
        return self.bm25.get_scores(tokenized_query)