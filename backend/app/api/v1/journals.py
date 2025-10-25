import json
import logging
from typing import List, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models import (
    CreateJournalRequest,
    Journal,
    JournalMetadata,
    JournalNotFoundError,
    UpdateWriteContentRequest,
    AskAIRequest,
    UpdateJournalTitleRequest,
)
from app.services.journal_service import JournalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/journals", tags=["journals"])


# Import dependency injection
from app.dependencies import get_journal_service


@router.get("", response_model=dict)
async def list_journals(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="date"),
    journal_service: JournalService = Depends(get_journal_service)
):
    """
    List all journal entries with pagination.
    
    Args:
        limit: Maximum number of journals to return (1-100)
        offset: Number of journals to skip
        sort_by: Sort field (currently only 'date' supported)
        journal_service: Injected JournalService
    
    Returns:
        Dict with journals list and pagination info
    """
    try:
        journals, total = await journal_service.list_journals(
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


@router.get("/{journal_id}", response_model=Journal)
async def get_journal(
    journal_id: str,
    journal_service: JournalService = Depends(get_journal_service)
) -> Journal:
    """
    Get a specific journal entry.
    
    Used to load past conversations into the chat interface for continuation.
    Reads from MARKDOWN FILE on disk (NOT from ChromaDB).
    
    Args:
        journal_id: Journal filename
        journal_service: Injected JournalService
    
    Returns:
        Full journal with messages and raw markdown content
    
    Raises:
        HTTPException 404: If journal not found
    """
    try:
        journal = await journal_service.get_journal(journal_id)
        
        logger.info(f"Retrieved journal: {journal_id} ({journal.message_count} messages)")
        
        return journal
        
    except JournalNotFoundError as e:
        logger.warning(f"Journal not found: {journal_id}")
        raise e
    except Exception as e:
        logger.error(f"Failed to get journal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve journal: {str(e)}"
        )


@router.post("", response_model=JournalMetadata)
async def save_journal(
    request: CreateJournalRequest,
    journal_service: JournalService = Depends(get_journal_service)
) -> JournalMetadata:
    """
    Save or update a journal entry.
    
    If journal_id is provided in request, updates existing journal.
    If journal_id is None/missing, creates new journal.
    
    Args:
        request: Journal creation/update request
        journal_service: Injected JournalService
    
    Returns:
        JournalMetadata with saved journal information
    """
    try:
        result = await journal_service.save_journal(
            session_id=request.session_id,
            messages=request.messages,
            journal_id=request.journal_id,
            title=request.title
        )
        
        action = "Updated" if request.journal_id else "Created"
        logger.info(f"{action} journal: {result.filename}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to save journal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save journal: {str(e)}"
        )


@router.delete("/{journal_id}")
async def delete_journal(
    journal_id: str,
    journal_service: JournalService = Depends(get_journal_service)
):
    """
    Delete a journal entry.
    
    Removes from both filesystem and vector database.
    
    Args:
        journal_id: Journal filename to delete
        journal_service: Injected JournalService
    
    Returns:
        Success message
    
    Raises:
        HTTPException 404: If journal not found
    """
    try:
        await journal_service.delete_journal(journal_id)
        
        logger.info(f"Deleted journal: {journal_id}")
        
        return {
            "success": True,
            "message": f"Journal {journal_id} deleted successfully"
        }
        
    except JournalNotFoundError as e:
        logger.warning(f"Journal not found for deletion: {journal_id}")
        raise e
    except Exception as e:
        logger.error(f"Failed to delete journal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete journal: {str(e)}"
        )


@router.put("/write-content", response_model=JournalMetadata)
async def update_write_content(
    request: UpdateWriteContentRequest,
    journal_service: JournalService = Depends(get_journal_service)
) -> JournalMetadata:
    """
    Update write mode content.
    
    Args:
        request: Write content update request
        journal_service: Injected JournalService
    
    Returns:
        JournalMetadata with updated journal information
    """
    try:
        result = await journal_service.update_write_content(
            session_id=request.session_id,
            content=request.content,
            journal_id=request.journal_id,
            title=request.title
        )
        
        logger.info(f"Updated write content for journal: {result.filename}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to update write content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update write content: {str(e)}"
        )


@router.post("/ask-ai", response_model=dict)
async def ask_ai_for_input(
    request: AskAIRequest,
    journal_service: JournalService = Depends(get_journal_service)
):
    """
    Ask AI for input on write mode content.
    
    Args:
        request: AI input request
        journal_service: Injected JournalService
    
    Returns:
        AI response message
    """
    try:
        response = await journal_service.ask_ai_for_input(
            session_id=request.session_id,
            content=request.content,
            conversation_history=request.conversation_history,
            journal_id=request.journal_id
        )
        
        logger.info(f"AI provided input for write content")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get AI input: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI input: {str(e)}"
        )


@router.post("/ask-ai/stream")
async def ask_ai_for_input_stream(
    request: AskAIRequest,
    journal_service: JournalService = Depends(get_journal_service)
):
    """
    Stream AI input for write mode content using Server-Sent Events (SSE).
    
    Args:
        request: AI input request
        journal_service: Injected JournalService
    
    Returns:
        StreamingResponse with SSE events
    
    Event Types:
        - token: Individual tokens from AI
        - done: Completion metadata
        - error: Error information
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            logger.info(f"Streaming AI input for write content: session={request.session_id}")
            
            async for event in journal_service.stream_ai_for_input(
                session_id=request.session_id,
                content=request.content,
                conversation_history=request.conversation_history,
                journal_id=request.journal_id
            ):
                # Format as SSE: "data: {json}\n\n"
                event_data = json.dumps({
                    "type": event.type,
                    "data": event.data
                })
                yield f"data: {event_data}\n\n"
            
            logger.info("AI input streaming completed")
            
        except Exception as e:
            logger.error(f"AI input streaming error: {e}")
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

@router.put("/title", response_model=JournalMetadata)
async def update_journal_title(
    request: UpdateJournalTitleRequest,
    journal_service: JournalService = Depends(get_journal_service)
) -> JournalMetadata:
    """
    Update journal title.
    """
    try:
        journal_metadata = await journal_service.update_journal_title(
            journal_id=request.journal_id,
            title=request.title
        )
        
        logger.info(f"Updated journal title: {request.journal_id}")
        
        return journal_metadata
        
    except JournalNotFoundError as e:
        logger.warning(f"Journal not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"Failed to update journal title: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update journal title: {str(e)}"
        )

