"""LLM interaction handler."""
from typing import Optional, Dict, Any
import time
from langchain_openai import ChatOpenAI
from langchain.callbacks import get_openai_callback
from utils.config import config
from utils.logger import get_logger
from utils.error_handlers import LLMError

logger = get_logger(__name__)


class LLMHandler:
    """Handle LLM interactions."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """Initialize LLM handler."""
        self.model = model or config.openai_model
        self.temperature = temperature if temperature is not None else config.temperature
        
        try:
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                openai_api_key=config.openai_api_key
            )
            logger.info(f"Initialized LLM: {self.model} (temp={self.temperature})")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise LLMError(f"LLM initialization failed: {e}")
    
    def generate(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response from LLM with retry handling."""
        last_error = None
        for attempt in range(3):
            try:
                logger.debug(f"Generating response for prompt: {prompt[:100]}... (attempt {attempt + 1})")

                with get_openai_callback() as cb:
                    response = self.llm.invoke(prompt, **kwargs)

                    result = {
                        'response': response.content,
                        'model': self.model,
                        'tokens': {
                            'prompt': cb.prompt_tokens,
                            'completion': cb.completion_tokens,
                            'total': cb.total_tokens
                        },
                        'cost': cb.total_cost
                    }

                    logger.info(
                        f"Generated response - Tokens: {cb.total_tokens}, "
                        f"Cost: ${cb.total_cost:.4f}"
                    )

                    return result

            except Exception as e:
                last_error = e
                logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(1)

        logger.error(f"Error generating response after retries: {last_error}")
        raise LLMError(f"Response generation failed: {last_error}")
    
    def stream_generate(self, prompt: str):
        """Stream response from LLM."""
        try:
            logger.debug("Starting streaming response")
            for chunk in self.llm.stream(prompt):
                yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            raise LLMError(f"Streaming failed: {e}")