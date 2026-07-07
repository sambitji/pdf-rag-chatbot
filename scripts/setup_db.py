"""Setup database script."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.metadata_store import MetadataStore
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger('setup_db')


def main():
    """Setup database."""
    logger.info("Setting up database...")
    
    # Create metadata store (initializes tables)
    metadata_store = MetadataStore()
    
    logger.info("Database tables created successfully!")
    logger.info(f"Database location: {config.metadata_db_path}")
    
    # Create vector database directory
    config.vectordb_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Vector database directory created: {config.vectordb_dir}")
    
    logger.info("Setup complete!")


if __name__ == "__main__":
    main()