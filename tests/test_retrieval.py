"""Tests for retrieval."""
import pytest
from retrieval.bm25_search import BM25Search
from langchain.schema import Document


def test_bm25_search():
    """Test BM25 search."""
    documents = [
        Document(page_content="The quick brown fox jumps over the lazy dog"),
        Document(page_content="A fast brown fox leaps over a sleepy dog"),
        Document(page_content="Python is a programming language")
    ]
    
    searcher = BM25Search(documents)
    results = searcher.search("brown fox", k=2)
    
    assert len(results) <= 2
    assert "fox" in results[0].page_content.lower()


def test_empty_query():
    """Test empty query handling."""
    documents = [Document(page_content="Test document")]
    searcher = BM25Search(documents)
    
    results = searcher.search("", k=1)
    assert isinstance(results, list)