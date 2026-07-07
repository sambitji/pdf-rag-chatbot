"""Document comparison specialist agent."""
from typing import Dict, Any, List
from langchain.schema import Document
from utils.logger import get_logger

logger = get_logger(__name__)


class ComparisonAgent:
    """Specialized agent for comparing documents."""
    
    def __init__(self, llm, retriever):
        """
        Initialize comparison agent.
        
        Args:
            llm: Language model
            retriever: Document retriever
        """
        self.llm = llm
        self.retriever = retriever
        logger.info("Initialized comparison agent")
    
    def compare(
        self,
        query: str,
        documents: List[Document] = None,
        comparison_aspects: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compare documents.
        
        Args:
            query: Comparison query
            documents: Documents to compare
            comparison_aspects: Specific aspects to compare
            
        Returns:
            Comparison result
        """
        try:
            logger.info(f"Comparison agent processing: {query[:100]}...")
            
            # Get documents if not provided
            if documents is None:
                documents = self.retriever.get_relevant_documents(query)
            
            if len(documents) < 2:
                return {
                    'success': False,
                    'error': 'Need at least 2 documents for comparison',
                    'agent': 'Comparison'
                }
            
            # Build comparison prompt
            prompt = self._build_comparison_prompt(query, documents, comparison_aspects)
            
            # Generate comparison
            response = self.llm.invoke(prompt)
            comparison = response.content
            
            result = {
                'success': True,
                'comparison': comparison,
                'num_documents': len(documents),
                'documents_compared': [
                    doc.metadata.get('source', 'Unknown') for doc in documents
                ],
                'agent': 'Comparison'
            }
            
            logger.info(f"Compared {len(documents)} documents")
            return result
            
        except Exception as e:
            logger.error(f"Comparison error: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'Comparison'
            }
    
    def _build_comparison_prompt(
        self,
        query: str,
        documents: List[Document],
        aspects: List[str] = None
    ) -> str:
        """Build comparison prompt."""
        doc_texts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', f'Document {i}')
            doc_texts.append(f"Document {i} ({source}):\n{doc.page_content[:1000]}")
        
        prompt = f"""Compare the following documents based on the query: {query}

{chr(10).join(doc_texts)}

"""
        
        if aspects:
            prompt += f"\nCompare specifically on these aspects: {', '.join(aspects)}\n"
        
        prompt += """
Provide a structured comparison highlighting:
1. Similarities
2. Differences
3. Key insights

Comparison:"""
        
        return prompt
    
    def find_contradictions(self, documents: List[Document]) -> Dict[str, Any]:
        """Find contradictions between documents."""
        prompt = f"""Analyze the following documents and identify any contradictions or conflicting information:

{self._combine_documents(documents)}

List any contradictions found:"""
        
        try:
            response = self.llm.invoke(prompt)
            
            return {
                'success': True,
                'contradictions': response.content,
                'agent': 'Comparison-Contradictions'
            }
        except Exception as e:
            logger.error(f"Contradiction detection error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _combine_documents(self, documents: List[Document], max_length: int = 4000) -> str:
        """Combine documents for analysis."""
        combined = "\n\n---\n\n".join([
            f"Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(documents)
        ])
        if len(combined) > max_length:
            combined = combined[:max_length] + "..."
        return combined