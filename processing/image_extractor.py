"""Extract and describe images from documents."""
from typing import List, Dict
from pathlib import Path
from PIL import Image
import io
import base64
from utils.logger import get_logger

logger = get_logger(__name__)


class ImageExtractor:
    """Extract images from PDF documents."""
    
    def __init__(self):
        """Initialize image extractor."""
        logger.info("Initialized image extractor")
    
    def extract_images(self, pdf_path: Path, output_dir: Path = None) -> List[Dict]:
        """
        Extract images from PDF.
        
        Args:
            pdf_path: Path to PDF
            output_dir: Directory to save images
            
        Returns:
            List of image metadata
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF not installed - image extraction disabled")
            return []
        
        images_data = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Create PIL Image
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Save if output directory specified
                    if output_dir:
                        output_dir.mkdir(exist_ok=True)
                        image_filename = f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
                        image_path = output_dir / image_filename
                        image.save(image_path)
                    
                    # Store metadata
                    images_data.append({
                        'page': page_num + 1,
                        'index': img_index + 1,
                        'width': image.width,
                        'height': image.height,
                        'format': image_ext,
                        'mode': image.mode,
                        'size_bytes': len(image_bytes)
                    })
                    
                    logger.debug(
                        f"Extracted image {img_index + 1} from page {page_num + 1}"
                    )
            
            logger.info(f"Extracted {len(images_data)} images from {pdf_path.name}")
            return images_data
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []
    
    def describe_images(self, pdf_path: Path, llm) -> List[Dict]:
        """
        Extract and describe images using vision model.
        
        Args:
            pdf_path: Path to PDF
            llm: Vision-capable LLM
            
        Returns:
            List of images with descriptions
        """
        # This would use GPT-4 Vision or similar
        # Simplified placeholder implementation
        images = self.extract_images(pdf_path)
        
        for image_data in images:
            image_data['description'] = "Image description not available"
        
        return images