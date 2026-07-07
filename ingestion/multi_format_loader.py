"""Multi-format document loader."""
from typing import List
from pathlib import Path
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)
from langchain.schema import Document
from utils.logger import get_logger
from utils.constants import FileType
from utils.error_handlers import DocumentProcessingError
from .pdf_loader import PDFLoader
from .ocr_loader import OCRLoader

logger = get_logger(__name__)


class MultiFormatLoader:
    """Load documents in multiple formats."""
    
    def __init__(self):
        """Initialize multi-format loader."""
        self.pdf_loader = PDFLoader()
        self.ocr_loader = OCRLoader()
        logger.info("Initialized multi-format loader")
    
    def load(self, file_path: Path) -> List[Document]:
        """
        Load document based on file type.
        
        Args:
            file_path: Path to document
            
        Returns:
            List of Document objects
        """
        extension = file_path.suffix.lstrip('.').lower()
        
        try:
            if extension == FileType.PDF.value:
                # Check if scanned
                if self.ocr_loader.detect_scanned_pdf(file_path):
                    logger.info(f"Detected scanned PDF: {file_path.name}")
                    return self.ocr_loader.load(file_path)
                else:
                    return self.pdf_loader.load(file_path)
            
            elif extension == FileType.DOCX.value:
                return self._load_docx(file_path)
            
            elif extension == FileType.TXT.value:
                return self._load_text(file_path)
            
            elif extension == FileType.MD.value:
                return self._load_markdown(file_path)
            
            elif extension == FileType.HTML.value:
                return self._load_html(file_path)
            
            else:
                raise DocumentProcessingError(f"Unsupported file type: {extension}")
                
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise DocumentProcessingError(f"Failed to load document: {e}")
    
    def _load_docx(self, file_path: Path) -> List[Document]:
        """Load DOCX file."""
        logger.info(f"Loading DOCX: {file_path.name}")
        loader = UnstructuredWordDocumentLoader(str(file_path))
        documents = loader.load()
        
        for doc in documents:
            doc.metadata.update({
                'source': str(file_path),
                'filename': file_path.name,
                'type': 'docx'
            })
        
        return documents
    
    def _load_text(self, file_path: Path) -> List[Document]:
        """Load text file."""
        logger.info(f"Loading TXT: {file_path.name}")
        loader = TextLoader(str(file_path), encoding='utf-8')
        documents = loader.load()
        
        for doc in documents:
            doc.metadata.update({
                'source': str(file_path),
                'filename': file_path.name,
                'type': 'txt'
            })
        
        return documents
    
    def _load_markdown(self, file_path: Path) -> List[Document]:
        """Load Markdown file."""
        logger.info(f"Loading MD: {file_path.name}")
        loader = UnstructuredMarkdownLoader(str(file_path))
        documents = loader.load()
        
        for doc in documents:
            doc.metadata.update({
                'source': str(file_path),
                'filename': file_path.name,
                'type': 'markdown'
            })
        
        return documents
    
    def _load_html(self, file_path: Path) -> List[Document]:
        """Load HTML file."""
        logger.info(f"Loading HTML: {file_path.name}")
        loader = UnstructuredHTMLLoader(str(file_path))
        documents = loader.load()
        
        for doc in documents:
            doc.metadata.update({
                'source': str(file_path),
                'filename': file_path.name,
                'type': 'html'
            })
        
        return documents