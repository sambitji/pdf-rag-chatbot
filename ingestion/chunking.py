"""Document chunking strategies."""
from typing import List, Optional
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)
from langchain.schema import Document
from utils.config import config
from utils.logger import get_logger
from utils.constants import ChunkingStrategy

logger = get_logger(__name__)


class DocumentChunker:
    """Chunk documents using various strategies."""
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    ):
        """
        Initialize document chunker.
        
        Args:
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy
        """
        self.chunk_size = chunk_size or config.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap
        self.strategy = strategy
        
        self._setup_splitter()
        
        logger.info(
            f"Initialized chunker (size: {self.chunk_size}, "
            f"overlap: {self.chunk_overlap}, strategy: {strategy})"
        )
    
    def _setup_splitter(self):
        """Setup text splitter based on strategy."""
        if self.strategy == ChunkingStrategy.RECURSIVE:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        
        elif self.strategy == ChunkingStrategy.FIXED_SIZE:
            self.splitter = CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator="\n"
            )
        
        elif self.strategy == ChunkingStrategy.SEMANTIC:
            # Semantic chunking would use sentence embeddings
            # For now, use recursive as fallback
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        
        else:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Chunk documents.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of chunked documents
        """
        try:
            logger.info(f"Chunking {len(documents)} documents")
            
            chunks = self.splitter.split_documents(documents)
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata['chunk_id'] = i
                chunk.metadata['chunk_size'] = len(chunk.page_content)
            
            logger.info(f"Created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking documents: {e}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Chunk raw text."""
        try:
            chunks = self.splitter.split_text(text)
            logger.debug(f"Created {len(chunks)} text chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise


class SemanticChunker:
    """Chunk documents based on semantic similarity."""
    
    def __init__(
        self,
        embedding_function,
        similarity_threshold: float = 0.5,
        max_chunk_size: int = 1000
    ):
        """
        Initialize semantic chunker.
        
        Args:
            embedding_function: Function to generate embeddings
            similarity_threshold: Threshold for semantic similarity
            max_chunk_size: Maximum chunk size
        """
        self.embedding_function = embedding_function
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size
        logger.info("Initialized semantic chunker")
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk documents using semantic similarity."""
        # This is a simplified version
        # Production would use more sophisticated semantic analysis
        
        all_chunks = []
        
        for doc in documents:
            sentences = self._split_into_sentences(doc.page_content)
            chunks = self._group_semantically(sentences, doc.metadata)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _group_semantically(
        self,
        sentences: List[str],
        metadata: dict
    ) -> List[Document]:
        """Group sentences into semantic chunks."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.max_chunk_size:
                if current_chunk:
                    chunks.append(Document(
                        page_content=" ".join(current_chunk),
                        metadata=metadata.copy()
                    ))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(Document(
                page_content=" ".join(current_chunk),
                metadata=metadata.copy()
            ))
        
        return chunks