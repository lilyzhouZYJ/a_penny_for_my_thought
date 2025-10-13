"""Unit tests for Pydantic models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models import (
    Message,
    ChatRequest,
    ChatResponse,
    RetrievedContext,
    JournalMetadata,
    Journal,
    CreateJournalRequest,
)


class TestMessageModel:
    """Tests for Message model."""
    
    def test_message_creation_with_defaults(self):
        """Test message creates with auto-generated id and timestamp."""
        msg = Message(role="user", content="Hello")
        
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.id is not None
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata is None
    
    def test_message_with_all_fields(self):
        """Test message with all fields specified."""
        timestamp = datetime.now()
        msg = Message(
            id="custom-id",
            role="assistant",
            content="Hi there!",
            timestamp=timestamp,
            metadata={"key": "value"}
        )
        
        assert msg.id == "custom-id"
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"
        assert msg.timestamp == timestamp
        assert msg.metadata == {"key": "value"}
    
    def test_message_role_validation(self):
        """Test that only valid roles are accepted."""
        # Valid roles
        for role in ["user", "assistant", "system"]:
            msg = Message(role=role, content="test")
            assert msg.role == role
        
        # Invalid role should fail
        with pytest.raises(ValidationError):
            Message(role="invalid", content="test")


class TestChatRequest:
    """Tests for ChatRequest model."""
    
    def test_chat_request_valid(self):
        """Test valid chat request."""
        req = ChatRequest(
            message="Hello",
            session_id="session-123",
            use_rag=True,
            stream=False
        )
        
        assert req.message == "Hello"
        assert req.session_id == "session-123"
        assert req.use_rag is True
        assert req.stream is False
    
    def test_chat_request_defaults(self):
        """Test chat request with defaults."""
        req = ChatRequest(
            message="Hello",
            session_id="session-123"
        )
        
        assert req.use_rag is True  # Default
        assert req.stream is False  # Default
    
    def test_chat_request_empty_message_fails(self):
        """Test that empty message fails validation."""
        with pytest.raises(ValidationError):
            ChatRequest(message="", session_id="session-123")
    
    def test_chat_request_too_long_message_fails(self):
        """Test that overly long message fails validation."""
        long_message = "a" * 10001  # Over 10,000 char limit
        
        with pytest.raises(ValidationError):
            ChatRequest(message=long_message, session_id="session-123")


class TestChatResponse:
    """Tests for ChatResponse model."""
    
    def test_chat_response_without_context(self):
        """Test chat response without retrieved context."""
        msg = Message(role="assistant", content="Hello!")
        response = ChatResponse(message=msg)
        
        assert response.message == msg
        assert response.retrieved_context == []
        assert response.metadata == {}
    
    def test_chat_response_with_context(self):
        """Test chat response with retrieved context."""
        msg = Message(role="assistant", content="Hello!")
        context = RetrievedContext(
            content="Previous conversation...",
            metadata={"date": "2025-01-01"},
            similarity_score=0.85
        )
        
        response = ChatResponse(
            message=msg,
            retrieved_context=[context],
            metadata={"tokens": 100}
        )
        
        assert len(response.retrieved_context) == 1
        assert response.retrieved_context[0].similarity_score == 0.85
        assert response.metadata["tokens"] == 100


class TestJournalModels:
    """Tests for journal models."""
    
    def test_journal_metadata(self):
        """Test JournalMetadata model."""
        metadata = JournalMetadata(
            id="journal-1",
            filename="2025-01-01_10-00-00_test.md",
            title="Test Journal",
            date=datetime.now(),
            message_count=10,
            duration_seconds=300
        )
        
        assert metadata.id == "journal-1"
        assert metadata.message_count == 10
        assert metadata.duration_seconds == 300
    
    def test_journal_full(self):
        """Test full Journal model."""
        msg = Message(role="user", content="Test")
        journal = Journal(
            id="journal-1",
            filename="test.md",
            title="Test",
            date=datetime.now(),
            message_count=1,
            messages=[msg],
            raw_content="# Test\n\nUser: Test"
        )
        
        assert len(journal.messages) == 1
        assert journal.raw_content.startswith("# Test")
    
    def test_create_journal_request(self):
        """Test CreateJournalRequest model."""
        msg = Message(role="user", content="Test")
        
        # New journal (no journal_id)
        req = CreateJournalRequest(
            session_id="session-123",
            messages=[msg]
        )
        
        assert req.session_id == "session-123"
        assert req.journal_id is None
        assert req.title is None
        assert len(req.messages) == 1
    
    def test_create_journal_request_update(self):
        """Test CreateJournalRequest for updating existing journal."""
        msg = Message(role="user", content="Test")
        
        # Update existing journal
        req = CreateJournalRequest(
            session_id="session-123",
            journal_id="journal-1",
            messages=[msg],
            title="Existing Title"
        )
        
        assert req.journal_id == "journal-1"
        assert req.title == "Existing Title"

