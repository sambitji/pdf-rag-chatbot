"""Pytest configuration and fixtures."""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rag_pipeline import RAGPipeline
from database.metadata_store import MetadataStore
from utils.config import Config


@pytest.fixture
def config():
    """Test configuration."""
    return Config()


@pytest.fixture
def rag_pipeline():
    """RAG pipeline instance."""
    return RAGPipeline()


@pytest.fixture
def metadata_store():
    """Metadata store instance."""
    return MetadataStore()


@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF for testing."""
    return Path(__file__).parent / 'fixtures' / 'sample.pdf'


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    This is a sample document for testing purposes.
    It contains multiple sentences and paragraphs.
    The RAG system should be able to process this text efficiently.
    """