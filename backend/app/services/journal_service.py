import logging
from datetime import datetime
from typing import List, Optional, Tuple, AsyncGenerator

from app.models import Journal, JournalMetadata, Message, UpdateWriteContentRequest, AskAIRequest, StreamEvent
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
        title: Optional[str] = None,
        mode: str = "chat"
    ) -> JournalMetadata:
        """
        Save or update journal using database storage.
        
        Args:
            session_id: Session UUID
            messages: List of messages in journal
            journal_id: Optional existing journal ID (for updates)
            title: Optional title (auto-generated if None and creating new)
            mode: Journal mode ("chat" or "write")
        
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
                journal_id=journal_id,
                mode=mode
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
    
    async def update_write_content(
        self,
        session_id: str,
        content: str,
        journal_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> JournalMetadata:
        """
        Update write mode content by creating/updating a user message.
        
        Args:
            session_id: Session UUID
            content: The write mode content
            journal_id: Optional existing journal ID (for updates)
            title: Optional title
        
        Returns:
            JournalMetadata with journal information
        """
        try:
            # Create a user message with the write content
            from datetime import datetime, timezone
            write_message = Message(
                role="user",
                content=content,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Generate title if needed
            if not journal_id and title is None:
                title = await self._generate_title_from_content(content)
            
            # Save as a journal with write mode
            journal_metadata = self.database_storage.save_journal(
                session_id=session_id,
                messages=[write_message],
                title=title or "Untitled Journal",
                journal_id=journal_id,
                mode="write"
            )
            
            # Index the write content for RAG
            try:
                await self.rag_service.index_write_content(
                    content=content,
                    session_id=session_id,
                    metadata={
                        'date': journal_metadata.date.isoformat(),
                        'title': journal_metadata.title,
                        'journal_id': journal_metadata.id,
                        'mode': 'write'
                    }
                )
            except Exception as e:
                logger.error(f"Failed to index write content in vector DB: {e}")
                logger.warning("Write content saved to database but not indexed for semantic search")
            
            action = "Updated" if journal_id else "Saved"
            logger.info(f"{action} write journal: {journal_metadata.id}")
            
            return journal_metadata
            
        except Exception as e:
            logger.error(f"Failed to update write content: {e}")
            raise
    
    async def ask_ai_for_input(
        self,
        session_id: str,
        content: str,
        conversation_history: List[Message],
        journal_id: Optional[str] = None
    ) -> dict:
        """
        Ask AI for input on write mode content.
        
        Args:
            session_id: Session UUID
            content: The write mode content
            conversation_history: Previous AI interactions
            journal_id: Optional journal ID
        
        Returns:
            AI response message
        """
        try:
            # Use LLM service to generate therapeutic response
            response = await self.llm_service.generate_therapeutic_response(
                journal_content=content,
                conversation_history=conversation_history
            )
            
            # Create AI message
            from datetime import datetime, timezone
            ai_message = Message(
                role="assistant",
                content=response,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add to conversation history
            updated_messages = conversation_history + [ai_message]
            
            # Save the updated conversation
            await self.save_journal(
                session_id=session_id,
                messages=updated_messages,
                journal_id=journal_id,
                mode="write"
            )
            
            return {
                "message": ai_message,
                "conversation_history": updated_messages
            }
            
        except Exception as e:
            logger.error(f"Failed to get AI input: {e}")
            raise
    
    async def stream_ai_for_input(
        self,
        session_id: str,
        content: str,
        conversation_history: List[Message],
        journal_id: Optional[str] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream AI input for write mode content.
        
        Args:
            session_id: Session UUID
            content: The write mode content
            conversation_history: Previous AI interactions
            journal_id: Optional journal ID
        
        Yields:
            StreamEvent objects (token, done, or error events)
        """
        try:
            # Stream therapeutic response from LLM
            full_response = ""
            async for token in self.llm_service.stream_therapeutic_response(
                journal_content=content,
                conversation_history=conversation_history
            ):
                full_response += token
                yield StreamEvent(
                    type="token",
                    data={"token": token}
                )
            
            # Create AI message
            from datetime import datetime, timezone
            ai_message = Message(
                role="assistant",
                content=full_response,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Add to conversation history
            updated_messages = conversation_history + [ai_message]
            
            # Save the updated conversation
            await self.save_journal(
                session_id=session_id,
                messages=updated_messages,
                journal_id=journal_id,
                mode="write"
            )
            
            # Send completion event
            yield StreamEvent(
                type="done",
                data={
                    "message": {
                        "role": ai_message.role,
                        "content": ai_message.content,
                        "timestamp": ai_message.timestamp.isoformat()
                    },
                    "conversation_history": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat()
                        }
                        for msg in updated_messages
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to stream AI input: {e}")
            yield StreamEvent(
                type="error",
                data={"message": str(e)}
            )
    
    async def _generate_title_from_content(self, content: str) -> str:
        """
        Generate title for write mode content using LLM.
        
        Args:
            content: Write mode content
        
        Returns:
            Generated title
        """
        try:
            title = await self.llm_service.generate_title_from_content(
                content=content,
                max_length=50
            )
            return title
        except Exception as e:
            logger.warning(f"Title generation from content failed: {e}")
            # Return default title
            return "Untitled Journal"
    
    async def update_journal_title(self, journal_id: str, title: str) -> JournalMetadata:
        """
        Update journal title.
        
        Args:
            journal_id: Journal ID
            title: New title
        
        Returns:
            Updated JournalMetadata
        """
        try:
            # Update title in database
            journal_metadata = self.database_storage.update_journal_title(
                journal_id=journal_id,
                title=title
            )
            
            logger.info(f"Updated journal title: {journal_id} -> {title}")
            return journal_metadata
            
        except Exception as e:
            logger.error(f"Failed to update journal title: {e}")
            raise
    