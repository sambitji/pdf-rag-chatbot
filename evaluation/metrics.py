"""Evaluation metrics for RAG system."""
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer, util
from utils.logger import get_logger

logger = get_logger(__name__)


class RAGMetrics:
    """Calculate various metrics for RAG evaluation."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'],
            use_stemmer=True
        )
        try:
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Initialized semantic similarity model")
        except Exception as e:
            logger.warning(f"Could not load semantic model: {e}")
            self.semantic_model = None
    
    def calculate_retrieval_metrics(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 5
    ) -> Dict[str, float]:
        """
        Calculate retrieval metrics.
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of relevant document IDs
            k: Top-k for precision/recall
            
        Returns:
            Dictionary of metrics
        """
        retrieved_set = set(retrieved_docs[:k])
        relevant_set = set(relevant_docs)
        
        # True positives
        tp = len(retrieved_set.intersection(relevant_set))
        
        # Precision@k
        precision = tp / k if k > 0 else 0
        
        # Recall@k
        recall = tp / len(relevant_set) if len(relevant_set) > 0 else 0
        
        # F1@k
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Mean Reciprocal Rank (MRR)
        mrr = 0
        for i, doc in enumerate(retrieved_docs[:k], 1):
            if doc in relevant_set:
                mrr = 1 / i
                break
        
        # Average Precision
        ap = 0
        relevant_count = 0
        for i, doc in enumerate(retrieved_docs[:k], 1):
            if doc in relevant_set:
                relevant_count += 1
                ap += relevant_count / i
        ap = ap / len(relevant_set) if len(relevant_set) > 0 else 0
        
        # Normalized Discounted Cumulative Gain (NDCG)
        ndcg = self._calculate_ndcg(retrieved_docs[:k], relevant_docs)
        
        return {
            'precision@k': precision,
            'recall@k': recall,
            'f1@k': f1,
            'mrr': mrr,
            'map': ap,
            'ndcg@k': ndcg
        }
    
    def _calculate_ndcg(
        self,
        retrieved: List[str],
        relevant: List[str]
    ) -> float:
        """Calculate NDCG score."""
        def dcg(relevances):
            return sum(
                (2 ** rel - 1) / np.log2(i + 2)
                for i, rel in enumerate(relevances)
            )
        
        # Actual DCG
        actual_relevances = [1 if doc in relevant else 0 for doc in retrieved]
        actual_dcg = dcg(actual_relevances)
        
        # Ideal DCG
        ideal_relevances = sorted(actual_relevances, reverse=True)
        ideal_dcg = dcg(ideal_relevances)
        
        return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0
    
    def calculate_generation_metrics(
        self,
        generated: str,
        reference: str
    ) -> Dict[str, float]:
        """
        Calculate generation quality metrics.
        
        Args:
            generated: Generated answer
            reference: Reference answer
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # ROUGE scores
        rouge_scores = self.rouge_scorer.score(reference, generated)
        metrics['rouge1_f'] = rouge_scores['rouge1'].fmeasure
        metrics['rouge2_f'] = rouge_scores['rouge2'].fmeasure
        metrics['rougeL_f'] = rouge_scores['rougeL'].fmeasure
        
        # BLEU score (simplified)
        metrics['bleu'] = self._calculate_bleu(generated, reference)
        
        # Semantic similarity
        if self.semantic_model:
            metrics['semantic_similarity'] = self._calculate_semantic_similarity(
                generated,
                reference
            )
        
        # Length ratio
        metrics['length_ratio'] = len(generated.split()) / len(reference.split())
        
        return metrics
    
    def _calculate_bleu(self, generated: str, reference: str) -> float:
        """Calculate simplified BLEU score."""
        gen_words = generated.lower().split()
        ref_words = reference.lower().split()
        
        if not gen_words or not ref_words:
            return 0.0
        
        # Unigram precision
        matches = sum(1 for word in gen_words if word in ref_words)
        precision = matches / len(gen_words)
        
        # Brevity penalty
        bp = 1.0 if len(gen_words) >= len(ref_words) else np.exp(
            1 - len(ref_words) / len(gen_words)
        )
        
        return bp * precision
    
    def _calculate_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """Calculate semantic similarity using embeddings."""
        if not self.semantic_model:
            return 0.0
        
        try:
            emb1 = self.semantic_model.encode(text1, convert_to_tensor=True)
            emb2 = self.semantic_model.encode(text2, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(emb1, emb2).item()
            return similarity
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def calculate_faithfulness(
        self,
        answer: str,
        context: str
    ) -> float:
        """
        Calculate faithfulness score (answer grounded in context).
        
        Args:
            answer: Generated answer
            context: Retrieved context
            
        Returns:
            Faithfulness score (0-1)
        """
        if not self.semantic_model:
            # Fallback to word overlap
            answer_words = set(answer.lower().split())
            context_words = set(context.lower().split())
            overlap = len(answer_words.intersection(context_words))
            return overlap / len(answer_words) if answer_words else 0
        
        try:
            # Calculate semantic similarity between answer and context
            similarity = self._calculate_semantic_similarity(answer, context)
            return similarity
        except Exception as e:
            logger.error(f"Error calculating faithfulness: {e}")
            return 0.0
    
    def calculate_answer_relevance(
        self,
        answer: str,
        question: str
    ) -> float:
        """
        Calculate answer relevance to question.
        
        Args:
            answer: Generated answer
            question: User question
            
        Returns:
            Relevance score (0-1)
        """
        if not self.semantic_model:
            return 0.5  # Neutral score if no model
        
        try:
            similarity = self._calculate_semantic_similarity(answer, question)
            return similarity
        except Exception as e:
            logger.error(f"Error calculating answer relevance: {e}")
            return 0.0
    
    def calculate_context_relevance(
        self,
        context: str,
        question: str
    ) -> float:
        """
        Calculate context relevance to question.
        
        Args:
            context: Retrieved context
            question: User question
            
        Returns:
            Relevance score (0-1)
        """
        if not self.semantic_model:
            return 0.5
        
        try:
            similarity = self._calculate_semantic_similarity(context, question)
            return similarity
        except Exception as e:
            logger.error(f"Error calculating context relevance: {e}")
            return 0.0


def evaluate_retrieval(
    retrieved_docs: List[str],
    relevant_docs: List[str],
    k: int = 5
) -> Dict[str, float]:
    """Convenience function for retrieval evaluation."""
    metrics = RAGMetrics()
    return metrics.calculate_retrieval_metrics(retrieved_docs, relevant_docs, k)


def evaluate_generation(
    generated: str,
    reference: str
) -> Dict[str, float]:
    """Convenience function for generation evaluation."""
    metrics = RAGMetrics()
    return metrics.calculate_generation_metrics(generated, reference)