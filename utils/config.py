"""Configuration management."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """Application configuration."""
    
    # OpenAI
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    openai_model: str = Field(default='deepseek-v3.2', env='OPENAI_MODEL')
    embedding_model: str = Field(default='deepseek-v3.2', env='EMBEDDING_MODEL')
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    storage_dir: Path = base_dir / 'storage'
    documents_dir: Path = storage_dir / 'documents'
    vectordb_dir: Path = storage_dir / 'vectordb'
    metadata_db_path: Path = storage_dir / 'metadata' / 'metadata.db'
    cache_dir: Path = storage_dir / 'cache'
    temp_dir: Path = storage_dir / 'temp'
    logs_dir: Path = base_dir / 'logs'
    
    # Database
    chroma_db_path: str = Field(default='./storage/vectordb', env='CHROMA_DB_PATH')
    redis_host: str = Field(default='localhost', env='REDIS_HOST')
    redis_port: int = Field(default=6379, env='REDIS_PORT')
    redis_password: Optional[str] = Field(default=None, env='REDIS_PASSWORD')
    
    # Processing
    chunk_size: int = Field(default=1000, env='CHUNK_SIZE')
    chunk_overlap: int = Field(default=200, env='CHUNK_OVERLAP')
    top_k_results: int = Field(default=5, env='TOP_K_RESULTS')
    temperature: float = Field(default=0.0, env='TEMPERATURE')
    
    # API
    api_host: str = Field(default='0.0.0.0', env='API_HOST')
    api_port: int = Field(default=8000, env='API_PORT')
    api_secret_key: str = Field(..., env='API_SECRET_KEY')
    jwt_algorithm: str = Field(default='HS256', env='JWT_ALGORITHM')
    jwt_expiration: int = Field(default=3600, env='JWT_EXPIRATION')
    
    # OCR
    tesseract_path: str = Field(default='/usr/bin/tesseract', env='TESSERACT_PATH')
    ocr_language: str = Field(default='eng', env='OCR_LANGUAGE')
    
    # Performance
    max_workers: int = Field(default=4, env='MAX_WORKERS')
    enable_cache: bool = Field(default=True, env='ENABLE_CACHE')
    cache_ttl: int = Field(default=3600, env='CACHE_TTL')
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env='ENABLE_METRICS')
    prometheus_port: int = Field(default=9090, env='PROMETHEUS_PORT')
    
    # Environment
    environment: str = Field(default='development', env='ENVIRONMENT')
    debug: bool = Field(default=True, env='DEBUG')
    log_level: str = Field(default='INFO', env='LOG_LEVEL')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_directories()
        if self.is_production:
            if self.api_secret_key == 'your-secret-key-change-this-in-production' or not self.api_secret_key:
                raise ValueError("API_SECRET_KEY must be changed to a secure value in production environment!")
    
    def _create_directories(self):
        """Create necessary directories."""
        for directory in [
            self.storage_dir,
            self.documents_dir,
            self.vectordb_dir,
            self.cache_dir,
            self.temp_dir,
            self.logs_dir,
            self.metadata_db_path.parent
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == 'development'


# Global config instance
config = Config()