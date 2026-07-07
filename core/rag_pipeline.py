"""Main RAG pipeline orchestrator."""
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from ingestion.pdf_loader import PDFLoader
from ingestion.chunking import DocumentChunker
from database.vector_store import VectorStoreManager
from retrieval.hybrid_search import HybridRetriever
from core.embeddings import EmbeddingGenerator
from core.llm_handler import LLMHandler
from core.memory import ConversationMemory
from utils.config import config
from utils.logger import get_logger
from utils.helpers import extract_page_numbers, format_docs
from utils.constants import QA_PROMPT_TEMPLATE

logger = get_logger(__name__)


class RAGPipeline:
    """Main RAG system pipeline."""
    
    def __init__(self):
        """Initialize RAG pipeline."""
        logger.info("Initializing RAG pipeline...")
        
        # Components
        self.embedding_generator = EmbeddingGenerator()
        self.llm_handler = LLMHandler()
        self.memory = ConversationMemory()
        self.vector_store = VectorStoreManager(self.embedding_generator.embeddings)
        
        # Loaders and processors
        self.pdf_loader = PDFLoader()
        self.chunker = DocumentChunker()
        
        # Retriever
        self.retriever = None
        self.qa_chain = None
        
        # State
        self.processed_files: List[str] = []
        
        logger.info("RAG pipeline initialized successfully")
    
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a document through the entire pipeline.
        
        Args:
            file_path: Path to document
            
        Returns:
            Processing result dictionary
        """
        try:
            logger.info(f"Processing document: {file_path.name}")
            
            # Load document
            documents = self.pdf_loader.load(file_path)
            logger.info(f"Loaded {len(documents)} pages")
            
            # Chunk documents
            chunks = self.chunker.chunk_documents(documents)
            logger.info(f"Created {len(chunks)} chunks")
            
            # Store in vector database
            self.vector_store.add_documents(chunks)
            logger.info("Stored chunks in vector database")
            
            # Update retriever
            self._setup_retriever()
            
            # Track processed file
            self.processed_files.append(str(file_path.name))
            
            return {
                'success': True,
                'filename': file_path.name,
                'pages': len(documents),
                'chunks': len(chunks),
                'message': 'Document processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'success': False,
                'filename': file_path.name,
                'error': str(e)
            }
    
    def _setup_retriever(self):
        """Setup hybrid retriever and QA chain."""
        try:
            # Create hybrid retriever
            self.retriever = HybridRetriever(
                vector_store=self.vector_store.vectorstore,
                top_k=config.top_k_results
            )
            
            # Create QA chain
            prompt = PromptTemplate(
                template=QA_PROMPT_TEMPLATE,
                input_variables=["context", "question"]
            )
            
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm_handler.llm,
                chain_type="stuff",
                retriever=self.retriever.get_retriever(),
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True
            )
            
            logger.info("Retriever and QA chain setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up retriever: {e}")
            raise
    
    def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User question
            session_id: Session identifier for memory
            use_memory: Whether to use conversation memory
            
        Returns:
            Query result dictionary
        """
        try:
            if not self.qa_chain:
                return {
                    'success': False,
                    'error': 'No documents loaded. Please upload documents first.'
                }
            
            logger.info(f"Processing query: {question[:100]}...")
            
            # Add conversation context if using memory
            if use_memory and session_id:
                context = self.memory.get_context(session_id)
                if context:
                    question = f"Previous conversation:\n{context}\n\nCurrent question: {question}"
            
            # Get answer
            result = self.qa_chain({"query": question})
            
            answer = result['result']
            source_docs = result['source_documents']
            pages = extract_page_numbers(source_docs)
            
            # Store in memory
            if use_memory and session_id:
                self.memory.add_user_message(session_id, question)
                self.memory.add_ai_message(
                    session_id,
                    answer,
                    metadata={'sources': pages}
                )
            
            logger.info(f"Query processed successfully - Sources: {pages}")
            
            return {
                'success': True,
                'answer': answer,
                'sources': [
                    {
                        'content': doc.page_content,
                        'page': doc.metadata.get('page'),
                        'source': doc.metadata.get('source')
                    }
                    for doc in source_docs
                ],
                'pages': pages,
                'question': question
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session."""
        return self.memory.get_history(session_id)
    
    def delete_document(self, filename: str) -> bool:
        """Delete a document from vector store and pipeline state."""
        try:
            logger.info(f"Deleting document from pipeline: {filename}")
            
            # Delete vectors
            self.vector_store.delete_by_filename(filename)
            
            # Remove from processed files
            if filename in self.processed_files:
                self.processed_files.remove(filename)
                
            # Re-setup retriever with remaining documents
            self._setup_retriever()
            return True
        except Exception as e:
            logger.error(f"Error deleting document {filename} from pipeline: {e}")
            return False

    def clear_conversation(self, session_id: str):
        """Clear conversation for session."""
        self.memory.clear_session(session_id)
    
    def clear_database(self):
        """Clear vector database and reset state."""
        self.vector_store.clear()
        self.processed_files.clear()
        self.retriever = None
        self.qa_chain = None
        self.memory.clear_all()
        logger.info("Database and state cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            'processed_files': len(self.processed_files),
            'files': self.processed_files,
            'vector_count': self.vector_store.count(),
            'has_retriever': self.retriever is not None
        }