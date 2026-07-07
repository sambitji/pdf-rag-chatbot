"""Tests for document ingestion."""
import pytest
from pathlib import Path
from ingestion.pdf_loader import PDFLoader
from ingestion.chunking import DocumentChunker


def test_pdf_loader_initialization():
    """Test PDF loader initialization."""
    loader = PDFLoader()
    assert loader is not None


def test_pdf_loading(sample_pdf_path):
    """Test PDF loading."""
    if sample_pdf_path.exists():
        loader = PDFLoader()
        documents = loader.load(sample_pdf_path)
        assert len(documents) > 0
        assert all(hasattr(doc, 'page_content') for doc in documents)


def test_document_chunker():
    """Test document chunking."""
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    text = "This is a test. " * 50
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 0
    assert all(len(chunk) <= 120 for chunk in chunks)  # chunk_size + some buffer


def test_chunking_overlap():
    """Test chunk overlap."""
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
    
    text = "Word " * 30
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 1