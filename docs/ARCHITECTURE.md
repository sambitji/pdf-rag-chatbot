
### **`docs/ARCHITECTURE.md`**
```markdown
# System Architecture

## Overview

The RAG system follows a modular, microservices-inspired architecture.

## Components

### 1. Ingestion Layer
- **Purpose**: Process and prepare documents
- **Components**:
  - PDF Loader
  - OCR Loader
  - Multi-format Loader
  - Document Chunker

### 2. Storage Layer
- **Vector Database** (ChromaDB)
  - Stores document embeddings
  - Enables semantic search
- **Metadata Database** (SQLite)
  - Tracks documents
  - Logs queries
  - Stores analytics
- **Cache** (Redis)
  - Query caching
  - Embedding caching

### 3. Retrieval Layer
- **Vector Search**: Semantic similarity
- **BM25 Search**: Keyword-based
- **Hybrid Search**: Combined approach
- **Reranker**: Cross-encoder for relevance

### 4. Agent Layer
- **Router Agent**: Directs queries
- **QA Agent**: Answers questions
- **Summarization Agent**: Summarizes content
- **Comparison Agent**: Compares documents
- **Citation Agent**: Verifies sources

### 5. API Layer
- **REST API** (FastAPI)
  - Document management
  - Query endpoints
  - Authentication
  - Admin functions

### 6. Presentation Layer
- **Web UI** (Streamlit)
  - Chat interface
  - Document management
  - Analytics dashboard

## Data Flow

1. Document uploaded through UI/API
2. Document processed and chunked
3. Chunks embedded using OpenAI
4. Embeddings stored in ChromaDB
5. Metadata stored in SQLite
6. User submits query
7. Router determines query type
8. Appropriate agent handles query
9. Relevant documents retrieved
10. LLM generates response
11. Response returned with citations

## Scaling Considerations

- **Horizontal Scaling**: Multiple API/UI instances
- **Database Sharding**: Partition vector database
- **Caching**: Redis for frequently accessed data
- **Async Processing**: Celery for background tasks
- **Load Balancing**: Nginx for traffic distribution