"""Citation and source verification agent."""
from typing import Dict, Any, List
from langchain.schema import Document
from utils.logger import get_logger

logger = get_logger(__name__)


class CitationAgent:
    """Specialized agent for finding and verifying citations."""
    
    def __init__(self, llm, retriever):
        """
        Initialize citation agent.
        
        Args:
            llm: Language model
            retriever: Document retriever
        """
        self.llm = llm
        self.retriever = retriever
        logger.info("Initialized citation agent")
    
    def find_citations(self, claim: str) -> Dict[str, Any]:
        """
        Find citations supporting a claim.
        
        Args:
            claim: Claim to verify
            
        Returns:
            Citations and verification result
        """
        try:
            logger.info(f"Finding citations for: {claim[:100]}...")
            
            # Retrieve relevant documents
            documents = self.retriever.get_relevant_documents(claim)
            
            # Build verification prompt
            prompt = f"""Find citations that support or refute this claim: "{claim}"

Based on these documents:
{self._format_documents(documents)}

Provide:
1. Supporting citations (with page numbers)
2. Contradicting citations (if any)
3. Confidence level (High/Medium/Low)

Analysis:"""
            
            response = self.llm.invoke(prompt)
            
            result = {
                'success': True,
                'claim': claim,
                'analysis': response.content,
                'sources': [
                    {
                        'content': doc.page_content[:200],
                        'page': doc.metadata.get('page'),
                        'source': doc.metadata.get('source')
                    }
                    for doc in documents
                ],
                'agent': 'Citation'
            }
            
            logger.info(f"Found {len(documents)} relevant sources")
            return result
            
        except Exception as e:
            logger.error(f"Citation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'Citation'
            }
    
    def verify_fact(self, statement: str) -> Dict[str, Any]:
        """
        Verify a factual statement against documents.
        
        Args:
            statement: Statement to verify
            
        Returns:
            Verification result
        """
        try:
            documents = self.retriever.get_relevant_documents(statement)
            
            prompt = f"""Verify this statement against the provided documents: "{statement}"

Documents:
{self._format_documents(documents)}

Verification (respond with: SUPPORTED, CONTRADICTED, or INCONCLUSIVE):
Explanation:"""
            
            response = self.llm.invoke(prompt)
            content = response.content
            
            # Determine verification status
            if "SUPPORTED" in content.upper():
                status = "SUPPORTED"
            elif "CONTRADICTED" in content.upper():
                status = "CONTRADICTED"
            else:
                status = "INCONCLUSIVE"
            
            return {
                'success': True,
                'statement': statement,
                'status': status,
                'explanation': content,
                'sources_checked': len(documents),
                'agent': 'Citation-Verification'
            }
            
        except Exception as e:
            logger.error(f"Fact verification error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_bibliography(self, documents: List[Document]) -> str:
        """Generate formatted bibliography."""
        bibliography = []
        
        seen_sources = set()
        for doc in documents:
            source = doc.metadata.get('source', 'Unknown')
            if source not in seen_sources:
                seen_sources.add(source)
                
                page = doc.metadata.get('page', 'N/A')
                filename = doc.metadata.get('filename', source)
                
                citation = f"- {filename}, Page {page}"
                bibliography.append(citation)
        
        return "\n".join(bibliography)
    
    def _format_documents(self, documents: List[Document], max_length: int = 3000) -> str:
        """Format documents for citation analysis."""
        formatted = []
        for i, doc in enumerate(documents, 1):
            page = doc.metadata.get('page', 'Unknown')
            source = doc.metadata.get('source', 'Unknown')
            formatted.append(
                f"[{i}] (Page {page}, {source}):\n{doc.page_content[:500]}"
            )
        
        combined = "\n\n".join(formatted)
        if len(combined) > max_length:
            combined = combined[:max_length] + "..."
        return combined