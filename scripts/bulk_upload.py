"""Bulk document upload script."""
import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rag_pipeline import RAGPipeline
from database.metadata_store import MetadataStore
from utils.logger import setup_logger
from utils.helpers import generate_file_hash

logger = setup_logger('bulk_upload')


def bulk_upload(directory: Path, pattern: str = "*.pdf"):
    """
    Bulk upload documents from directory.
    
    Args:
        directory: Directory containing documents
        pattern: File pattern to match
    """
    logger.info(f"Starting bulk upload from: {directory}")
    
    # Initialize components
    rag_pipeline = RAGPipeline()
    metadata_store = MetadataStore()
    
    # Find files
    files = list(directory.glob(pattern))
    logger.info(f"Found {len(files)} files matching pattern: {pattern}")
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for file_path in files:
        try:
            logger.info(f"Processing: {file_path.name}")
            
            # Generate hash
            file_hash = generate_file_hash(file_path)
            
            # Check if already exists
            existing = metadata_store.get_document_by_hash(file_hash)
            if existing:
                logger.warning(f"Skipping (already exists): {file_path.name}")
                continue
            
            # Add to metadata
            doc_id = metadata_store.add_document(
                filename=file_path.name,
                file_path=str(file_path),
                file_hash=file_hash,
                file_size=file_path.stat().st_size,
                file_type=file_path.suffix.lstrip('.')
            )
            
            # Process document
            result = rag_pipeline.process_document(file_path)
            
            if result['success']:
                metadata_store.update_document_status(
                    doc_id,
                    'completed',
                    result['chunks']
                )
                success_count += 1
                logger.info(f"✓ Processed: {file_path.name} ({result['chunks']} chunks)")
            else:
                metadata_store.update_document_status(doc_id, 'failed')
                error_count += 1
                logger.error(f"✗ Failed: {file_path.name} - {result.get('error')}")
        
        except Exception as e:
            error_count += 1
            logger.error(f"✗ Error processing {file_path.name}: {e}")
    
    # Summary
    logger.info("=" * 50)
    logger.info(f"Bulk upload complete!")
    logger.info(f"Success: {success_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Total: {len(files)}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bulk upload documents")
    parser.add_argument("directory", type=Path, help="Directory containing documents")
    parser.add_argument("--pattern", default="*.pdf", help="File pattern (default: *.pdf)")
    
    args = parser.parse_args()
    
    if not args.directory.exists():
        logger.error(f"Directory not found: {args.directory}")
        return
    
    bulk_upload(args.directory, args.pattern)


if __name__ == "__main__":
    main()