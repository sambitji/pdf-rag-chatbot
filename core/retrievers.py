"""Retrieval strategies module."""
from typing import List, Optional, Dict, Any
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain.retrievers import EnsembleRetriever
from rank_bm25 import BM25Okapi
import numpy as np
from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseRetriever:
    """Base retriever class."""
    
    def __init__(self, top_k: int = 5):
        """Initialize base retriever."""
        self.top_k = top_k
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve relevant documents."""
        raise NotImplementedError


class VectorRetriever(BaseRetriever):
    """Vector similarity retriever."""
    
    def __init__(self, vector_store: Chroma, top_k: int = 5):
        """Initialize vector retriever."""
        super().__init__(top_k)
        self.vector_store = vector_store
        logger.info("Initialized vector retriever")
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve using vector similarity."""
        try:
            docs = self.vector_store.similarity_search(query, k=self.top_k)
            logger.debug(f"Retrieved {len(docs)} documents using vector search")
            return docs
        except Exception as e:
            logger.error(f"Vector retrieval error: {e}")
            return []
    
    def retrieve_with_scores(self, query: str) -> List[tuple]:
        """Retrieve with similarity scores."""
        try:
            docs = self.vector_store.similarity_search_with_score(query, k=self.top_k)
            logger.debug(f"Retrieved {len(docs)} documents with scores")
            return docs
        except Exception as e:
            logger.error(f"Vector retrieval with scores error: {e}")
            return []


class BM25Retriever(BaseRetriever):
    """BM25 keyword-based retriever."""
    
    def __init__(self, documents: List[Document], top_k: int = 5):
        """Initialize BM25 retriever."""
        super().__init__(top_k)
        self.documents = documents
        
        # Tokenize documents
        self.tokenized_docs = [doc.page_content.lower().split() for doc in documents]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(self.tokenized_docs)
        logger.info(f"Initialized BM25 retriever with {len(documents)} documents")
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve using BM25."""
        try:
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get scores
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[-self.top_k:][::-1]
            
            # Return documents
            docs = [self.documents[i] for i in top_indices]
            logger.debug(f"Retrieved {len(docs)} documents using BM25")
            return docs
        except Exception as e:
            logger.error(f"BM25 retrieval error: {e}")
            return []
    
    def get_scores(self, query: str) -> List[float]:
        """Get BM25 scores for query."""
        tokenized_query = query.lower().split()
        return self.bm25.get_scores(tokenized_query)


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining vector and BM25."""
    
    def __init__(
        self,
        vector_store: Chroma,
        documents: Optional[List[Document]] = None,
        top_k: int = 5,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5
    ):
        """Initialize hybrid retriever."""
        super().__init__(top_k)
        
        self.vector_retriever = VectorRetriever(vector_store, top_k)
        
        # Get all documents from vector store if not provided
        if documents is None:
            try:
                documents = vector_store.get()['documents']
                documents = [Document(page_content=doc) for doc in documents]
            except:
                documents = []
        
        self.bm25_retriever = BM25Retriever(documents, top_k) if documents else None
        
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        
        logger.info(
            f"Initialized hybrid retriever "
            f"(vector: {vector_weight}, BM25: {bm25_weight})"
        )
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve using hybrid approach."""
        try:
            # Get vector results
            vector_docs = self.vector_retriever.retrieve(query)
            
            if not self.bm25_retriever:
                return vector_docs
            
            # Get BM25 results
            bm25_docs = self.bm25_retriever.retrieve(query)
            
            # Combine and deduplicate
            seen = set()
            combined = []
            
            # Add vector results first (weighted)
            for doc in vector_docs:
                doc_id = hash(doc.page_content)
                if doc_id not in seen:
                    seen.add(doc_id)
                    combined.append(doc)
            
            # Add BM25 results
            for doc in bm25_docs:
                doc_id = hash(doc.page_content)
                if doc_id not in seen:
                    seen.add(doc_id)
                    combined.append(doc)
            
            # Return top-k
            result = combined[:self.top_k]
            logger.debug(f"Retrieved {len(result)} documents using hybrid search")
            return result
            
        except Exception as e:
            logger.error(f"Hybrid retrieval error: {e}")
            return []
    
    def get_retriever(self):
        """Get LangChain compatible retriever."""
        return self.vector_retriever.vector_store.as_retriever(
            search_kwargs={"k": self.top_k}
        )


class MultiQueryRetriever(BaseRetriever):
    """Retriever that generates multiple query variations."""
    
    def __init__(
        self,
        base_retriever: BaseRetriever,
        llm,
        top_k: int = 5
    ):
        """Initialize multi-query retriever."""
        super().__init__(top_k)
        self.base_retriever = base_retriever
        self.llm = llm
        logger.info("Initialized multi-query retriever")
    
    def generate_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """Generate query variations."""
        prompt = f"""Generate {num_queries} different versions of the following question 
to retrieve relevant documents from a vector database:

Original question: {query}

Generated questions:"""
        
        try:
            response = self.llm.invoke(prompt)
            queries = [q.strip() for q in response.content.split('\n') if q.strip()]
            queries = [query] + queries[:num_queries]
            return queries
        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return [query]
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve using multiple query variations."""
        try:
            # Generate query variations
            queries = self.generate_queries(query)
            logger.debug(f"Generated {len(queries)} query variations")
            
            # Retrieve for each query
            all_docs = []
            seen = set()
            
            for q in queries:
                docs = self.base_retriever.retrieve(q)
                for doc in docs:
                    doc_id = hash(doc.page_content)
                    if doc_id not in seen:
                        seen.add(doc_id)
                        all_docs.append(doc)
            
            # Return top-k
            result = all_docs[:self.top_k]
            logger.debug(f"Retrieved {len(result)} unique documents")
            return result
            
        except Exception as e:
            logger.error(f"Multi-query retrieval error: {e}")
            return []