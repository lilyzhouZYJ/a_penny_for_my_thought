import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models import JournalNotFoundError, StorageError

class FileStorage:
    """
    Handles markdown file operations for journal storage.
    Markdown files are used to load conversations into the UI.
    """
    
    def __init__(self, base_directory: Path):
        """
        Initialize file storage.
        
        Args:
            base_directory: Directory where journal markdown files are stored
        """
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)
    
    def save_journal(
        self,
        content: str,
        title: str,
        timestamp: datetime,
        filename: Optional[str] = None
    ) -> str:
        """
        Save or update journal markdown file.
        
        Args:
            content: Markdown content to save
            title: Journal title
            timestamp: Timestamp for the journal
            filename: Optional existing filename (for updates)
        
        Returns:
            Filename of the saved journal
        
        Raises:
            StorageError: If file cannot be saved
        """
        try:
            if filename:
                # Update existing file
                file_path = self._validate_file_path(filename)
            else:
                # Create new file with naming convention
                sanitized_title = self._sanitize_filename(title)
                timestamp_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{timestamp_str}_{sanitized_title}.md"
                file_path = self.base_directory / filename
            
            # Write file
            file_path.write_text(content, encoding="utf-8")
            
            return filename
            
        except Exception as e:
            raise StorageError(f"Failed to save journal: {e}")
    
    def get_journal(self, filename: str) -> str:
        """
        Read journal content from markdown file.
        
        Args:
            filename: Journal filename
        
        Returns:
            Markdown content
        
        Raises:
            JournalNotFoundError: If file doesn't exist
            StorageError: If file cannot be read
        """
        try:
            file_path = self._validate_file_path(filename)
            
            if not file_path.exists():
                raise JournalNotFoundError(filename)
            
            return file_path.read_text(encoding="utf-8")
            
        except JournalNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to read journal: {e}")
    
    def list_journals(self) -> List[str]:
        """
        List all journal filenames sorted by date (newest first).
        
        Returns:
            List of journal filenames
        
        Raises:
            StorageError: If directory cannot be read
        """
        try:
            # Get all .md files
            md_files = list(self.base_directory.glob("*.md"))
            
            # Sort by modification time (newest first)
            md_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            return [f.name for f in md_files]
            
        except Exception as e:
            raise StorageError(f"Failed to list journals: {e}")
    
    def delete_journal(self, filename: str) -> None:
        """
        Delete journal file.
        
        Args:
            filename: Journal filename to delete
        
        Raises:
            JournalNotFoundError: If file doesn't exist
            StorageError: If file cannot be deleted
        """
        try:
            file_path = self._validate_file_path(filename)
            
            if not file_path.exists():
                raise JournalNotFoundError(filename)
            
            file_path.unlink()
            
        except JournalNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete journal: {e}")
    
    def _sanitize_filename(self, title: str) -> str:
        """
        Sanitize title for safe filename.
        
        Args:
            title: Raw title string
        
        Returns:
            Sanitized filename-safe string
        """
        # Remove or replace unsafe characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        
        # Replace spaces with hyphens
        sanitized = sanitized.replace(' ', '-')
        
        # Remove multiple consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Trim to reasonable length
        sanitized = sanitized[:50]
        
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        
        # If empty after sanitization, use default
        if not sanitized:
            sanitized = "untitled"
        
        return sanitized.lower()
    
    def _validate_file_path(self, filename: str) -> Path:
        """
        Validate file path to prevent directory traversal attacks.
        
        Args:
            filename: Filename to validate
        
        Returns:
            Validated absolute path
        
        Raises:
            StorageError: If path is invalid or attempts directory traversal
        """
        file_path = (self.base_directory / filename).resolve()
        
        # Ensure path is within base directory
        if not str(file_path).startswith(str(self.base_directory.resolve())):
            raise StorageError(f"Invalid file path: {filename}")
        
        return file_path
