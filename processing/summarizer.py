"""Document summarization."""
from typing import Optional
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document
from utils.logger import get_logger
from utils.constants import SUMMARIZATION_PROMPT

logger = get_logger(__name__)


class DocumentSummarizer:
    """Summarize documents using LLM."""
    
    def __init__(self, llm):
        """
        Initialize summarizer.
        
        Args:
            llm: Language model
        """
        self.llm = llm
        logger.info("Initialized document summarizer")
    
    def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        method: str = "stuff"
    ) -> str:
        """
        Summarize text.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            method: Summarization method (stuff, map_reduce, refine)
            
        Returns:
            Summary text
        """
        try:
            logger.debug(f"Summarizing text ({len(text)} chars)")
            
            # Create document
            doc = Document(page_content=text)
            
            # Load chain
            chain = load_summarize_chain(
                self.llm,
                chain_type=method
            )
            
            # Generate summary
            summary = chain.run([doc])
            
            # Truncate if needed
            if max_length and len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            logger.info(f"Generated summary ({len(summary)} chars)")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Summary generation failed"
    
    def summarize_long_document(
        self,
        documents: list,
        method: str = "map_reduce"
    ) -> str:
        """Summarize long documents using map-reduce."""
        try:
            chain = load_summarize_chain(
                self.llm,
                chain_type=method
            )
            
            summary = chain.run(documents)
            logger.info("Generated long document summary")
            return summary
            
        except Exception as e:
            logger.error(f"Long document summarization error: {e}")
            return "Summary generation failed"