"""Unit tests for TokenCounter utility."""

import pytest
from app.models import Message
from app.utils.token_counter import TokenCounter


class TestTokenCounter:
    """Tests for TokenCounter class."""
    
    def test_initialization(self):
        """Test TokenCounter initializes with correct model."""
        counter = TokenCounter(model="gpt-4o")
        assert counter.encoding is not None
    
    def test_count_tokens_simple(self):
        """Test counting tokens in simple text."""
        counter = TokenCounter()
        
        # Simple text
        tokens = counter.count_tokens("Hello world")
        assert tokens > 0
        assert tokens < 10  # Should be around 2-3 tokens
    
    def test_count_tokens_empty(self):
        """Test counting tokens in empty string."""
        counter = TokenCounter()
        tokens = counter.count_tokens("")
        assert tokens == 0
    
    def test_count_message_tokens(self):
        """Test counting tokens in a Message object."""
        counter = TokenCounter()
        
        msg = Message(
            role="user",
            content="This is a test message with some content"
        )
        
        tokens = counter.count_message_tokens(msg)
        
        # Should be > 0 (content + role + overhead)
        assert tokens > 5
        # Should include overhead (~4 tokens)
        assert tokens > counter.count_tokens(msg.content)
    
    def test_count_messages_tokens(self):
        """Test counting tokens in multiple messages."""
        counter = TokenCounter()
        
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
            Message(role="user", content="How are you?")
        ]
        
        total = counter.count_messages_tokens(messages)
        
        # Should be sum of individual messages
        individual_sum = sum(counter.count_message_tokens(m) for m in messages)
        assert total == individual_sum
        
        # Should be greater than zero
        assert total > 0
    
    def test_count_dict_message_tokens(self):
        """Test counting tokens in OpenAI format message dict."""
        counter = TokenCounter()
        
        msg_dict = {"role": "user", "content": "Hello world"}
        tokens = counter.count_dict_message_tokens(msg_dict)
        
        assert tokens > 0
    
    def test_count_dict_messages_tokens(self):
        """Test counting tokens in list of message dicts."""
        counter = TokenCounter()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        
        total = counter.count_dict_messages_tokens(messages)
        assert total > 0
    
    def test_longer_text_has_more_tokens(self):
        """Test that longer text has more tokens."""
        counter = TokenCounter()
        
        short_text = "Hi"
        long_text = "This is a much longer piece of text with many more words and tokens."
        
        short_tokens = counter.count_tokens(short_text)
        long_tokens = counter.count_tokens(long_text)
        
        assert long_tokens > short_tokens

