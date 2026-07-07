"""Named entity recognition and extraction."""
from typing import List, Dict
import spacy
from utils.logger import get_logger

logger = get_logger(__name__)


class EntityExtractor:
    """Extract named entities from text."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize entity extractor.
        
        Args:
            model_name: spaCy model name
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Initialized entity extractor with {model_name}")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of entity types and values
        """
        if not self.nlp:
            return {}
        
        try:
            doc = self.nlp(text)
            
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append(ent.text)
            
            # Remove duplicates
            for label in entities:
                entities[label] = list(set(entities[label]))
            
            logger.debug(f"Extracted {len(doc.ents)} entities")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using noun chunks."""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            phrases = [chunk.text for chunk in doc.noun_chunks]
            return list(set(phrases))
        except Exception as e:
            logger.error(f"Error extracting phrases: {e}")
            return []