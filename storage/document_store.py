"""Document storage with metadata."""
from typing import Dict, Any, Optional
from pathlib import Path
from database.metadata_store import MetadataStore
from storage.file_storage import FileStorage
from utils.logger import get_logger
from utils.helpers import generate_file_hash

logger = get_logger(__name__)


class DocumentStore:
    """Combined document and metadata storage."""
    
    def __init__(self):
        """Initialize document store."""
        self.file_storage = FileStorage()
        self.metadata_store = MetadataStore()
        logger.info("Initialized document store")
    
    def add_document(
        self,
        file,
        filename: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add document with metadata.
        
        Args:
            file: File object
            filename: Filename
            file_type: File type
            metadata: Additional metadata
            
        Returns:
            Result dictionary
        """
        try:
            # Save file
            file_path = self.file_storage.save_file(file, filename, file_type)
            
            # Generate hash
            file_hash = generate_file_hash(file_path)
            
            # Check if already exists
            existing = self.metadata_store.get_document_by_hash(file_hash)
            if existing:
                logger.warning(f"Document already exists: {filename}")
                return {
                    'success': False,
                    'error': 'Document already exists',
                    'document_id': existing['id']
                }
            
            # Add to metadata store
            doc_id = self.metadata_store.add_document(
                filename=filename,
                file_path=str(file_path),
                file_hash=file_hash,
                file_size=file_path.stat().st_size,
                file_type=file_type,
                metadata=metadata
            )
            
            logger.info(f"Added document: {filename} (ID: {doc_id})")
            
            return {
                'success': True,
                'document_id': doc_id,
                'file_path': str(file_path),
                'file_hash': file_hash
            }
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        cursor = self.metadata_store.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_document(self, doc_id: int) -> bool:
        """
        Delete document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Success status
        """
        try:
            # Get document info
            doc = self.get_document(doc_id)
            if not doc:
                return False
            
            # Delete file
            file_path = Path(doc['file_path'])
            self.file_storage.delete_file(file_path)
            
            # Delete from metadata
            cursor = self.metadata_store.conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            self.metadata_store.conn.commit()
            
            logger.info(f"Deleted document ID: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def search_documents(self, query: str) -> list:
        """Search documents by filename or metadata."""
        cursor = self.metadata_store.conn.cursor()
        cursor.execute("""
            SELECT * FROM documents 
            WHERE filename LIKE ? OR metadata LIKE ?
            ORDER BY upload_date DESC
        """, (f'%{query}%', f'%{query}%'))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]