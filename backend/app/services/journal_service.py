import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.models import CreateJournalRequest, Journal, JournalMetadata, Message
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.storage.file_storage import FileStorage
from app.storage.vector_storage import VectorStorage
from app.utils.markdown_formatter import format_journal_markdown, parse_journal_markdown

logger = logging.getLogger(__name__)


def _parse_datetime(date_str: str) -> datetime:
    """
    Parse datetime string from markdown frontmatter.
    
    Handles format: "2025-10-13 05:01:56 UTC"
    
    Args:
        date_str: Date string from frontmatter
    
    Returns:
        datetime object
    """
    # Remove " UTC" suffix if present
    if date_str.endswith(" UTC"):
        date_str = date_str[:-4]
    
    # Parse ISO format
    return datetime.fromisoformat(date_str)

class JournalService:
    """
    Service for journal CRUD operations.
    
    Coordinates FileStorage and VectorStorage.
    Ensures both storage systems are updated together.
    """
    
    def __init__(
        self,
        file_storage: FileStorage,
        vector_storage: VectorStorage,
        rag_service: RAGService,
        llm_service: LLMService
    ):
        """
        Initialize journal service.
        
        Args:
            file_storage: Filesystem storage for markdown files
            vector_storage: Vector database for semantic search
            rag_service: RAG service for indexing conversations
            llm_service: LLM service for title generation
        """
        self.file_storage = file_storage
        self.vector_storage = vector_storage
        self.rag_service = rag_service
        self.llm_service = llm_service
    
    async def save_journal(
        self,
        session_id: str,
        messages: List[Message],
        journal_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> JournalMetadata:
        """
        Save or update conversation as journal.
        
        Updates BOTH markdown file (source of truth) and vector database (search index).
        
        Args:
            session_id: Session UUID
            messages: List of messages in conversation
            journal_id: Optional existing journal filename (for updates)
            title: Optional title (auto-generated if None and creating new)
        
        Returns:
            JournalMetadata with journal information
        """
        is_update = journal_id is not None
        
        try:
            # Generate title if needed (only for new journals)
            if not is_update and title is None:
                title = await self._generate_title(messages)
            elif is_update and title is None:
                # For updates, extract title from existing file
                existing_content = self.file_storage.get_journal(journal_id)
                existing_metadata = parse_journal_markdown(existing_content)
                title = existing_metadata.get('title', 'Untitled')
            
            # Calculate conversation metadata
            created_at = messages[0].timestamp if messages else datetime.now()
            if len(messages) >= 2:
                duration = (messages[-1].timestamp - messages[0].timestamp).total_seconds()
                duration_seconds = int(duration)
            else:
                duration_seconds = None
            
            # Format as markdown
            markdown_content = format_journal_markdown(
                title=title,
                session_id=session_id,
                messages=messages,
                created_at=created_at,
                duration_seconds=duration_seconds
            )
            
            # Save to filesystem (create or update)
            filename = self.file_storage.save_journal(
                content=markdown_content,
                title=title,
                timestamp=created_at,
                filename=journal_id  # None for new, existing filename for update
            )
            
            # Index in vector database
            try:
                await self.rag_service.index_conversation(
                    messages=messages,
                    session_id=session_id,
                    metadata={
                        'date': created_at.isoformat(),
                        'title': title,
                        'filename': filename
                    }
                )
            except Exception as e:
                # Log error but don't fail the save
                # Markdown file is already saved (source of truth)
                logger.error(f"Failed to index conversation in vector DB: {e}")
                logger.warning("Journal saved to disk but not indexed for semantic search")
            
            # Create metadata response
            journal_metadata = JournalMetadata(
                id=filename,
                filename=filename,
                title=title,
                date=created_at,
                message_count=len(messages),
                duration_seconds=duration_seconds
            )
            
            action = "Updated" if is_update else "Saved"
            logger.info(f"{action} journal: {filename}")
            
            return journal_metadata
            
        except Exception as e:
            logger.error(f"Failed to save journal: {e}")
            raise
    
    async def list_journals(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "date"
    ) -> Tuple[List[JournalMetadata], int]:
        """
        List all journal entries.
        
        Args:
            limit: Maximum number of journals to return
            offset: Number of journals to skip
            sort_by: Sort field (currently only 'date' supported)
        
        Returns:
            Tuple of (list of journal metadata, total count)
        """
        # Get all journal filenames (already sorted by date, newest first)
        all_filenames = self.file_storage.list_journals()
        total = len(all_filenames)
        
        # Apply pagination
        paginated_filenames = all_filenames[offset:offset + limit]
        
        # Extract metadata from each file
        journals = []
        for filename in paginated_filenames:
            try:
                # Read file to get metadata
                content = self.file_storage.get_journal(filename)
                metadata_dict = parse_journal_markdown(content)
                
                # Parse metadata
                journals.append(
                    JournalMetadata(
                        id=filename,
                        filename=filename,
                        title=metadata_dict.get('title', 'Untitled'),
                        date=_parse_datetime(metadata_dict.get('date', datetime.now().isoformat())),
                        message_count=int(metadata_dict.get('message_count', 0)),
                        duration_seconds=int(metadata_dict.get('duration')) if metadata_dict.get('duration') else None
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse journal {filename}: {e}")
                # Skip malformed journals
                continue
        
        return journals, total
    
    async def get_journal(self, journal_id: str) -> Journal:
        """
        Retrieve specific journal with full message history.
        
        Used to load past conversations into chat interface for continuation.
        
        Reads from MARKDOWN FILE on disk (NOT from ChromaDB).
        Parses markdown to reconstruct complete message list.
        
        Args:
            journal_id: Journal filename
        
        Returns:
            Full journal with messages
        """
        # Read from markdown file (NOT from vector DB)
        content = self.file_storage.get_journal(journal_id)
        
        # Parse frontmatter metadata
        metadata_dict = parse_journal_markdown(content)
        
        # Parse messages from markdown content
        messages = self._parse_messages_from_markdown(content)
        
        # Create Journal object
        journal = Journal(
            id=journal_id,
            filename=journal_id,
            title=metadata_dict.get('title', 'Untitled'),
            date=_parse_datetime(metadata_dict.get('date', datetime.now().isoformat())),
            message_count=len(messages),
            duration_seconds=int(metadata_dict.get('duration')) if metadata_dict.get('duration') else None,
            messages=messages,
            raw_content=content
        )
        
        return journal
    
    async def delete_journal(self, journal_id: str) -> None:
        """
        Delete journal from BOTH storages (filesystem and vector database).
        
        Args:
            journal_id: Journal filename to delete
        """
        # Get metadata before deleting
        content = self.file_storage.get_journal(journal_id)
        metadata_dict = parse_journal_markdown(content)
        session_id = metadata_dict.get('session_id')
        
        # Delete from filesystem
        self.file_storage.delete_journal(journal_id)
        logger.info(f"Deleted journal file: {journal_id}")
        
        # Delete from vector database
        if session_id:
            try:
                await self.vector_storage.delete_by_metadata({'session_id': session_id})
                logger.info(f"Deleted journal from vector DB: {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete from vector DB: {e}")
                # Don't fail the whole operation - file is already deleted
    
    async def _generate_title(self, messages: List[Message]) -> str:
        """
        Generate title for conversation using LLM.
        
        Args:
            messages: Conversation messages
        
        Returns:
            Generated title
        """
        # Use first few messages for title generation
        conversation_preview = ""
        for msg in messages[:4]:  # First 2 exchanges
            role_label = "User" if msg.role == "user" else "Assistant"
            conversation_preview += f"{role_label}: {msg.content}\n"
        
        try:
            title = await self.llm_service.generate_title(
                conversation=conversation_preview,
                max_length=50
            )
            return title
        except Exception as e:
            logger.warning(f"Title generation failed: {e}")
            # Return default title
            return "Untitled Conversation"
    
    def _parse_messages_from_markdown(self, content: str) -> List[Message]:
        """
        Parse messages from markdown content.
        
        This is a simple parser that extracts user and assistant messages.
        
        Args:
            content: Markdown content
        
        Returns:
            List of Message objects
        """
        messages = []
        
        # Split by conversation section
        if "## Conversation" in content:
            conversation_section = content.split("## Conversation", 1)[1]
            conversation_section = conversation_section.split("---", 1)[0]  # Remove footer
            
            # Split by message markers
            lines = conversation_section.split('\n')
            current_role = None
            current_content = []
            current_timestamp = None
            
            for line in lines:
                line = line.strip()
                
                # Check for message headers
                if line.startswith("**User**") or line.startswith("**Assistant**"):
                    # Save previous message if exists
                    if current_role and current_content:
                        messages.append(Message(
                            role=current_role,
                            content='\n'.join(current_content).strip(),
                            timestamp=current_timestamp or datetime.now()
                        ))
                        current_content = []
                    
                    # Parse new message header
                    if line.startswith("**User**"):
                        current_role = "user"
                    else:
                        current_role = "assistant"
                    
                    # Extract timestamp if present
                    if "*" in line:
                        # Try to parse timestamp (HH:MM:SS format)
                        try:
                            time_str = line.split("*")[1].strip()
                            # Create today's date with this time (approximate)
                            current_timestamp = datetime.now()
                        except:
                            current_timestamp = datetime.now()
                
                elif line and current_role:
                    # Add to current message content
                    current_content.append(line)
            
            # Add final message
            if current_role and current_content:
                messages.append(Message(
                    role=current_role,
                    content='\n'.join(current_content).strip(),
                    timestamp=current_timestamp or datetime.now()
                ))
        
        return messages

