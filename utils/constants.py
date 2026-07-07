"""Application constants."""
from enum import Enum


class FileType(str, Enum):
    """Supported file types."""
    PDF = 'pdf'
    DOCX = 'docx'
    TXT = 'txt'
    MD = 'md'
    HTML = 'html'


class ChunkingStrategy(str, Enum):
    """Document chunking strategies."""
    FIXED_SIZE = 'fixed_size'
    RECURSIVE = 'recursive'
    SEMANTIC = 'semantic'
    PARAGRAPH = 'paragraph'


class RetrievalMethod(str, Enum):
    """Retrieval methods."""
    VECTOR = 'vector'
    BM25 = 'bm25'
    HYBRID = 'hybrid'
    RERANK = 'rerank'


class AgentType(str, Enum):
    """Agent types."""
    ROUTER = 'router'
    QA = 'qa'
    SUMMARIZATION = 'summarization'
    COMPARISON = 'comparison'
    CITATION = 'citation'


# File size limits (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_BATCH_SIZE = 100 * 1024 * 1024  # 100MB

# Processing limits
MAX_CHUNK_SIZE = 2000
MIN_CHUNK_SIZE = 100
MAX_CHUNKS_PER_DOC = 10000

# Retrieval limits
MAX_TOP_K = 20
DEFAULT_TOP_K = 5

# Cache settings
DEFAULT_CACHE_TTL = 3600  # 1 hour
MAX_CACHE_SIZE = 1000

# Model settings
SUPPORTED_MODELS = [
    'gpt-4-turbo-preview',
    'gpt-4',
    'gpt-3.5-turbo',
    'gpt-3.5-turbo-16k'
]

EMBEDDING_MODELS = [
    'text-embedding-3-small',
    'text-embedding-3-large',
    'text-embedding-ada-002'
]

# Prompts
SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on provided documents.
Always cite the source and page number when providing answers.
If you don't know the answer from the context, say so - don't make up information."""

QA_PROMPT_TEMPLATE = """Answer the question based only on the following context:

Context:
{context}

Question: {question}

Answer: """

SUMMARIZATION_PROMPT = """Summarize the following document in a concise manner:

{text}

Summary: """