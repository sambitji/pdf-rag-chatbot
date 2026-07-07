"""File storage management."""
from pathlib import Path
from typing import Optional, BinaryIO
import shutil
from datetime import datetime
from utils.config import config
from utils.logger import get_logger
from utils.helpers import sanitize_filename, generate_file_hash

logger = get_logger(__name__)


class FileStorage:
    """Manage file storage operations."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize file storage.
        
        Args:
            base_path: Base directory for storage
        """
        self.base_path = base_path or config.storage_dir
        self.documents_dir = self.base_path / 'documents'
        self.temp_dir = self.base_path / 'temp'
        self.cache_dir = self.base_path / 'cache'
        
        # Create directories
        self._setup_directories()
        
        logger.info(f"Initialized file storage at: {self.base_path}")
    
    def _setup_directories(self):
        """Create storage directories."""
        for directory in [
            self.documents_dir,
            self.documents_dir / 'pdf',
            self.documents_dir / 'docx',
            self.documents_dir / 'txt',
            self.temp_dir,
            self.cache_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_file(
        self,
        file: BinaryIO,
        filename: str,
        file_type: str = 'pdf',
        use_hash: bool = True
    ) -> Path:
        """
        Save uploaded file.
        
        Args:
            file: File object
            filename: Original filename
            file_type: File type (pdf, docx, txt)
            use_hash: Whether to use hash in filename
            
        Returns:
            Path to saved file
        """
        try:
            # Sanitize filename
            safe_filename = sanitize_filename(filename)
            
            # Determine destination
            dest_dir = self.documents_dir / file_type
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to temp first
            temp_path = self.temp_dir / safe_filename
            with open(temp_path, 'wb') as f:
                shutil.copyfileobj(file, f)
            
            # Generate hash if needed
            if use_hash:
                file_hash = generate_file_hash(temp_path)
                name_parts = safe_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    safe_filename = f"{name_parts[0]}_{file_hash[:8]}.{name_parts[1]}"
                else:
                    safe_filename = f"{safe_filename}_{file_hash[:8]}"
            
            # Move to final location
            final_path = dest_dir / safe_filename
            shutil.move(str(temp_path), str(final_path))
            
            logger.info(f"Saved file: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    def get_file(self, filename: str, file_type: str = 'pdf') -> Optional[Path]:
        """
        Get file path.
        
        Args:
            filename: Filename
            file_type: File type
            
        Returns:
            Path to file or None
        """
        file_path = self.documents_dir / file_type / filename
        return file_path if file_path.exists() else None
    
    def delete_file(self, filepath: Path) -> bool:
        """
        Delete file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Success status
        """
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted file: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def list_files(self, file_type: str = None) -> list:
        """
        List files in storage.
        
        Args:
            file_type: Filter by file type
            
        Returns:
            List of file paths
        """
        if file_type:
            directory = self.documents_dir / file_type
            if directory.exists():
                return list(directory.glob('*'))
        else:
            files = []
            for subdir in self.documents_dir.iterdir():
                if subdir.is_dir():
                    files.extend(subdir.glob('*'))
            return files
        return []
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_type': {}
        }
        
        for file_type_dir in self.documents_dir.iterdir():
            if file_type_dir.is_dir():
                files = list(file_type_dir.glob('*'))
                size = sum(f.stat().st_size for f in files if f.is_file())
                
                stats['by_type'][file_type_dir.name] = {
                    'count': len(files),
                    'size': size
                }
                stats['total_files'] += len(files)
                stats['total_size'] += size
        
        return stats
    
    def cleanup_temp(self, older_than_hours: int = 24):
        """
        Clean up temporary files.
        
        Args:
            older_than_hours: Delete files older than this
        """
        logger.info("Cleaning up temporary files...")
        
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        deleted = 0
        
        for file in self.temp_dir.glob('*'):
            if file.is_file() and file.stat().st_mtime < cutoff_time:
                try:
                    file.unlink()
                    deleted += 1
                except Exception as e:
                    logger.error(f"Error deleting {file}: {e}")
        
        logger.info(f"Deleted {deleted} temporary files")