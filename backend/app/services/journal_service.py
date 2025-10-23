import logging
from datetime import datetime
from typing import List, Optional, Tuple

from app.models import CreateJournalRequest, Journal, JournalMetadata, Message
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.storage.database import DatabaseStorage
from app.storage.vector_storage import VectorStorage

logger = logging.getLogger(__name__)


class JournalService:
    """
    Service for journal CRUD operations using database storage.
    
    Coordinates DatabaseStorage and VectorStorage for RAG indexing.
    """
    
    def __init__(
        self,
        database_storage: DatabaseStorage,
        vector_storage: VectorStorage,
        rag_service: RAGService,
        llm_service: LLMService
    ):
        """
        Initialize journal service.
        
        Args:
            database_storage: Database storage for journal data
            vector_storage: Vector database for semantic search
            rag_service: RAG service for indexing conversations
            llm_service: LLM service for title generation
        """
        self.database_storage = database_storage
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
        Save or update journal using database storage.
        
        Args:
            session_id: Session UUID
            messages: List of messages in journal
            journal_id: Optional existing journal ID (for updates)
            title: Optional title (auto-generated if None and creating new)
        
        Returns:
            JournalMetadata with journal information
        """
        try:
            # Generate title if needed (only for new journals)
            if not journal_id and title is None:
                title = await self._generate_title(messages)
            
            # Save to database
            journal_metadata = self.database_storage.save_journal(
                session_id=session_id,
                messages=messages,
                title=title or "Untitled Journal",
                journal_id=journal_id
            )
            
            # Index in vector database for RAG
            try:
                await self.rag_service.index_conversation(
                    messages=messages,
                    session_id=session_id,
                    metadata={
                        'date': journal_metadata.date.isoformat(),
                        'title': journal_metadata.title,
                        'journal_id': journal_metadata.id
                    }
                )
            except Exception as e:
                # Log error but don't fail the save
                logger.error(f"Failed to index journal in vector DB: {e}")
                logger.warning("Journal saved to database but not indexed for semantic search")
            
            action = "Updated" if journal_id else "Saved"
            logger.info(f"{action} journal: {journal_metadata.id}")
            
            return journal_metadata
            
        except Exception as e:
            logger.error(f"Failed to save journal: {e}")
            raise
    
    async def list_journals(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at"
    ) -> Tuple[List[JournalMetadata], int]:
        """
        List all journal entries from database.
        
        Args:
            limit: Maximum number of journals to return
            offset: Number of journals to skip
            sort_by: Sort field ('created_at' or 'updated_at')
        
        Returns:
            Tuple of (list of journal metadata, total count)
        """
        return self.database_storage.list_journals(
            limit=limit,
            offset=offset,
            sort_by=sort_by
        )
    
    async def get_journal(self, journal_id: str) -> Journal:
        """
        Retrieve specific journal with full message history from database.
        
        Args:
            journal_id: Journal ID
        
        Returns:
            Full journal with messages
        """
        return self.database_storage.get_journal(journal_id)
    
    async def delete_journal(self, journal_id: str) -> None:
        """
        Delete journal from database and vector storage.
        
        Args:
            journal_id: Journal ID to delete
        """
        # Get journal metadata before deleting
        try:
            journal = self.database_storage.get_journal(journal_id)
            session_id = journal.id  # Use journal ID as session ID
            
            # Delete from database
            self.database_storage.delete_journal(journal_id)
            logger.info(f"Deleted journal from database: {journal_id}")
            
            # Delete from vector database
            try:
                await self.vector_storage.delete_by_metadata({'session_id': session_id})
                logger.info(f"Deleted journal from vector DB: {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete from vector DB: {e}")
                # Don't fail the whole operation - journal is already deleted from database
                
        except Exception as e:
            logger.error(f"Failed to delete journal: {e}")
            raise
    
    async def _generate_title(self, messages: List[Message]) -> str:
        """
        Generate title for journal using LLM.
        
        Args:
            messages: Journal messages
        
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
            return "Untitled Journal"
    