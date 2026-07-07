"""Test case management for RAG evaluation."""
from typing import List, Dict, Any
from pathlib import Path
import json
from utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseManager:
    """Manage test cases for evaluation."""
    
    def __init__(self):
        """Initialize test case manager."""
        self.test_cases = []
    
    def add_test_case(
        self,
        query: str,
        expected_answer: str = None,
        relevant_docs: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Add a test case.
        
        Args:
            query: Test query
            expected_answer: Expected answer (for generation metrics)
            relevant_docs: List of relevant document IDs (for retrieval metrics)
            metadata: Additional metadata
        """
        test_case = {
            'query': query,
            'expected_answer': expected_answer,
            'relevant_docs': relevant_docs or [],
            'metadata': metadata or {}
        }
        self.test_cases.append(test_case)
        logger.debug(f"Added test case: {query[:50]}...")
    
    def load_from_file(self, filepath: Path):
        """Load test cases from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self.test_cases = data
            elif isinstance(data, dict) and 'test_cases' in data:
                self.test_cases = data['test_cases']
            
            logger.info(f"Loaded {len(self.test_cases)} test cases from {filepath}")
        except Exception as e:
            logger.error(f"Error loading test cases: {e}")
    
    def save_to_file(self, filepath: Path):
        """Save test cases to JSON file."""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(self.test_cases, f, indent=2)
            
            logger.info(f"Saved {len(self.test_cases)} test cases to {filepath}")
        except Exception as e:
            logger.error(f"Error saving test cases: {e}")
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases."""
        return self.test_cases
    
    def create_default_test_suite(self) -> List[Dict[str, Any]]:
        """Create default test suite."""
        default_cases = [
            {
                'query': 'What is the main topic of the document?',
                'expected_answer': 'The document discusses...',
                'relevant_docs': ['1', '2'],
                'metadata': {'category': 'general', 'difficulty': 'easy'}
            },
            {
                'query': 'Summarize the key points',
                'expected_answer': 'The key points are...',
                'relevant_docs': ['1', '2', '3'],
                'metadata': {'category': 'summarization', 'difficulty': 'medium'}
            },
            {
                'query': 'What are the specific requirements mentioned?',
                'expected_answer': 'The requirements include...',
                'relevant_docs': ['5', '6'],
                'metadata': {'category': 'detail', 'difficulty': 'medium'}
            },
            {
                'query': 'Compare the approaches discussed',
                'expected_answer': 'The approaches differ in...',
                'relevant_docs': ['3', '4', '5'],
                'metadata': {'category': 'comparison', 'difficulty': 'hard'}
            },
            {
                'query': 'What is the conclusion?',
                'expected_answer': 'The conclusion states...',
                'relevant_docs': ['10'],
                'metadata': {'category': 'conclusion', 'difficulty': 'easy'}
            }
        ]
        
        self.test_cases = default_cases
        return default_cases