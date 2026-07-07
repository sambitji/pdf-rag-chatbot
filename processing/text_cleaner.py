"""Text cleaning and preprocessing."""
import re
from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)


class TextCleaner:
    """Clean and preprocess text."""
    
    def __init__(self):
        """Initialize text cleaner."""
        logger.info("Initialized text cleaner")
    
    def clean(self, text: str) -> str:
        """
        Clean text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove special characters (keep basic punctuation)
        text = re.sub(r'[^\w\s.,!?;:()\-\'\""]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def remove_headers_footers(self, text: str) -> str:
        """Remove common headers and footers."""
        lines = text.split('\n')
        
        # Simple heuristic: remove very short lines at start/end
        # that might be headers/footers
        if len(lines) > 2:
            if len(lines[0]) < 50:
                lines = lines[1:]
            if len(lines[-1]) < 50:
                lines = lines[:-1]
        
        return '\n'.join(lines)
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Normalize newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text
    
    def remove_urls(self, text: str) -> str:
        """Remove URLs from text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, '', text)
        return text
    
    def remove_emails(self, text: str) -> str:
        """Remove email addresses."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '', text)
        return text
    
    def fix_encoding(self, text: str) -> str:
        """Fix common encoding issues."""
        replacements = {
            'â€™': "'",
            'â€œ': '"',
            'â€': '"',
            'â€"': '—',
            'â€"': '–',
            'Â': '',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def clean_batch(self, texts: List[str]) -> List[str]:
        """Clean multiple texts."""
        return [self.clean(text) for text in texts]