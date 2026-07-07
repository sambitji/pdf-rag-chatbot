"""Question-answering specialist agent."""
from typing import Dict, Any, List
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from utils.logger import get_logger
from utils.helpers import extract_page_numbers

logger = get_logger(__name__)


class QAAgent:
    """Specialized agent for question answering."""
    
    def __init__(self, llm, retriever):
        """
        Initialize QA agent.
        
        Args:
            llm: Language model
            retriever: Document retriever
        """
        self.llm = llm
        self.retriever = retriever
        
        # QA prompt template
        self.prompt_template = """You are a helpful assistant answering questions based on provided documents.

Use the following pieces of context to answer the question at the end.
If you don't know the answer from the context, just say that you don't know.
Always cite the page number(s) when providing answers.

Context:
{context}

Question: {question}

Detailed Answer:"""
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": self.prompt},
            return_source_documents=True
        )
        
        logger.info("Initialized QA agent")
    
    def answer(self, question: str) -> Dict[str, Any]:
        """
        Answer a question.
        
        Args:
            question: User question
            
        Returns:
            Answer with sources
        """
        try:
            logger.info(f"QA Agent processing: {question[:100]}...")
            
            result = self.qa_chain({"query": question})
            
            answer = result['result']
            source_docs = result['source_documents']
            pages = extract_page_numbers(source_docs)
            
            response = {
                'success': True,
                'answer': answer,
                'sources': [
                    {
                        'content': doc.page_content[:200] + "...",
                        'page': doc.metadata.get('page'),
                        'source': doc.metadata.get('source', 'Unknown')
                    }
                    for doc in source_docs
                ],
                'pages': pages,
                'agent': 'QA'
            }
            
            logger.info(f"QA Agent answered with {len(source_docs)} sources")
            return response
            
        except Exception as e:
            logger.error(f"QA Agent error: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'QA'
            }
    
    def multi_hop_answer(self, question: str, max_hops: int = 3) -> Dict[str, Any]:
        """
        Answer complex multi-hop questions.
        
        Args:
            question: Complex question requiring multiple reasoning steps
            max_hops: Maximum reasoning hops
            
        Returns:
            Answer with reasoning chain
        """
        reasoning_chain = []
        current_question = question
        
        for hop in range(max_hops):
            result = self.answer(current_question)
            
            if not result['success']:
                break
            
            reasoning_chain.append({
                'hop': hop + 1,
                'question': current_question,
                'answer': result['answer'],
                'sources': result['pages']
            })
            
            # Check if we need another hop
            if "need more information" not in result['answer'].lower():
                break
            
            # Generate follow-up question
            current_question = self._generate_followup(question, result['answer'])
        
        return {
            'success': True,
            'final_answer': reasoning_chain[-1]['answer'] if reasoning_chain else "Unable to answer",
            'reasoning_chain': reasoning_chain,
            'agent': 'QA-MultiHop'
        }
    
    def _generate_followup(self, original_question: str, partial_answer: str) -> str:
        """Generate follow-up question for multi-hop reasoning."""
        prompt = f"""Given this original question and partial answer, what follow-up question should be asked?

Original Question: {original_question}
Partial Answer: {partial_answer}

Follow-up Question:"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except:
            return original_question