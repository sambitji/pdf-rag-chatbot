"""Tests for RAG pipeline."""
import pytest
from core.rag_pipeline import RAGPipeline


def test_pipeline_initialization():
    """Test pipeline initialization."""
    pipeline = RAGPipeline()
    assert pipeline is not None
    assert pipeline.embedding_generator is not None
    assert pipeline.llm_handler is not None


def test_get_stats():
    """Test statistics retrieval."""
    pipeline = RAGPipeline()
    stats = pipeline.get_stats()
    
    assert 'processed_files' in stats
    assert isinstance(stats['processed_files'], int)


def test_clear_database():
    """Test database clearing."""
    pipeline = RAGPipeline()
    pipeline.clear_database()
    
    stats = pipeline.get_stats()
    assert stats['processed_files'] == 0