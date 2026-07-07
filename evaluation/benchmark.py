"""Benchmark suite for RAG system."""
import time
from typing import List, Dict, Any
from pathlib import Path
import json
from core.rag_pipeline import RAGPipeline
from evaluation.metrics import RAGMetrics
from utils.logger import get_logger

logger = get_logger(__name__)


class BenchmarkSuite:
    """Run comprehensive benchmarks on RAG system."""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Initialize benchmark suite.
        
        Args:
            rag_pipeline: RAG pipeline to benchmark
        """
        self.pipeline = rag_pipeline
        self.metrics = RAGMetrics()
        self.results = []
    
    def run_benchmark(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run benchmark on test cases.
        
        Args:
            test_cases: List of test cases with queries and expected answers
            
        Returns:
            Benchmark results
        """
        logger.info(f"Running benchmark on {len(test_cases)} test cases...")
        
        results = {
            'total_cases': len(test_cases),
            'successful': 0,
            'failed': 0,
            'total_time': 0,
            'avg_time': 0,
            'metrics': {
                'precision': [],
                'recall': [],
                'f1': [],
                'rouge1': [],
                'rouge2': [],
                'rougeL': [],
                'semantic_similarity': [],
                'faithfulness': [],
                'answer_relevance': []
            },
            'test_results': []
        }
        
        start_time = time.time()
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Running test case {i}/{len(test_cases)}")
            
            result = self._run_single_test(test_case)
            results['test_results'].append(result)
            
            if result['success']:
                results['successful'] += 1
                
                # Aggregate metrics
                for metric, value in result['metrics'].items():
                    if metric in results['metrics']:
                        results['metrics'][metric].append(value)
            else:
                results['failed'] += 1
        
        results['total_time'] = time.time() - start_time
        results['avg_time'] = results['total_time'] / len(test_cases)
        
        # Calculate average metrics
        for metric, values in results['metrics'].items():
            if values:
                results['metrics'][metric] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'std': self._calculate_std(values)
                }
        
        logger.info("Benchmark complete!")
        logger.info(f"Success rate: {results['successful']}/{results['total_cases']}")
        logger.info(f"Average time: {results['avg_time']:.3f}s")
        
        return results
    
    def _run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run single test case."""
        result = {
            'query': test_case['query'],
            'success': False,
            'time': 0,
            'metrics': {},
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Run query
            response = self.pipeline.query(test_case['query'])
            
            result['time'] = time.time() - start_time
            
            if not response['success']:
                result['error'] = response.get('error', 'Unknown error')
                return result
            
            # Calculate metrics
            generated_answer = response['answer']
            reference_answer = test_case.get('expected_answer', '')
            retrieved_context = ' '.join([
                src['content'] for src in response.get('sources', [])
            ])
            
            # Generation metrics
            if reference_answer:
                gen_metrics = self.metrics.calculate_generation_metrics(
                    generated_answer,
                    reference_answer
                )
                result['metrics'].update(gen_metrics)
            
            # Faithfulness
            if retrieved_context:
                result['metrics']['faithfulness'] = self.metrics.calculate_faithfulness(
                    generated_answer,
                    retrieved_context
                )
            
            # Answer relevance
            result['metrics']['answer_relevance'] = self.metrics.calculate_answer_relevance(
                generated_answer,
                test_case['query']
            )
            
            # Retrieval metrics
            if 'relevant_docs' in test_case:
                retrieved_docs = [str(p) for p in response.get('pages', [])]
                relevant_docs = test_case['relevant_docs']
                
                retrieval_metrics = self.metrics.calculate_retrieval_metrics(
                    retrieved_docs,
                    relevant_docs
                )
                result['metrics'].update(retrieval_metrics)
            
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Error in test case: {e}")
            result['error'] = str(e)
        
        return result
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def save_results(self, filepath: Path):
        """Save benchmark results to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def load_test_cases(self, filepath: Path) -> List[Dict[str, Any]]:
        """Load test cases from JSON file."""
        try:
            with open(filepath, 'r') as f:
                test_cases = json.load(f)
            logger.info(f"Loaded {len(test_cases)} test cases from {filepath}")
            return test_cases
        except Exception as e:
            logger.error(f"Error loading test cases: {e}")
            return []