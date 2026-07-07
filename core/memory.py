"""Conversation memory management."""
from typing import List, Dict, Optional
from datetime import datetime
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """Manage conversation history."""
    
    def __init__(self, max_messages: int = 10):
        """Initialize conversation memory."""
        self.max_messages = max_messages
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.conversations: Dict[str, List[Dict]] = {}
        logger.info(f"Initialized conversation memory (max: {max_messages})")
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add message to conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversations[session_id].append(message)
        
        # Trim to max messages
        if len(self.conversations[session_id]) > self.max_messages * 2:
            self.conversations[session_id] = self.conversations[session_id][-self.max_messages * 2:]
        
        logger.debug(f"Added {role} message to session {session_id}")
    
    def add_user_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add user message."""
        self.add_message(session_id, 'user', content, metadata)
        self.memory.chat_memory.add_user_message(content)
    
    def add_ai_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add AI message."""
        self.add_message(session_id, 'assistant', content, metadata)
        self.memory.chat_memory.add_ai_message(content)
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session."""
        return self.conversations.get(session_id, [])
    
    def get_context(self, session_id: str, max_turns: int = 5) -> str:
        """Get formatted conversation context."""
        history = self.get_history(session_id)
        recent = history[-max_turns * 2:] if history else []
        
        context_parts = []
        for msg in recent:
            role = "Human" if msg['role'] == 'user' else "AI"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str):
        """Clear conversation history for session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared session {session_id}")
    
    def clear_all(self):
        """Clear all conversations."""
        self.conversations.clear()
        self.memory.clear()
        logger.info("Cleared all conversations")