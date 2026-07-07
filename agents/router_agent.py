"""Router agent to direct queries to specialized agents."""
from typing import Dict, Any
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)


class QueryType(Enum):
    """Types of queries."""
    QA = "qa"
    SUMMARIZATION = "summarization"
    COMPARISON = "comparison"
    CITATION = "citation"


class RouterAgent:
    """Route queries to appropriate specialized agents."""
    
    def __init__(self, llm):
        """
        Initialize router agent.
        
        Args:
            llm: Language model for classification
        """
        self.llm = llm
        logger.info("Initialized router agent")
    
    def route(self, query: str) -> QueryType:
        """
        Determine query type and route accordingly.
        
        Args:
            query: User query
            
        Returns:
            Query type
        """
        try:
            prompt = f"""Classify the following query into one of these categories:
1. QA - Direct question about document content
2. SUMMARIZATION - Request to summarize document(s)
3. COMPARISON - Compare multiple documents or sections
4. CITATION - Find specific citations or sources

Query: {query}

Category (reply with only: QA, SUMMARIZATION, COMPARISON, or CITATION):"""

            response = self.llm.invoke(prompt)
            category = response.content.strip().upper()
            
            if "SUMMARIZATION" in category or "SUMMARIZE" in category:
                query_type = QueryType.SUMMARIZATION
            elif "COMPARISON" in category or "COMPARE" in category:
                query_type = QueryType.COMPARISON
            elif "CITATION" in category or "SOURCE" in category:
                query_type = QueryType.CITATION
            else:
                query_type = QueryType.QA
            
            logger.info(f"Routed query to: {query_type.value}")
            return query_type
            
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return QueryType.QA  # Default to QA
    
    def get_agent_description(self, query_type: QueryType) -> str:
        """Get description of agent capabilities."""
        descriptions = {
            QueryType.QA: "Answers specific questions about document content",
            QueryType.SUMMARIZATION: "Provides summaries of documents",
            QueryType.COMPARISON: "Compares multiple documents or sections",
            QueryType.CITATION: "Finds and verifies citations and sources"
        }
        return descriptions.get(query_type, "General purpose assistant")