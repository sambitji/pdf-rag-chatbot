"""Data migration script."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.metadata_store import MetadataStore
from utils.logger import setup_logger

logger = setup_logger('migrate_data')


def migrate():
    """Run database migrations."""
    logger.info("Starting database migration...")
    
    metadata_store = MetadataStore()
    
    # Read and execute migration files
    migrations_dir = Path(__file__).parent.parent / 'database' / 'migrations'
    
    migration_files = sorted(migrations_dir.glob('*.sql'))
    
    for migration_file in migration_files:
        logger.info(f"Running migration: {migration_file.name}")
        
        try:
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            # Execute SQL
            metadata_store.conn.executescript(sql)
            metadata_store.conn.commit()
            
            logger.info(f"✓ Completed: {migration_file.name}")
        
        except Exception as e:
            logger.error(f"✗ Failed: {migration_file.name} - {e}")
            metadata_store.conn.rollback()
    
    logger.info("Migration complete!")


if __name__ == "__main__":
    migrate()