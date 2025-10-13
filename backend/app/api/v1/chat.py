import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.models import ChatRequest, ChatResponse, LLMError
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# Import dependency injection
from app.dependencies import get_chat_service


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

