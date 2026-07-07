"""Query routes."""
from fastapi import APIRouter, HTTPException
from api.models.request import QueryRequest, SummarizeRequest, CompareRequest
from api.models.response import QueryResponse, SummarizeResponse
from core.rag_pipeline import RAGPipeline
from agents.router_agent import RouterAgent, QueryType
from agents.qa_agent import QAAgent
from agents.summarization_agent import SummarizationAgent
from agents.comparison_agent import ComparisonAgent
from core.llm_handler import LLMHandler
from database.metadata_store import MetadataStore
from utils.logger import get_logger
import time

from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from typing import List, Any

logger = get_logger(__name__)
router = APIRouter()

# Initialize components
rag_pipeline = RAGPipeline()
llm_handler = LLMHandler()
metadata_store = MetadataStore()

# Define a dynamic retriever proxy wrapper
class DynamicPipelineRetriever(BaseRetriever):
    pipeline: Any

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        if self.pipeline.retriever:
            return self.pipeline.retriever.search(query)
        return []

# Initialize agents with dynamic retriever proxy
dynamic_retriever = DynamicPipelineRetriever(pipeline=rag_pipeline)
router_agent = RouterAgent(llm_handler.llm)
qa_agent = QAAgent(llm_handler.llm, dynamic_retriever)
summarization_agent = SummarizationAgent(llm_handler.llm, dynamic_retriever)
comparison_agent = ComparisonAgent(llm_handler.llm, dynamic_retriever)


@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Ask a question using the RAG system.
    
    Args:
        request: Query request
    
    Returns:
        Query response with answer and sources
    """
    try:
        start_time = time.time()
        
        # Route to appropriate agent
        query_type = router_agent.route(request.query)
        
        if query_type == QueryType.QA:
            result = qa_agent.answer(request.query)
        elif query_type == QueryType.SUMMARIZATION:
            result = summarization_agent.summarize(query=request.query)
        elif query_type == QueryType.COMPARISON:
            result = comparison_agent.compare(request.query)
        else:
            result = rag_pipeline.query(
                request.query,
                session_id=request.session_id,
                use_memory=request.use_memory
            )
        
        # Log query
        response_time = time.time() - start_time
        if request.session_id:
            metadata_store.add_query(
                query_text=request.query,
                response=result.get('answer', ''),
                sources=result.get('pages', []),
                response_time=response_time,
                session_id=request.session_id
            )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_documents(request: SummarizeRequest):
    """Summarize documents."""
    try:
        result = summarization_agent.summarize(
            query=request.query,
            summary_type=request.summary_type
        )
        
        return SummarizeResponse(**result)
        
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_documents(request: CompareRequest):
    """Compare documents."""
    try:
        result = comparison_agent.compare(
            query=request.query,
            comparison_aspects=request.comparison_aspects
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_query_history(session_id: str, limit: int = 10):
    """Get query history for a session."""
    try:
        history = metadata_store.get_query_history(session_id, limit)
        return {
            "success": True,
            "history": history,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))