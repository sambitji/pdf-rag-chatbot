"""Extract and parse tables from documents."""
from typing import List, Dict
import pdfplumber
from pathlib import Path
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


class TableExtractor:
    """Extract tables from PDF documents."""
    
    def __init__(self):
        """Initialize table extractor."""
        logger.info("Initialized table extractor")
    
    def extract_tables(self, pdf_path: Path) -> List[Dict]:
        """
        Extract tables from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of table data
        """
        tables_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    
                    for table_num, table in enumerate(tables, 1):
                        if table and len(table) > 1:
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            
                            # Store table info
                            table_info = {
                                'page': page_num,
                                'table_number': table_num,
                                'data': df.to_dict('records'),
                                'csv': df.to_csv(index=False),
                                'markdown': df.to_markdown(index=False),
                                'shape': df.shape
                            }
                            
                            tables_data.append(table_info)
                            
                            logger.debug(
                                f"Extracted table {table_num} from page {page_num} "
                                f"(shape: {df.shape})"
                            )
            
            logger.info(f"Extracted {len(tables_data)} tables from {pdf_path.name}")
            return tables_data
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def extract_table_text(self, pdf_path: Path) -> str:
        """Extract tables as formatted text."""
        tables = self.extract_tables(pdf_path)
        
        text_parts = []
        for table in tables:
            text_parts.append(
                f"\n[Table from Page {table['page']}]\n{table['markdown']}\n"
            )
        
        return "\n".join(text_parts)
    
    def detect_tables(self, pdf_path: Path) -> List[Dict]:
        """Detect table locations in PDF."""
        table_locations = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.find_tables()
                    
                    for table in tables:
                        table_locations.append({
                            'page': page_num,
                            'bbox': table.bbox,
                            'cells': len(table.cells)
                        })
            
            logger.info(f"Detected {len(table_locations)} tables")
            return table_locations
            
        except Exception as e:
            logger.error(f"Error detecting tables: {e}")
            return []