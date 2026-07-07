"""Admin routes."""
from fastapi import APIRouter, HTTPException, Depends
from api.routes.auth import verify_token
from database.metadata_store import MetadataStore
from core.rag_pipeline import RAGPipeline
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

metadata_store = MetadataStore()
rag_pipeline = RAGPipeline()


@router.get("/stats")
async def get_statistics(username: str = Depends(verify_token)):
    """Get system statistics."""
    try:
        stats = metadata_store.get_statistics()
        rag_stats = rag_pipeline.get_stats()
        
        return {
            "success": True,
            "database_stats": stats,
            "rag_stats": rag_stats
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-database")
async def clear_database(username: str = Depends(verify_token)):
    """Clear vector database."""
    try:
        rag_pipeline.clear_database()
        
        return {
            "success": True,
            "message": "Database cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Clear database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_logs(username: str = Depends(verify_token), limit: int = 100):
    """Get recent logs."""
    try:
        # Read recent log entries
        log_file = logger.handlers[1].baseFilename  # File handler
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-limit:]
        
        return {
            "success": True,
            "logs": recent_logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))