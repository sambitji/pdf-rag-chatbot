"""Cross-encoder reranking for improved relevance."""
from typing import List, Tuple
from sentence_transformers import CrossEncoder
from langchain.schema import Document
from utils.logger import get_logger

logger = get_logger(__name__)


class CrossEncoderReranker:
    """Rerank documents using cross-encoder."""
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize cross-encoder reranker.
        
        Args:
            model_name: HuggingFace model name
        """
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"Initialized reranker with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5
    ) -> List[Document]:
        """
        Rerank documents.
        
        Args:
            query: Search query
            documents: Documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Reranked documents
        """
        if not self.model or not documents:
            return documents[:top_k]
        
        try:
            logger.debug(f"Reranking {len(documents)} documents")
            
            # Create query-document pairs
            pairs = [[query, doc.page_content] for doc in documents]
            
            # Get scores
            scores = self.model.predict(pairs)
            
            # Sort by score
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k
            reranked = [doc for doc, score in doc_score_pairs[:top_k]]
            
            logger.info(f"Reranked to top {len(reranked)} documents")
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return documents[:top_k]
    
    def get_scores(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Tuple[Document, float]]:
        """Get documents with reranking scores."""
        if not self.model:
            return [(doc, 0.0) for doc in documents]
        
        try:
            pairs = [[query, doc.page_content] for doc in documents]
            scores = self.model.predict(pairs)
            return list(zip(documents, scores))
        except Exception as e:
            logger.error(f"Error getting scores: {e}")
            return [(doc, 0.0) for doc in documents]