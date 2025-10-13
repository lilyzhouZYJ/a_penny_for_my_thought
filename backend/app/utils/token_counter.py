import tiktoken
from typing import Dict, List

from app.models import Message

class TokenCounter:
    """
    Counts tokens for LLM context management.
    
    Uses tiktoken to accurately count tokens for OpenAI models.
    """
    
    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize token counter.
        
        Args:
            model: Model name to get correct encoding
        """
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    def count_message_tokens(self, message: Message) -> int:
        """
        Count tokens in a message.
        
        Args:
            message: Message object
        
        Returns:
            Approximate token count (includes role overhead)
        """
        # OpenAI counts role + content + some overhead
        role_tokens = self.count_tokens(message.role)
        content_tokens = self.count_tokens(message.content)
        
        # Add overhead (approximately 4 tokens per message for formatting)
        return role_tokens + content_tokens + 4
    
    def count_messages_tokens(self, messages: List[Message]) -> int:
        """
        Count total tokens in a list of messages.
        
        Args:
            messages: List of messages
        
        Returns:
            Total token count
        """
        return sum(self.count_message_tokens(msg) for msg in messages)
    
    def count_dict_message_tokens(self, message: Dict[str, str]) -> int:
        """
        Count tokens in a message dict (OpenAI API format).
        
        Args:
            message: Dict with 'role' and 'content'
        
        Returns:
            Token count
        """
        role_tokens = self.count_tokens(message.get('role', ''))
        content_tokens = self.count_tokens(message.get('content', ''))
        return role_tokens + content_tokens + 4
    
    def count_dict_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count total tokens in a list of message dicts.
        
        Args:
            messages: List of message dicts
        
        Returns:
            Total token count
        """
        return sum(self.count_dict_message_tokens(msg) for msg in messages)

