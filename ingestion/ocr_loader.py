"""OCR-based PDF loader for scanned documents."""
from typing import List
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from langchain.schema import Document
from utils.config import config
from utils.logger import get_logger
from utils.error_handlers import DocumentProcessingError

logger = get_logger(__name__)


class OCRLoader:
    """Load scanned PDFs using OCR."""
    
    def __init__(
        self,
        language: str = 'eng',
        dpi: int = 300,
        tesseract_cmd: str = None
    ):
        """
        Initialize OCR loader.
        
        Args:
            language: OCR language
            dpi: Image DPI for conversion
            tesseract_cmd: Path to tesseract executable
        """
        self.language = language
        self.dpi = dpi
        
        # Set tesseract command
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif config.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
        
        logger.info(f"Initialized OCR loader (lang: {language}, dpi: {dpi})")
    
    def load(self, file_path: Path) -> List[Document]:
        """
        Load scanned PDF using OCR.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Loading scanned PDF with OCR: {file_path.name}")
            
            # Convert PDF to images
            images = convert_from_path(
                str(file_path),
                dpi=self.dpi
            )
            logger.debug(f"Converted PDF to {len(images)} images")
            
            documents = []
            
            # OCR each page
            for i, image in enumerate(images):
                try:
                    # Preprocess image
                    processed_image = self._preprocess_image(image)
                    
                    # Extract text
                    text = pytesseract.image_to_string(
                        processed_image,
                        lang=self.language
                    )
                    
                    # Create document
                    doc = Document(
                        page_content=text,
                        metadata={
                            'source': str(file_path),
                            'page': i + 1,
                            'total_pages': len(images),
                            'filename': file_path.name,
                            'ocr': True
                        }
                    )
                    documents.append(doc)
                    
                    logger.debug(f"OCR completed for page {i + 1}/{len(images)}")
                    
                except Exception as e:
                    logger.error(f"Error processing page {i + 1}: {e}")
                    continue
            
            logger.info(f"OCR extraction complete: {len(documents)} pages")
            return documents
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {e}")
            raise DocumentProcessingError(f"OCR processing failed: {e}")
    
    def _preprocess_image(self, image: Image) -> Image:
        """Preprocess image for better OCR."""
        # Convert to grayscale
        image = image.convert('L')
        
        # Could add more preprocessing:
        # - Thresholding
        # - Noise removal
        # - Deskewing
        
        return image
    
    def detect_scanned_pdf(self, file_path: Path) -> bool:
        """
        Detect if PDF is scanned (image-based).
        
        Returns:
            True if PDF appears to be scanned
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(str(file_path))
            
            # Check first few pages
            for page_num in range(min(3, len(reader.pages))):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # If text is very short, likely scanned
                if len(text.strip()) < 50:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting scanned PDF: {e}")
            return False