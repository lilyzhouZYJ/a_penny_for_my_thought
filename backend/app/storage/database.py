import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from app.models import Message, JournalMetadata, Journal, StorageError, JournalNotFoundError

logger = logging.getLogger(__name__)


class DatabaseStorage:
    """
    SQLite database storage for chat history and journal management.
    
    Replaces markdown file storage with a proper database for better
    querying, indexing, and data integrity.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize database storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create journals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journals (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    duration_seconds INTEGER,
                    mode TEXT NOT NULL DEFAULT 'chat' CHECK (mode IN ('chat', 'write')),
                    metadata TEXT  -- JSON string for additional data
                )
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    journal_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata TEXT,  -- JSON string for additional data
                    FOREIGN KEY (journal_id) REFERENCES journals (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_session_id ON journals (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_created_at ON journals (created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_journal_id ON messages (journal_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)")
            
            # Migration: Add mode column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE journals ADD COLUMN mode TEXT DEFAULT 'chat'")
                logger.info("Added mode column to journals table")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            conn.commit()
            logger.info("Database schema initialized")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise StorageError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def save_journal(
        self,
        session_id: str,
        messages: List[Message],
        title: str,
        journal_id: Optional[str] = None,
        mode: str = "chat"
    ) -> JournalMetadata:
        """
        Save or update a journal.
        
        Args:
            session_id: Session UUID
            messages: List of messages in journal
            title: Journal title
            journal_id: Optional existing journal ID (for updates)
            mode: Journal mode ("chat" or "write")
        
        Returns:
            JournalMetadata with journal information
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate metadata
            created_at = messages[0].timestamp if messages else datetime.now(timezone.utc)
            updated_at = datetime.now(timezone.utc)
            
            if len(messages) >= 2:
                duration = (messages[-1].timestamp - messages[0].timestamp).total_seconds()
                duration_seconds = int(duration)
            else:
                duration_seconds = None
            
            # Check if a journal with this session_id already exists
            cursor.execute("SELECT id FROM journals WHERE session_id = ?", (session_id,))
            existing_journal = cursor.fetchone()
            
            if existing_journal:
                # Update existing journal
                final_journal_id = existing_journal['id']
                cursor.execute("""
                    UPDATE journals 
                    SET title = ?, updated_at = ?, message_count = ?, duration_seconds = ?, mode = ?
                    WHERE id = ?
                """, (title, updated_at, len(messages), duration_seconds, mode, final_journal_id))
                
                # Delete existing messages
                cursor.execute("DELETE FROM messages WHERE journal_id = ?", (final_journal_id,))
            else:
                # Create new journal
                final_journal_id = session_id  # Use session_id as journal_id
                cursor.execute("""
                    INSERT INTO journals 
                    (id, session_id, title, created_at, updated_at, message_count, duration_seconds, mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (final_journal_id, session_id, title, created_at, updated_at, len(messages), duration_seconds, mode))
            
            # Insert messages
            for message in messages:
                metadata_json = None
                if message.metadata:
                    import json
                    metadata_json = json.dumps(message.metadata)
                
                cursor.execute("""
                    INSERT INTO messages 
                    (id, journal_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (message.id, final_journal_id, message.role, message.content, message.timestamp, metadata_json))
            
            conn.commit()
            
            # Create metadata response
            journal_metadata = JournalMetadata(
                id=final_journal_id,
                filename=final_journal_id,  # For compatibility
                title=title,
                date=created_at,
                message_count=len(messages),
                duration_seconds=duration_seconds,
                mode=mode
            )
            
            action = "Updated" if existing_journal else "Saved"
            logger.info(f"{action} journal: {final_journal_id}")
            
            return journal_metadata
    
    def get_journal(self, journal_id: str) -> Journal:
        """
        Retrieve a journal with all messages.
        
        Args:
            journal_id: Journal ID
        
        Returns:
            Journal object with messages
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get journal metadata
            cursor.execute("""
                SELECT id, session_id, title, created_at, updated_at, 
                       message_count, duration_seconds, mode, metadata
                FROM journals 
                WHERE id = ?
            """, (journal_id,))
            
            journal_row = cursor.fetchone()
            if not journal_row:
                raise JournalNotFoundError(journal_id)
            
            # Get messages
            cursor.execute("""
                SELECT id, role, content, timestamp, metadata
                FROM messages 
                WHERE journal_id = ? 
                ORDER BY timestamp ASC
            """, (journal_id,))
            
            message_rows = cursor.fetchall()
            
            # Convert to Message objects
            messages = []
            for row in message_rows:
                metadata = None
                if row['metadata']:
                    import json
                    metadata = json.loads(row['metadata'])
                
                messages.append(Message(
                    id=row['id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=metadata
                ))
            
            # Create Journal object
            journal = Journal(
                id=journal_row['id'],
                filename=journal_row['id'],  # For compatibility
                title=journal_row['title'],
                date=datetime.fromisoformat(journal_row['created_at']),
                message_count=journal_row['message_count'],
                duration_seconds=journal_row['duration_seconds'],
                mode=journal_row['mode'] or 'chat',  # Default to 'chat' for existing records
                messages=messages,
                raw_content=""  # Not used for database storage
            )
            
            return journal
    
    def list_journals(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at"
    ) -> tuple[List[JournalMetadata], int]:
        """
        List journals with pagination.
        
        Args:
            limit: Maximum number of journals to return
            offset: Number of journals to skip
            sort_by: Sort field ('created_at' or 'updated_at')
        
        Returns:
            Tuple of (list of journal metadata, total count)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Validate sort_by
            if sort_by not in ['created_at', 'updated_at']:
                sort_by = 'created_at'
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM journals")
            total = cursor.fetchone()[0]
            
            # Get paginated results
            cursor.execute(f"""
                SELECT id, session_id, title, created_at, updated_at, 
                       message_count, duration_seconds, mode, metadata
                FROM journals 
                ORDER BY {sort_by} DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            
            # Convert to JournalMetadata objects
            journals = []
            for row in rows:
                journals.append(JournalMetadata(
                    id=row['id'],
                    filename=row['id'],  # For compatibility
                    title=row['title'],
                    date=datetime.fromisoformat(row['created_at']),
                    message_count=row['message_count'],
                    duration_seconds=row['duration_seconds'],
                    mode=row['mode'] or 'chat'  # Default to 'chat' for existing records
                ))
            
            return journals, total
    
        """
        Create a placeholder journal entry with no messages.
        
        This is used when starting a new conversation so it appears
        in the conversation list immediately.
        
        Args:
            session_id: Session UUID
            title: Journal title (defaults to "New Conversation")
        
        Returns:
            JournalMetadata for the created journal
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if journal already exists
            cursor.execute("SELECT id FROM journals WHERE session_id = ?", (session_id,))
            existing_journal = cursor.fetchone()
            
            if existing_journal:
                # Journal already exists, return its metadata
                cursor.execute("""
                    SELECT id, session_id, title, created_at, updated_at, 
                           message_count, duration_seconds, mode, metadata
                    FROM journals WHERE session_id = ?
                """, (session_id,))
                row = cursor.fetchone()
                
                return JournalMetadata(
                    id=row['id'],
                    filename=row['id'],
                    title=row['title'],
                    date=datetime.fromisoformat(row['created_at']),
                    message_count=row['message_count'],
                    duration_seconds=row['duration_seconds'],
                    mode=row['mode'] or 'chat'  # Default to 'chat' for existing records
                )
            
            # Create new placeholder journal
            now = datetime.now(timezone.utc)
            journal_id = session_id  # Use session_id as journal_id
            
            cursor.execute("""
                INSERT INTO journals 
                (id, session_id, title, created_at, updated_at, message_count, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (journal_id, session_id, title, now, now, 0, None))
            
            conn.commit()
            
            logger.info(f"Created placeholder journal: {session_id}")
            
            return JournalMetadata(
                id=journal_id,
                filename=journal_id,
                title=title,
                date=now,
                message_count=0,
                duration_seconds=None
            ), total
    
    def delete_journal(self, journal_id: str) -> None:
        """
        Delete a journal and all its messages.
        
        Args:
            journal_id: Journal ID to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if journal exists
            cursor.execute("SELECT id FROM journals WHERE id = ?", (journal_id,))
            if not cursor.fetchone():
                raise JournalNotFoundError(journal_id)
            
            # Delete journal (messages will be deleted by CASCADE)
            cursor.execute("DELETE FROM journals WHERE id = ?", (journal_id,))
            conn.commit()
            
            logger.info(f"Deleted journal: {journal_id}")
    
    def get_journal_by_session_id(self, session_id: str) -> Optional[Journal]:
        """
        Get journal by session ID.
        
        Args:
            session_id: Session UUID
        
        Returns:
            Journal object if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get journal ID by session_id
            cursor.execute("SELECT id FROM journals WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get full journal
            return self.get_journal(row['id'])
    
