"""Unit tests for RAG conversation chunking."""

import pytest
from datetime import datetime

from app.models import Message
from app.services.rag_service import RAGService


class TestRAGChunking:
    """Tests for conversation chunking logic."""
    
    def test_chunk_conversation_basic(self):
        """Test basic chunking of user+assistant pairs."""
        messages = [
            Message(id="1", role="user", content="Question 1"),
            Message(id="2", role="assistant", content="Answer 1"),
            Message(id="3", role="user", content="Question 2"),
            Message(id="4", role="assistant", content="Answer 2"),
        ]
        
        # Create RAGService instance (we'll only test chunking, not storage)
        rag_service = RAGService(vector_storage=None, embeddings=None)
        
        chunks = rag_service._chunk_conversation(messages)
        
        # Should create 2 chunks (2 pairs)
        assert len(chunks) == 2
        
        # Check first chunk
        assert "User: Question 1" in chunks[0]['content']
        assert "Assistant: Answer 1" in chunks[0]['content']
        assert chunks[0]['message_ids'] == ["1", "2"]
        
        # Check second chunk
        assert "User: Question 2" in chunks[1]['content']
        assert "Assistant: Answer 2" in chunks[1]['content']
        assert chunks[1]['message_ids'] == ["3", "4"]
    
    def test_chunk_conversation_odd_number_messages(self):
        """Test chunking when there's an odd number of messages."""
        messages = [
            Message(id="1", role="user", content="Q1"),
            Message(id="2", role="assistant", content="A1"),
            Message(id="3", role="user", content="Q2"),  # No response yet
        ]
        
        rag_service = RAGService(vector_storage=None, embeddings=None)
        chunks = rag_service._chunk_conversation(messages)
        
        # Should only create 1 chunk (only complete pair)
        assert len(chunks) == 1
        assert chunks[0]['message_ids'] == ["1", "2"]
    
    def test_chunk_conversation_empty(self):
        """Test chunking empty conversation."""
        messages = []
        
        rag_service = RAGService(vector_storage=None, embeddings=None)
        chunks = rag_service._chunk_conversation(messages)
        
        assert chunks == []
    
    def test_chunk_conversation_single_message(self):
        """Test chunking with only one message."""
        messages = [
            Message(id="1", role="user", content="Hello")
        ]
        
        rag_service = RAGService(vector_storage=None, embeddings=None)
        chunks = rag_service._chunk_conversation(messages)
        
        # No complete pairs
        assert chunks == []
    
    def test_chunk_conversation_preserves_content(self):
        """Test that chunking preserves message content."""
        messages = [
            Message(id="1", role="user", content="This is a detailed question with multiple sentences. It contains important context."),
            Message(id="2", role="assistant", content="Here's a comprehensive answer that addresses your question fully."),
        ]
        
        rag_service = RAGService(vector_storage=None, embeddings=None)
        chunks = rag_service._chunk_conversation(messages)
        
        assert len(chunks) == 1
        
        # Full content should be preserved
        chunk_content = chunks[0]['content']
        assert "detailed question with multiple sentences" in chunk_content
        assert "comprehensive answer" in chunk_content
    
    def test_chunk_conversation_skips_system_messages(self):
        """Test that system messages don't create chunks."""
        messages = [
            Message(id="1", role="system", content="System message"),
            Message(id="2", role="user", content="User message"),
            Message(id="3", role="assistant", content="Assistant message"),
        ]
        
        rag_service = RAGService(vector_storage=None, embeddings=None)
        chunks = rag_service._chunk_conversation(messages)
        
        # Should create 1 chunk (user+assistant, skipping system)
        assert len(chunks) == 1
        assert chunks[0]['message_ids'] == ["2", "3"]
        assert "System message" not in chunks[0]['content']

