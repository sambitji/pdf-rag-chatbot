"""PDF document loader."""
from typing import List
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader
from langchain.schema import Document
from utils.logger import get_logger
from utils.error_handlers import DocumentProcessingError

logger = get_logger(__name__)


class PDFLoader:
    """Load and extract text from PDF files."""
    
    def __init__(self, use_plumber: bool = False):
        """
        Initialize PDF loader.
        
        Args:
            use_plumber: Use PDFPlumber for better table extraction
        """
        self.use_plumber = use_plumber
        logger.info(f"Initialized PDF loader (plumber: {use_plumber})")
    
    def load(self, file_path: Path) -> List[Document]:
        """
        Load PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Loading PDF: {file_path.name}")
            
            if self.use_plumber:
                loader = PDFPlumberLoader(str(file_path))
            else:
                loader = PyPDFLoader(str(file_path))
            
            documents = loader.load()
            
            # Add metadata
            for i, doc in enumerate(documents):
                doc.metadata.update({
                    'source': str(file_path),
                    'page': i + 1,
                    'total_pages': len(documents),
                    'filename': file_path.name
                })
            
            logger.info(f"Loaded {len(documents)} pages from {file_path.name}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise DocumentProcessingError(f"Failed to load PDF: {e}")
    
    def load_multiple(self, file_paths: List[Path]) -> List[Document]:
        """Load multiple PDF files."""
        all_documents = []
        
        for file_path in file_paths:
            try:
                docs = self.load(file_path)
                all_documents.extend(docs)
            except Exception as e:
                logger.error(f"Skipping {file_path}: {e}")
                continue
        
        logger.info(f"Loaded {len(all_documents)} total pages from {len(file_paths)} files")
        return all_documents