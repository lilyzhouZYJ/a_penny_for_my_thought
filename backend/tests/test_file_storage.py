"""Unit tests for FileStorage service."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from app.storage.file_storage import FileStorage
from app.models import JournalNotFoundError, StorageError


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    storage = FileStorage(temp_dir)
    
    yield storage
    
    # Cleanup
    shutil.rmtree(temp_dir)


class TestFileStorage:
    """Tests for FileStorage class."""
    
    def test_initialization_creates_directory(self):
        """Test that FileStorage creates directory if it doesn't exist."""
        temp_dir = Path(tempfile.mkdtemp())
        test_dir = temp_dir / "test_journals"
        
        # Directory doesn't exist yet
        assert not test_dir.exists()
        
        # Initialize storage
        storage = FileStorage(test_dir)
        
        # Directory should be created
        assert test_dir.exists()
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_save_new_journal(self, temp_storage):
        """Test saving a new journal file."""
        content = "# Test Journal\n\nUser: Hello"
        title = "Test Journal"
        timestamp = datetime(2025, 1, 15, 10, 30, 0)
        
        filename = temp_storage.save_journal(content, title, timestamp)
        
        # Check filename format
        assert filename.startswith("2025-01-15_10-30-00")
        assert "test-journal" in filename
        assert filename.endswith(".md")
        
        # Check file exists
        file_path = temp_storage.base_directory / filename
        assert file_path.exists()
        
        # Check content
        saved_content = file_path.read_text(encoding="utf-8")
        assert saved_content == content
    
    def test_save_update_existing_journal(self, temp_storage):
        """Test updating an existing journal file."""
        # Save initial version
        content1 = "# Test\n\nUser: Hello"
        filename = temp_storage.save_journal(
            content1,
            "Test",
            datetime.now()
        )
        
        # Update with new content
        content2 = "# Test\n\nUser: Hello\n\nAssistant: Hi!"
        filename2 = temp_storage.save_journal(
            content2,
            "Test",
            datetime.now(),
            filename=filename  # Update existing
        )
        
        # Should return same filename
        assert filename == filename2
        
        # Content should be updated
        saved_content = temp_storage.get_journal(filename)
        assert "Assistant: Hi!" in saved_content
    
    def test_get_journal(self, temp_storage):
        """Test reading a journal file."""
        content = "# Test\n\nSome content"
        filename = temp_storage.save_journal(
            content,
            "Test",
            datetime.now()
        )
        
        retrieved = temp_storage.get_journal(filename)
        
        assert retrieved == content
    
    def test_get_nonexistent_journal_raises_error(self, temp_storage):
        """Test that getting non-existent journal raises error."""
        with pytest.raises(JournalNotFoundError):
            temp_storage.get_journal("nonexistent.md")
    
    def test_list_journals_empty(self, temp_storage):
        """Test listing when no journals exist."""
        journals = temp_storage.list_journals()
        
        assert journals == []
    
    def test_list_journals_multiple(self, temp_storage):
        """Test listing multiple journals."""
        # Create 3 journals
        for i in range(3):
            temp_storage.save_journal(
                f"Content {i}",
                f"Journal {i}",
                datetime.now()
            )
        
        journals = temp_storage.list_journals()
        
        assert len(journals) == 3
        # All should be .md files
        assert all(f.endswith(".md") for f in journals)
    
    def test_delete_journal(self, temp_storage):
        """Test deleting a journal file."""
        filename = temp_storage.save_journal(
            "Content",
            "Test",
            datetime.now()
        )
        
        # Verify it exists
        assert filename in temp_storage.list_journals()
        
        # Delete it
        temp_storage.delete_journal(filename)
        
        # Verify it's gone
        assert filename not in temp_storage.list_journals()
    
    def test_delete_nonexistent_raises_error(self, temp_storage):
        """Test that deleting non-existent journal raises error."""
        with pytest.raises(JournalNotFoundError):
            temp_storage.delete_journal("nonexistent.md")
    
    def test_sanitize_filename(self, temp_storage):
        """Test filename sanitization."""
        # Test various problematic titles
        test_cases = [
            ("Hello World", "hello-world"),
            ("Test: Special/Characters?", "test-specialcharacters"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("A" * 100, "a" * 50),  # Truncate to 50 chars
            ("---Leading-Hyphens---", "leading-hyphens"),
            ("", "untitled"),  # Empty becomes untitled
        ]
        
        for input_title, expected in test_cases:
            result = temp_storage._sanitize_filename(input_title)
            assert result == expected
    
    def test_validate_file_path_prevents_traversal(self, temp_storage):
        """Test that path validation prevents directory traversal."""
        # Attempt directory traversal
        with pytest.raises(StorageError):
            temp_storage._validate_file_path("../../../etc/passwd")
        
        with pytest.raises(StorageError):
            temp_storage._validate_file_path("subdir/../../outside.md")

