"""Input validation utilities."""
import os
from pathlib import Path
from typing import Optional, Tuple
from .constants import FileType, MAX_FILE_SIZE
from .logger import get_logger

try:
    import magic
except ImportError:  # pragma: no cover
    magic = None

logger = get_logger(__name__)


def validate_file(
    file_path: Path,
    allowed_types: Optional[list] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_types is None:
        allowed_types = [ft.value for ft in FileType]
    
    # Check if file exists
    if not file_path.exists():
        return False, "File does not exist"
    
    # Check file size
    if file_path.stat().st_size > MAX_FILE_SIZE:
        return False, f"File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)"
    
    # Check file extension
    extension = file_path.suffix.lstrip('.').lower()
    if extension not in allowed_types:
        return False, f"File type not supported. Allowed: {allowed_types}"
    
    # Verify MIME type
    try:
        if magic is None:
            logger.warning("python-magic not available; skipping MIME validation")
            return True, None

        mime = magic.from_file(str(file_path), mime=True)
        valid_mimes = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/plain',
            'html': 'text/html'
        }
        
        expected_mime = valid_mimes.get(extension)
        if expected_mime and mime != expected_mime:
            logger.warning(f"MIME type mismatch: expected {expected_mime}, got {mime}")
    
    except Exception as e:
        logger.error(f"Error checking MIME type: {e}")
    
    return True, None


def validate_pdf(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate PDF file specifically."""
    return validate_file(file_path, allowed_types=['pdf'])


def validate_question(question: str) -> Tuple[bool, Optional[str]]:
    """Validate user question."""
    if not question or not question.strip():
        return False, "Question cannot be empty"
    
    if len(question) < 3:
        return False, "Question too short (minimum 3 characters)"
    
    if len(question) > 1000:
        return False, "Question too long (maximum 1000 characters)"
    
    return True, None


def validate_chunk_params(
    chunk_size: int,
    chunk_overlap: int
) -> Tuple[bool, Optional[str]]:
    """Validate chunking parameters."""
    if chunk_size < 100:
        return False, "Chunk size too small (minimum 100)"
    
    if chunk_size > 2000:
        return False, "Chunk size too large (maximum 2000)"
    
    if chunk_overlap >= chunk_size:
        return False, "Chunk overlap must be less than chunk size"
    
    if chunk_overlap < 0:
        return False, "Chunk overlap cannot be negative"
    
    return True, None