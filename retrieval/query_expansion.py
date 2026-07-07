"""Query expansion for better retrieval."""
from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)


class QueryExpander:
    """Expand queries for better retrieval."""
    
    def __init__(self, llm):
        """
        Initialize query expander.
        
        Args:
            llm: Language model for query expansion
        """
        self.llm = llm
        logger.info("Initialized query expander")
    
    def expand_query(
        self,
        query: str,
        num_expansions: int = 3
    ) -> List[str]:
        """
        Generate query expansions.
        
        Args:
            query: Original query
            num_expansions: Number of expansions to generate
            
        Returns:
            List of expanded queries including original
        """
        try:
            prompt = f"""Generate {num_expansions} different versions of the following question 
to improve document retrieval. Make them semantically similar but use different wording.

Original question: {query}

Alternative questions (one per line):"""

            response = self.llm.invoke(prompt)
            
            # Parse response
            expansions = [
                line.strip().lstrip('0123456789.-) ')
                for line in response.content.split('\n')
                if line.strip()
            ]
            
            # Include original query
            all_queries = [query] + expansions[:num_expansions]
            
            logger.info(f"Generated {len(all_queries)} query variations")
            return all_queries
            
        except Exception as e:
            logger.error(f"Query expansion error: {e}")
            return [query]
    
    def expand_with_synonyms(self, query: str) -> str:
        """Expand query with synonyms."""
        # Simple implementation - production would use WordNet or similar
        prompt = f"""Add relevant synonyms to enhance this search query:

Query: {query}

Enhanced query with synonyms:"""

        try:
            response = self.llm.invoke(prompt)
            expanded = response.content.strip()
            logger.debug(f"Expanded query: {expanded}")
            return expanded
        except Exception as e:
            logger.error(f"Synonym expansion error: {e}")
            return query