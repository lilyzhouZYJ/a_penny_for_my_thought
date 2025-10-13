"""Unit tests for JournalService with mocked dependencies."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path
import asyncio

from app.services.journal_service import JournalService
from app.storage.file_storage import FileStorage
from app.models import Message, JournalMetadata


@pytest.fixture
def temp_file_storage():
    """Create temporary file storage."""
    temp_dir = Path(tempfile.mkdtemp())
    storage = FileStorage(temp_dir)
    yield storage
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_vector_storage():
    """Create mock vector storage."""
    mock = Mock()
    mock.add_documents = AsyncMock()
    mock.delete_by_metadata = AsyncMock()
    return mock


@pytest.fixture
def mock_rag_service():
    """Create mock RAG service."""
    mock = Mock()
    mock.index_conversation = AsyncMock()
    return mock


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.generate_title = AsyncMock(return_value="Generated Title")
    return mock


@pytest.fixture
def journal_service(
    temp_file_storage,
    mock_vector_storage,
    mock_rag_service,
    mock_llm_service
):
    """Create JournalService with real file storage and mocked other dependencies."""
    return JournalService(
        file_storage=temp_file_storage,
        vector_storage=mock_vector_storage,
        rag_service=mock_rag_service,
        llm_service=mock_llm_service
    )


class TestJournalService:
    """Tests for JournalService."""
    
    @pytest.mark.asyncio
    async def test_save_new_journal(
        self,
        journal_service,
        mock_rag_service,
        mock_llm_service
    ):
        """Test saving a new journal entry."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!")
        ]
        
        result = await journal_service.save_journal(
            session_id="session-123",
            messages=messages
        )
        
        # Verify title was generated
        mock_llm_service.generate_title.assert_called_once()
        
        # Verify result
        assert isinstance(result, JournalMetadata)
        assert result.title == "Generated Title"
        assert result.message_count == 2
        
        # Verify file was created
        journals = journal_service.file_storage.list_journals()
        assert len(journals) == 1
        
        # Verify indexing was called
        mock_rag_service.index_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_journal_with_custom_title(
        self,
        journal_service,
        mock_llm_service
    ):
        """Test saving journal with custom title (no generation)."""
        messages = [Message(role="user", content="Test")]
        
        result = await journal_service.save_journal(
            session_id="session-123",
            messages=messages,
            title="Custom Title"
        )
        
        # Title generation should not be called
        mock_llm_service.generate_title.assert_not_called()
        
        # Should use custom title
        assert result.title == "Custom Title"
    
    @pytest.mark.asyncio
    async def test_update_existing_journal(
        self,
        journal_service
    ):
        """Test updating an existing journal."""
        # Save initial journal
        initial_messages = [
            Message(role="user", content="First message")
        ]
        
        initial_result = await journal_service.save_journal(
            session_id="session-123",
            messages=initial_messages
        )
        
        # Update with more messages
        updated_messages = [
            Message(role="user", content="First message"),
            Message(role="assistant", content="Response"),
            Message(role="user", content="Second message")
        ]
        
        updated_result = await journal_service.save_journal(
            session_id="session-123",
            messages=updated_messages,
            journal_id=initial_result.filename  # Update existing
        )
        
        # Should return same filename
        assert updated_result.filename == initial_result.filename
        
        # Should have more messages
        assert updated_result.message_count == 3
        
        # Should still only have 1 file
        journals = journal_service.file_storage.list_journals()
        assert len(journals) == 1
    
    @pytest.mark.asyncio
    async def test_list_journals(self, journal_service):
        """Test listing journals."""
        # Create 3 journals
        for i in range(3):
            messages = [Message(role="user", content=f"Message {i}")]
            await journal_service.save_journal(
                session_id=f"session-{i}",
                messages=messages,
                title=f"Journal {i}"
            )
        
        # List all
        journals, total = await journal_service.list_journals()
        
        assert len(journals) == 3
        assert total == 3
        assert all(isinstance(j, JournalMetadata) for j in journals)
    
    @pytest.mark.asyncio
    async def test_list_journals_with_pagination(self, journal_service):
        """Test listing journals with pagination."""
        # Create 5 journals with small delays to get different timestamps
        for i in range(5):
            messages = [Message(role="user", content=f"Message {i}")]
            await journal_service.save_journal(
                session_id=f"session-{i}",
                messages=messages,
                title=f"Journal {i}"  # Different titles ensure different filenames
            )
            # Small delay to ensure different timestamps
            await asyncio.sleep(0.01)
        
        # Get first 2
        journals, total = await journal_service.list_journals(limit=2, offset=0)
        
        assert len(journals) == 2
        assert total == 5
        
        # Get next 2
        journals, total = await journal_service.list_journals(limit=2, offset=2)
        
        assert len(journals) == 2
        assert total == 5
    
    @pytest.mark.asyncio
    async def test_get_journal(self, journal_service):
        """Test getting a specific journal."""
        # Save a journal
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi!")
        ]
        
        saved = await journal_service.save_journal(
            session_id="session-123",
            messages=messages,
            title="Test Journal"
        )
        
        # Get it back
        journal = await journal_service.get_journal(saved.filename)
        
        # Verify it loaded from markdown
        assert journal.title == "Test Journal"
        assert len(journal.messages) == 2
        assert journal.messages[0].content == "Hello"
        assert journal.raw_content is not None
    
    @pytest.mark.asyncio
    async def test_delete_journal(
        self,
        journal_service,
        mock_vector_storage
    ):
        """Test deleting a journal."""
        # Save a journal
        messages = [Message(role="user", content="Test")]
        
        saved = await journal_service.save_journal(
            session_id="session-123",
            messages=messages
        )
        
        # Delete it
        await journal_service.delete_journal(saved.filename)
        
        # Verify file was deleted
        journals = journal_service.file_storage.list_journals()
        assert len(journals) == 0
        
        # Verify vector DB delete was called
        mock_vector_storage.delete_by_metadata.assert_called_once()

