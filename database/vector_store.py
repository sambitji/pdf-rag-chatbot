"""Vector database management."""
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from utils.config import config
from utils.logger import get_logger
from utils.error_handlers import DatabaseError

logger = get_logger(__name__)


class VectorStoreManager:
    """Manage vector database operations."""
    
    def __init__(
        self,
        embeddings: Optional[OpenAIEmbeddings] = None,
        persist_directory: Optional[str] = None,
        collection_name: str = "documents"
    ):
        """
        Initialize vector store manager.
        
        Args:
            embeddings: Embedding function
            persist_directory: Directory to persist database
            collection_name: Name of the collection
        """
        self.embeddings = embeddings or OpenAIEmbeddings(
            model=config.embedding_model,
            openai_api_key=config.openai_api_key
        )
        
        self.persist_directory = persist_directory or str(config.vectordb_dir)
        self.collection_name = collection_name
        self.vectorstore = None
        
        # Load existing or create new
        self._initialize_store()
        
        logger.info(
            f"Initialized vector store (collection: {collection_name}, "
            f"path: {self.persist_directory})"
        )
    
    def _initialize_store(self):
        """Initialize or load vector store."""
        try:
            # Try to load existing
            if Path(self.persist_directory).exists():
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
                logger.info("Loaded existing vector store")
            else:
                # Create new empty store
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
                logger.info("Created new vector store")
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise DatabaseError(f"Vector store initialization failed: {e}")
    
    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents to vector store.
        
        Args:
            documents: Documents to add
            batch_size: Batch size for adding documents
            
        Returns:
            List of document IDs
        """
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            ids = []
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_ids = self.vectorstore.add_documents(batch)
                ids.extend(batch_ids)
                logger.debug(f"Added batch {i // batch_size + 1}")
            
            # Persist changes
            self.vectorstore.persist()
            
            logger.info(f"Successfully added {len(ids)} documents")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise DatabaseError(f"Failed to add documents: {e}")
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict] = None
    ) -> List[Document]:
        """Search for similar documents."""
        try:
            if filter_dict:
                results = self.vectorstore.similarity_search(
                    query,
                    k=k,
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)
            
            logger.debug(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            return []
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4
    ) -> List[tuple]:
        """Search with similarity scores."""
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Search with score error: {e}")
            return []
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs."""
        try:
            self.vectorstore.delete(ids)
            self.vectorstore.persist()
            logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
            
    def delete_by_filename(self, filename: str) -> bool:
        """Delete all chunks belonging to a document filename."""
        try:
            results = self.vectorstore.get(where={"filename": filename})
            ids = results.get('ids', [])
            if ids:
                self.vectorstore.delete(ids)
                if hasattr(self.vectorstore, 'persist'):
                    self.vectorstore.persist()
                logger.info(f"Deleted {len(ids)} chunks from vector store for {filename}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from vector store: {e}")
            return False
    
    def get_all_documents(self) -> List[Document]:
        """Get all documents from store."""
        try:
            result = self.vectorstore.get()
            
            documents = []
            if 'documents' in result and 'metadatas' in result:
                for doc, meta in zip(result['documents'], result['metadatas']):
                    documents.append(Document(
                        page_content=doc,
                        metadata=meta
                    ))
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def count(self) -> int:
        """Get count of documents in store."""
        try:
            result = self.vectorstore.get()
            count = len(result.get('documents', []))
            return count
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def clear(self):
        """Clear all documents from vector store."""
        try:
            # Delete collection
            self.vectorstore.delete_collection()
            
            # Recreate empty collection
            self._initialize_store()
            
            logger.info("Vector store cleared")
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            raise DatabaseError(f"Failed to clear vector store: {e}")
    
    def update_document(self, doc_id: str, document: Document) -> bool:
        """Update a document."""
        try:
            # Delete old
            self.vectorstore.delete([doc_id])
            
            # Add new
            self.vectorstore.add_documents([document], ids=[doc_id])
            self.vectorstore.persist()
            
            logger.info(f"Updated document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False