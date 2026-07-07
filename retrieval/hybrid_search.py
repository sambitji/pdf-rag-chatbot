"""Hybrid search combining vector and BM25."""
from typing import List, Optional
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from .vector_search import VectorSearch
from .bm25_search import BM25Search
from utils.logger import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    """Hybrid retriever combining multiple search methods."""
    
    def __init__(
        self,
        vector_store: Chroma,
        documents: Optional[List[Document]] = None,
        top_k: int = 5,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: Vector database
            documents: Document corpus for BM25
            top_k: Number of results to return
            vector_weight: Weight for vector search
            bm25_weight: Weight for BM25 search
        """
        self.top_k = top_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        
        # Initialize searchers
        self.vector_search = VectorSearch(vector_store)
        
        if documents is None:
            # Try to get documents from vector store
            try:
                all_docs = vector_store.get()
                if 'documents' in all_docs and 'metadatas' in all_docs:
                    documents = [
                        Document(
                            page_content=doc,
                            metadata=meta
                        )
                        for doc, meta in zip(
                            all_docs['documents'],
                            all_docs['metadatas']
                        )
                    ]
            except:
                documents = []
        
        self.bm25_search = BM25Search(documents) if documents else None
        
        logger.info(
            f"Initialized hybrid retriever "
            f"(vector: {vector_weight}, BM25: {bm25_weight})"
        )
    
    def search(self, query: str) -> List[Document]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documents
        """
        try:
            # Get vector search results
            vector_docs = self.vector_search.search(query, k=self.top_k * 2)
            
            if not self.bm25_search:
                return vector_docs[:self.top_k]
            
            # Get BM25 results
            bm25_docs = self.bm25_search.search(query, k=self.top_k * 2)
            
            # Combine results
            combined = self._combine_results(vector_docs, bm25_docs)
            
            logger.info(f"Hybrid search returned {len(combined)} documents")
            return combined[:self.top_k]
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return []
    
    def _combine_results(
        self,
        vector_docs: List[Document],
        bm25_docs: List[Document]
    ) -> List[Document]:
        """Combine and deduplicate results."""
        # Score documents
        doc_scores = {}
        
        # Add vector scores
        for i, doc in enumerate(vector_docs):
            doc_id = hash(doc.page_content)
            score = (len(vector_docs) - i) / len(vector_docs)
            doc_scores[doc_id] = {
                'doc': doc,
                'score': score * self.vector_weight
            }
        
        # Add BM25 scores
        for i, doc in enumerate(bm25_docs):
            doc_id = hash(doc.page_content)
            score = (len(bm25_docs) - i) / len(bm25_docs)
            
            if doc_id in doc_scores:
                doc_scores[doc_id]['score'] += score * self.bm25_weight
            else:
                doc_scores[doc_id] = {
                    'doc': doc,
                    'score': score * self.bm25_weight
                }
        
        # Sort by combined score
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [item['doc'] for item in sorted_docs]
    
    def get_retriever(self):
        """Get LangChain compatible retriever."""
        return self.vector_search.vector_store.as_retriever(
            search_kwargs={"k": self.top_k}
        )