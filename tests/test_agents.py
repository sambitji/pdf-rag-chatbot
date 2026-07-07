"""Tests for agents."""
import pytest
from agents.router_agent import RouterAgent, QueryType
from core.llm_handler import LLMHandler


def test_router_agent_initialization():
    """Test router agent initialization."""
    llm = LLMHandler()
    router = RouterAgent(llm.llm)
    assert router is not None


def test_query_type_detection():
    """Test query type detection."""
    llm = LLMHandler()
    router = RouterAgent(llm.llm)
    
    # This test requires OpenAI API key
    # query_type = router.route("What is the main topic?")
    # assert isinstance(query_type, QueryType)