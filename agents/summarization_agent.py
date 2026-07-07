"""Summarization specialist agent."""
from typing import Dict, Any, List
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document
from utils.logger import get_logger

logger = get_logger(__name__)


class SummarizationAgent:
    """Specialized agent for document summarization."""
    
    def __init__(self, llm, retriever):
        """
        Initialize summarization agent.
        
        Args:
            llm: Language model
            retriever: Document retriever
        """
        self.llm = llm
        self.retriever = retriever
        logger.info("Initialized summarization agent")
    
    def summarize(
        self,
        query: str = None,
        documents: List[Document] = None,
        summary_type: str = "concise"
    ) -> Dict[str, Any]:
        """
        Summarize documents.
        
        Args:
            query: Optional query to focus summary
            documents: Documents to summarize (if None, retrieve based on query)
            summary_type: Type of summary (concise, detailed, bullet_points)
            
        Returns:
            Summary result
        """
        try:
            logger.info(f"Summarization agent processing ({summary_type})")
            
            # Get documents if not provided
            if documents is None and query:
                documents = self.retriever.get_relevant_documents(query)
            elif documents is None:
                return {
                    'success': False,
                    'error': 'No documents provided or query specified'
                }
            
            # Choose summarization method
            if len(documents) <= 3:
                chain_type = "stuff"
            else:
                chain_type = "map_reduce"
            
            # Create summary chain
            chain = load_summarize_chain(
                self.llm,
                chain_type=chain_type
            )
            
            # Generate summary
            summary = chain.run(documents)
            
            # Format based on type
            formatted_summary = self._format_summary(summary, summary_type)
            
            response = {
                'success': True,
                'summary': formatted_summary,
                'num_documents': len(documents),
                'summary_type': summary_type,
                'agent': 'Summarization'
            }
            
            logger.info(f"Generated {summary_type} summary from {len(documents)} documents")
            return response
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'Summarization'
            }
    
    def _format_summary(self, summary: str, summary_type: str) -> str:
        """Format summary based on type."""
        if summary_type == "bullet_points":
            prompt = f"""Convert this summary into clear bullet points:

{summary}

Bullet points:"""
            
            try:
                response = self.llm.invoke(prompt)
                return response.content
            except:
                return summary
        
        elif summary_type == "detailed":
            return summary
        
        else:  # concise
            # Take first 500 characters if too long
            if len(summary) > 500:
                return summary[:500] + "..."
            return summary
    
    def summarize_by_topic(
        self,
        documents: List[Document],
        topics: List[str]
    ) -> Dict[str, str]:
        """
        Summarize documents by specific topics.
        
        Args:
            documents: Documents to summarize
            topics: List of topics to focus on
            
        Returns:
            Dictionary mapping topics to summaries
        """
        topic_summaries = {}
        
        for topic in topics:
            prompt = f"""Summarize the following documents focusing specifically on: {topic}

Documents:
{self._combine_documents(documents)}

Summary focused on {topic}:"""
            
            try:
                response = self.llm.invoke(prompt)
                topic_summaries[topic] = response.content
            except Exception as e:
                logger.error(f"Error summarizing topic {topic}: {e}")
                topic_summaries[topic] = f"Error generating summary for {topic}"
        
        return topic_summaries
    
    def _combine_documents(self, documents: List[Document], max_length: int = 4000) -> str:
        """Combine documents into single text."""
        combined = "\n\n---\n\n".join([doc.page_content for doc in documents])
        if len(combined) > max_length:
            combined = combined[:max_length] + "..."
        return combined