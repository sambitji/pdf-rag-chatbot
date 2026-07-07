"""Helper utility functions."""
import re
import hashlib
import tiktoken
from pathlib import Path
from typing import List, Optional
from langchain.schema import Document
from .logger import get_logger

logger = get_logger(__name__)


def format_docs(docs: List[Document]) -> str:
    """Format retrieved documents for context."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get('page', 'Unknown')
        source = doc.metadata.get('source', 'Unknown')
        formatted.append(
            f"[Document {i} - Page {page} from {Path(source).name}]\n{doc.page_content}"
        )
    return "\n\n".join(formatted)


def extract_page_numbers(docs: List[Document]) -> List[int]:
    """Extract unique page numbers from documents."""
    pages = set()
    for doc in docs:
        if 'page' in doc.metadata:
            pages.add(doc.metadata['page'])
    return sorted(list(pages))


def calculate_token_count(text: str, model: str = "gpt-4") -> int:
    """Calculate token count for text."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error calculating tokens: {e}")
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be filesystem-safe."""
    # Remove any character that isn't alphanumeric, dash, underscore, or dot
    sanitized = re.sub(r'[^\w\-.]', '_', filename)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def generate_file_hash(file_path: Path) -> str:
    """Generate SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def chunk_text_by_tokens(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
    model: str = "gpt-4"
) -> List[str]:
    """Chunk text by token count."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        
        chunks = []
        start = 0
        while start < len(tokens):
            end = start + max_tokens
            chunk_tokens = tokens[start:end]
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            start = end - overlap_tokens
        
        return chunks
    except Exception as e:
        logger.error(f"Error chunking by tokens: {e}")
        return [text]


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove multiple whitespaces
    text = re.sub(r'\s+', ' ', text)
    # Remove multiple newlines
    text = re.sub(r'\n+', '\n', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text