"""Unit tests for ChatService with mocked dependencies."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.services.chat_service import ChatService
from app.models import Message, ChatResponse, RetrievedContext


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.complete = AsyncMock(return_value="AI response")
    mock.stream_complete = AsyncMock()
    return mock


@pytest.fixture
def mock_rag_service():
    """Create mock RAG service."""
    mock = Mock()
    mock.retrieve_context = AsyncMock(return_value=[
        RetrievedContext(
            content="Past conversation context",
            metadata={"date": "2025-01-01"},
            similarity_score=0.85
        )
    ])
    mock.index_conversation = AsyncMock()
    return mock


@pytest.fixture
def mock_journal_service():
    """Create mock journal service."""
    mock = Mock()
    mock.save_journal = AsyncMock()
    return mock


@pytest.fixture
def chat_service(mock_llm_service, mock_rag_service, mock_journal_service):
    """Create ChatService with mocked dependencies."""
    return ChatService(
        llm_service=mock_llm_service,
        rag_service=mock_rag_service,
        journal_service=mock_journal_service
    )


class TestChatService:
    """Tests for ChatService."""
    
    @pytest.mark.asyncio
    async def test_send_message_without_history(
        self,
        chat_service,
        mock_llm_service,
        mock_rag_service,
        mock_journal_service
    ):
        """Test sending message without conversation history."""
        response = await chat_service.send_message(
            message="Hello",
            session_id="session-123",
            conversation_history=[],
            use_rag=True
        )
        
        # Verify response
        assert isinstance(response, ChatResponse)
        assert response.message.role == "assistant"
        assert response.message.content == "AI response"
        
        # Verify RAG was called
        mock_rag_service.retrieve_context.assert_called_once()
        
        # Verify LLM was called
        mock_llm_service.complete.assert_called_once()
        
        # Verify auto-save was called
        mock_journal_service.save_journal.assert_called_once()
        
        # Check auto-saved flag
        assert response.auto_saved is True
    
    @pytest.mark.asyncio
    async def test_send_message_with_history(
        self,
        chat_service,
        mock_llm_service
    ):
        """Test sending message with conversation history."""
        history = [
            Message(role="user", content="My name is Lily"),
            Message(role="assistant", content="Nice to meet you, Lily!")
        ]
        
        response = await chat_service.send_message(
            message="What's my name?",
            session_id="session-123",
            conversation_history=history,
            use_rag=False
        )
        
        # Verify LLM was called with history
        mock_llm_service.complete.assert_called_once()
        call_args = mock_llm_service.complete.call_args
        
        # Check that history was included in messages
        messages_sent = call_args.kwargs['messages']
        assert len(messages_sent) >= 3  # system + history + current
    
    @pytest.mark.asyncio
    async def test_send_message_without_rag(
        self,
        chat_service,
        mock_rag_service
    ):
        """Test sending message with RAG disabled."""
        response = await chat_service.send_message(
            message="Hello",
            session_id="session-123",
            conversation_history=[],
            use_rag=False
        )
        
        # RAG should not be called
        mock_rag_service.retrieve_context.assert_not_called()
        
        # Response should have no retrieved context
        assert response.retrieved_context == []
    
    @pytest.mark.asyncio
    async def test_send_message_rag_failure_graceful_degradation(
        self,
        chat_service,
        mock_llm_service,
        mock_rag_service
    ):
        """Test that RAG failure doesn't crash the request."""
        # Make RAG fail
        mock_rag_service.retrieve_context = AsyncMock(
            side_effect=Exception("RAG failed")
        )
        
        # Should still work
        response = await chat_service.send_message(
            message="Hello",
            session_id="session-123",
            conversation_history=[],
            use_rag=True
        )
        
        # Should still get response
        assert response.message.content == "AI response"
        
        # But no retrieved context
        assert response.retrieved_context == []
    
    @pytest.mark.asyncio
    async def test_send_message_save_failure_graceful_degradation(
        self,
        chat_service,
        mock_journal_service
    ):
        """Test that save failure doesn't crash the request."""
        # Make save fail
        mock_journal_service.save_journal = AsyncMock(
            side_effect=Exception("Save failed")
        )
        
        # Should still work
        response = await chat_service.send_message(
            message="Hello",
            session_id="session-123",
            conversation_history=[],
            use_rag=False
        )
        
        # Should still get AI response
        assert response.message.content == "AI response"
        
        # But auto_saved should be False
        assert response.auto_saved is False
    
    @pytest.mark.asyncio
    async def test_manage_conversation_history_fits_budget(
        self,
        chat_service
    ):
        """Test that short conversation history fits in token budget."""
        history = [
            Message(role="user", content="Hi"),
            Message(role="assistant", content="Hello!")
        ]
        
        result = await chat_service._manage_conversation_history(
            history,
            available_tokens=5000
        )
        
        # All messages should be included
        assert len(result) == 2
        assert result[0]["content"] == "Hi"
        assert result[1]["content"] == "Hello!"
    
    @pytest.mark.asyncio
    async def test_manage_conversation_history_empty(
        self,
        chat_service
    ):
        """Test managing empty conversation history."""
        result = await chat_service._manage_conversation_history(
            [],
            available_tokens=5000
        )
        
        assert result == []

