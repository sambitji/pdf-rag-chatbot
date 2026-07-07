# RAG System Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [API Reference](#api-reference)
6. [Deployment](#deployment)
7. [Contributing](#contributing)

## Architecture Overview

The RAG (Retrieval-Augmented Generation) system consists of several key components:

### Components

- **Document Ingestion**: Processes PDFs, DOCX, and other formats
- **Vector Database**: ChromaDB for semantic search
- **Metadata Database**: SQLite for document tracking
- **Cache Layer**: Redis for performance optimization
- **Multi-Agent System**: Specialized agents for different tasks
- **REST API**: FastAPI backend
- **Web UI**: Streamlit frontend

### Data Flow