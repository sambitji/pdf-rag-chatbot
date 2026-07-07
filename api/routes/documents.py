"""Document management routes."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from pathlib import Path
import shutil

from api.models.request import DocumentUploadRequest
from api.models.response import DocumentResponse, DocumentListResponse
from core.rag_pipeline import RAGPipeline
from utils.config import config
from utils.logger import get_logger
from utils.validators import validate_file
from utils.helpers import generate_file_hash, sanitize_filename
from database.metadata_store import MetadataStore

logger = get_logger(__name__)
router = APIRouter()

# Initialize components
rag_pipeline = RAGPipeline()
metadata_store = MetadataStore()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    description: str = None
):
    """
    Upload a document.
    
    Args:
        file: Document file
        description: Optional description
    
    Returns:
        Upload result
    """
    try:
        # Save file temporarily
        temp_path = config.temp_dir / sanitize_filename(file.filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate file
        is_valid, error = validate_file(temp_path)
        if not is_valid:
            temp_path.unlink()
            raise HTTPException(status_code=400, detail=error)
        
        # Generate file hash
        file_hash = generate_file_hash(temp_path)
        
        # Check if already exists
        existing = metadata_store.get_document_by_hash(file_hash)
        if existing:
            temp_path.unlink()
            return DocumentResponse(
                success=True,
                document_id=str(existing['id']),
                filename=existing['filename'],
                status='already_exists'
            )
        
        # Move to documents directory
        final_path = config.documents_dir / 'pdf' / sanitize_filename(file.filename)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temp_path), str(final_path))
        
        # Add to metadata store
        doc_id = metadata_store.add_document(
            filename=file.filename,
            file_path=str(final_path),
            file_hash=file_hash,
            file_size=final_path.stat().st_size,
            file_type=final_path.suffix.lstrip('.'),
            metadata={'description': description}
        )
        
        # Process document
        result = rag_pipeline.process_document(final_path)
        
        # Update status
        if result['success']:
            metadata_store.update_document_status(
                doc_id,
                'completed',
                result.get('chunks', 0)
            )
        else:
            metadata_store.update_document_status(doc_id, 'failed')
        
        return DocumentResponse(
            success=result['success'],
            document_id=str(doc_id),
            filename=file.filename,
            pages=result.get('pages'),
            chunks=result.get('chunks'),
            status='completed' if result['success'] else 'failed',
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """List all documents."""
    try:
        documents = metadata_store.get_all_documents()
        
        return DocumentListResponse(
            success=True,
            documents=documents,
            total=len(documents)
        )
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: int):
    """Delete a document."""
    try:
        # Delete from metadata store
        doc = metadata_store.delete_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        filename = doc['filename']
        file_path = Path(doc['file_path'])
        
        # Delete from vector store
        rag_pipeline.delete_document(filename)
        
        # Delete from filesystem
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file from storage: {file_path}")
            
        return {"success": True, "message": f"Document {filename} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(document_id: int):
    """Get document details."""
    try:
        doc = metadata_store.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))