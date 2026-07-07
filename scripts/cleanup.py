"""Cleanup script."""
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import config
from utils.logger import setup_logger

logger = setup_logger('cleanup')


def cleanup_temp_files():
    """Clean temporary files."""
    logger.info("Cleaning temporary files...")
    
    if config.temp_dir.exists():
        for file in config.temp_dir.glob('*'):
            try:
                file.unlink()
                logger.debug(f"Deleted: {file.name}")
            except Exception as e:
                logger.error(f"Error deleting {file.name}: {e}")
    
    logger.info("Temporary files cleaned")


def cleanup_cache():
    """Clean cache directory."""
    logger.info("Cleaning cache...")
    
    if config.cache_dir.exists():
        for file in config.cache_dir.glob('*'):
            try:
                file.unlink()
                logger.debug(f"Deleted: {file.name}")
            except Exception as e:
                logger.error(f"Error deleting {file.name}: {e}")
    
    logger.info("Cache cleaned")


def cleanup_logs(days: int = 7):
    """Clean old log files."""
    logger.info(f"Cleaning logs older than {days} days...")
    
    import time
    current_time = time.time()
    cutoff = current_time - (days * 24 * 60 * 60)
    
    if config.logs_dir.exists():
        for file in config.logs_dir.glob('*.log*'):
            try:
                if file.stat().st_mtime < cutoff:
                    file.unlink()
                    logger.debug(f"Deleted old log: {file.name}")
            except Exception as e:
                logger.error(f"Error deleting {file.name}: {e}")
    
    logger.info("Old logs cleaned")


def main():
    """Run cleanup."""
    logger.info("Starting cleanup...")
    
    cleanup_temp_files()
    cleanup_cache()
    cleanup_logs(days=7)
    
    logger.info("Cleanup complete!")


if __name__ == "__main__":
    main()