import json
import logging
from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models import ChatRequest, ChatResponse, LLMError, Message, JournalMetadata
from app.services.chat_service import ChatService
from app.storage.database import DatabaseStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# Import dependency injection
from app.dependencies import get_chat_service, get_database_storage


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """
    Send a chat message and get AI response.
    
    Features:
    - In-conversation memory (AI remembers earlier messages)
    - RAG context from past conversations
    - Automatic saving after response
    
    Args:
        request: Chat request with message, session_id, and conversation_history
        chat_service: Injected ChatService
    
    Returns:
        ChatResponse with AI message, retrieved context, and auto-save status
    
    Raises:
        HTTPException: If chat processing fails
    """
    try:
        logger.info(f"Chat request: session={request.session_id}, history_length={len(request.conversation_history)}")
        
        response = await chat_service.send_message(
            message=request.message,
            session_id=request.session_id,
            conversation_history=request.conversation_history,
            use_rag=request.use_rag
        )
        
        logger.info(f"Chat response: auto_saved={response.auto_saved}, contexts={len(response.retrieved_context)}")
        
        return response
        
    except LLMError as e:
        logger.error(f"LLM error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Stream chat response using Server-Sent Events (SSE).
    
    Features:
    - Tokens appear incrementally as generated
    - Same memory and auto-save as non-streaming
    
    Args:
        request: Chat request with message, session_id, and conversation_history
        chat_service: Injected ChatService
    
    Returns:
        StreamingResponse with SSE events
    
    Event Types:
        - context: Retrieved RAG context
        - token: Individual tokens from AI
        - done: Completion metadata
        - error: Error information
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            logger.info(f"Streaming chat: session={request.session_id}")
            
            async for event in chat_service.stream_message(
                message=request.message,
                session_id=request.session_id,
                conversation_history=request.conversation_history,
                use_rag=request.use_rag
            ):
                # Format as SSE: "data: {json}\n\n"
                event_data = json.dumps({
                    "type": event.type,
                    "data": event.data
                })
                yield f"data: {event_data}\n\n"
            
            logger.info("Streaming completed")
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            # Send error event
            error_data = json.dumps({
                "type": "error",
                "data": {"message": str(e)}
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/history/{session_id}", response_model=List[Message])
async def get_chat_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
) -> List[Message]:
    """
    Load chat history for a session.
    
    Args:
        session_id: Session UUID
        chat_service: Injected ChatService
    
    Returns:
        List of messages in chronological order
    
    Raises:
        HTTPException: If loading history fails
    """
    try:
        logger.info(f"Loading chat history for session: {session_id}")
        
        messages = await chat_service.load_chat_history(session_id)
        
        logger.info(f"Loaded {len(messages)} messages for session: {session_id}")
        
        return messages
        
    except Exception as e:
        logger.error(f"Failed to load chat history for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load chat history: {str(e)}"
        )


@router.get("/journals", response_model=dict)
async def list_journals(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="created_at"),
    database_storage = Depends(get_database_storage)
):
    """
    List all journals with pagination.
    
    Args:
        limit: Maximum number of journals to return (1-100)
        offset: Number of journals to skip
        sort_by: Sort field ('created_at' or 'updated_at')
        database_storage: Injected DatabaseStorage
    
    Returns:
        Dict with journals list and pagination info
    """
    try:
        journals, total = database_storage.list_journals(
            limit=limit,
            offset=offset,
            sort_by=sort_by
        )
        
        logger.info(f"Listed {len(journals)} journals (total: {total})")
        
        return {
            "journals": journals,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list journals: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list journals: {str(e)}"
        )


@router.delete("/journals/{journal_id}")
async def delete_journal(
    journal_id: str,
    database_storage: DatabaseStorage = Depends(get_database_storage)
):
    """
    Delete a journal and all its messages.
    
    Args:
        journal_id: The ID of the journal to delete
        
    Returns:
        Success message
    """
    try:
        # Check if journal exists
        try:
            journal = database_storage.get_journal(journal_id)
        except Exception:
            raise HTTPException(
                status_code=404,
                detail=f"Journal with ID '{journal_id}' not found"
            )
        
        # Delete the journal
        database_storage.delete_journal(journal_id)
        
        logger.info(f"Deleted journal: {journal_id}")
        
        return {"message": f"Journal '{journal.title}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete journal {journal_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete journal: {str(e)}"
        )



