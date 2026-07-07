"""Benchmark script for performance testing."""
import sys
from pathlib import Path
import time
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rag_pipeline import RAGPipeline
from utils.logger import setup_logger

logger = setup_logger('benchmark')


def benchmark_queries(rag_pipeline: RAGPipeline, queries: List[str]):
    """Benchmark query performance."""
    logger.info("Starting query benchmark...")
    
    results = []
    
    for query in queries:
        start_time = time.time()
        
        result = rag_pipeline.query(query)
        
        elapsed = time.time() - start_time
        
        results.append({
            'query': query,
            'time': elapsed,
            'success': result['success']
        })
        
        logger.info(f"Query: {query[:50]}... | Time: {elapsed:.3f}s")
    
    # Calculate statistics
    times = [r['time'] for r in results]
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    logger.info("=" * 50)
    logger.info("Benchmark Results:")
    logger.info(f"Total Queries: {len(queries)}")
    logger.info(f"Avg Time: {avg_time:.3f}s")
    logger.info(f"Min Time: {min_time:.3f}s")
    logger.info(f"Max Time: {max_time:.3f}s")


def main():
    """Run benchmarks."""
    # Test queries
    test_queries = [
        "What is the main topic of the document?",
        "Summarize the key points",
        "What are the recommendations?",
        "Who are the stakeholders mentioned?",
        "What is the timeline discussed?"
    ]
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline()
    
    # Run benchmark
    benchmark_queries(rag_pipeline, test_queries)


if __name__ == "__main__":
    main()