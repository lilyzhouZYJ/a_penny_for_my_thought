# How Chat Works - Complete Code Flow Documentation

This document provides a detailed technical overview of the chat functionality in the "A Penny for My Thoughts" application, tracing the complete flow from user input to AI response and data persistence.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Frontend Flow](#frontend-flow)
3. [Backend API Layer](#backend-api-layer)
4. [Service Layer](#service-layer)
5. [Storage Layer](#storage-layer)
6. [Data Models](#data-models)
7. [Key Features](#key-features)
8. [Error Handling](#error-handling)
9. [Streaming vs Non-Streaming](#streaming-vs-non-streaming)

## Architecture Overview

The chat system follows a layered architecture:

```
Frontend (React/Next.js)
    ↓ HTTP API calls
Backend API Layer (FastAPI)
    ↓ Dependency Injection
Service Layer (ChatService, LLMService, RAGService, JournalService)
    ↓ Data Access
Storage Layer (DatabaseStorage, VectorStorage)
```

## Frontend Flow

### 1. User Input Handling

**Entry Point**: `frontend/components/chat/ChatInput.tsx`

When a user types a message and presses Enter or clicks Send:

```typescript
// ChatInput.tsx:28-34
const handleSend = useCallback(() => {
  const trimmedInput = input.trim();
  if (trimmedInput && !disabled) {
    onSend(trimmedInput);
    setInput('');
  }
}, [input, disabled, onSend]);
```

**Function Called**: `handleSend()` → `onSend(trimmedInput)`

### 2. Chat Context Management

**Entry Point**: `frontend/lib/context/ChatContext.tsx`

The `ChatContext` manages the entire chat state and orchestrates message sending:

```typescript
// ChatContext.tsx:47-96
const sendMessage = useCallback(async (content: string, useStreaming: boolean = true) => {
  setIsLoading(true);
  setError(null);
  
  try {
    // Create user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    
    // Try streaming first, fallback to non-streaming on error
    const updatedMessages = [...messages, userMessage];
    if (useStreaming) {
      try {
        await handleStreamingMessage(content, userMessage, updatedMessages);
      } catch (streamError) {
        console.warn('Streaming failed, falling back to non-streaming:', streamError);
        await handleNonStreamingMessage(content, userMessage, updatedMessages);
      }
    } else {
      await handleNonStreamingMessage(content, userMessage, updatedMessages);
    }
  } catch (err) {
    // Error handling...
  }
}, [messages, sendMessage]);
```

**Functions Called**: 
- `sendMessage()` → `handleStreamingMessage()` or `handleNonStreamingMessage()`

### 3. API Client Functions

**Entry Point**: `frontend/lib/api/chat.ts`

#### Streaming Flow

```typescript
// chat.ts:75-141
export async function* streamChatMessage(
  message: string,
  sessionId: string,
  conversationHistory: Message[] = [],
  useRag: boolean = true
): AsyncGenerator<StreamEvent, void, unknown> {
  const request: ChatRequest = {
    message,
    session_id: sessionId,
    conversation_history: conversationHistory,
    use_rag: useRag,
    stream: true,
  };

  const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  // Parse SSE stream
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event: StreamEvent = JSON.parse(data);
            yield event;
          } catch (e) {
            console.error('Failed to parse SSE event:', data);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
```

**Functions Called**: `streamChatMessage()` → HTTP POST to `/api/v1/chat/stream`

#### Non-Streaming Flow

```typescript
// chat.ts:31-61
export async function sendChatMessage(
  message: string,
  sessionId: string,
  conversationHistory: Message[] = [],
  useRag: boolean = true
): Promise<ChatResponse> {
  const request: ChatRequest = {
    message,
    session_id: sessionId,
    conversation_history: conversationHistory,
    use_rag: useRag,
    stream: false,
  };

  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return await response.json();
}
```

**Functions Called**: `sendChatMessage()` → HTTP POST to `/api/v1/chat`

## Backend API Layer

### 1. Chat Endpoints

**Entry Point**: `backend/app/api/v1/chat.py`

#### Non-Streaming Endpoint

```python
# chat.py:21-66
@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
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
```

**Functions Called**: `chat()` → `chat_service.send_message()`

#### Streaming Endpoint

```python
# chat.py:69-131
@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Streaming chat: session={request.session_id}")
            
            async for event in chat_service.stream_message(
                message=request.message,
                session_id=request.session_id,
                conversation_history=request.conversation_history,
                use_rag=request.use_rag
            ):
                event_data = json.dumps({
                    "type": event.type,
                    "data": event.data
                })
                yield f"data: {event_data}\n\n"
            
            logger.info("Streaming completed")
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
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
```

**Functions Called**: `chat_stream()` → `chat_service.stream_message()`

### 2. Dependency Injection

**Entry Point**: `backend/app/dependencies.py`

```python
# dependencies.py:68-76
def get_chat_service() -> ChatService:
    return ChatService(
        llm_service=get_llm_service(),
        rag_service=get_rag_service(),
        journal_service=get_journal_service(),
        database_storage=get_database_storage()
    )
```

**Functions Called**: `get_chat_service()` → Creates `ChatService` with all dependencies

## Service Layer

### 1. ChatService - Main Orchestrator

**Entry Point**: `backend/app/services/chat_service.py`

#### Non-Streaming Message Processing

```python
# chat_service.py:55-182
async def send_message(
    self,
    message: str,
    session_id: str,
    conversation_history: List[Message],
    use_rag: bool = True
) -> ChatResponse:
    start_time = time.time()
    retrieved_context = []
    retrieval_time_ms = 0
    auto_saved = False
    
    # Step 1: Retrieve RAG context from past conversations
    if use_rag:
        try:
            rag_start = time.time()
            retrieved_context = await self.rag_service.retrieve_context(
                query=message,
                top_k=5,
                similarity_threshold=0.7
            )
            retrieval_time_ms = int((time.time() - rag_start) * 1000)
            logger.info(f"Retrieved {len(retrieved_context)} context chunks in {retrieval_time_ms}ms")
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
    
    # Step 2: Build messages for LLM with conversation history
    messages_for_llm = await self._build_llm_messages(
        current_message=message,
        conversation_history=conversation_history,
        retrieved_contexts=retrieved_context
    )
    
    # Step 3: Get LLM completion
    try:
        ai_response_content = await self.llm_service.complete(
            messages=messages_for_llm,
            temperature=0.7
        )
    except Exception as e:
        logger.error(f"LLM completion failed: {e}")
        raise
    
    # Step 4: Create AI message object
    ai_message = Message(
        role="assistant",
        content=ai_response_content
    )
    
    # Step 5: Auto-save conversation to database
    try:
        save_start = time.time()
        
        # Build complete conversation including new messages
        user_message = Message(role="user", content=message)
        complete_conversation = conversation_history + [user_message, ai_message]
        
        # Generate title for new journals
        title = None
        journal_id = None
        
        if conversation_history:
            # This is a continuation - find existing conversation
            existing_journal = self.database_storage.get_journal_by_session_id(session_id)
            if existing_journal:
                journal_id = existing_journal.id
                title = existing_journal.title
            else:
                # Generate title for new conversation
                title = await self._generate_title(complete_conversation)
        else:
            # New conversation - generate title
            title = await self._generate_title(complete_conversation)
        
        # Save to database via journal service (includes RAG indexing)
        try:
            await self.journal_service.save_journal(
                session_id=session_id,
                messages=complete_conversation,
                journal_id=journal_id,
                title=title
            )
        except Exception as e:
            logger.warning(f"Journal service save failed: {e}")
        
        save_time_ms = int((time.time() - save_start) * 1000)
        auto_saved = True
        logger.info(f"Auto-saved journal in {save_time_ms}ms")
        
    except Exception as e:
        logger.error(f"Auto-save failed: {e}")
    
    # Step 6: Build response with metadata
    total_time_ms = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        message=ai_message,
        retrieved_context=retrieved_context,
        auto_saved=auto_saved,
        metadata={
            "retrieval_time_ms": retrieval_time_ms,
            "response_time_ms": total_time_ms,
            "tokens_used": 0,
            "context_chunks_retrieved": len(retrieved_context),
            "conversation_length": len(conversation_history) + 2
        }
    )
```

**Functions Called**:
- `send_message()` → `rag_service.retrieve_context()`
- `send_message()` → `_build_llm_messages()`
- `send_message()` → `llm_service.complete()`
- `send_message()` → `journal_service.save_journal()`

#### Streaming Message Processing

```python
# chat_service.py:184-326
async def stream_message(
    self,
    message: str,
    session_id: str,
    conversation_history: List[Message],
    use_rag: bool = True
) -> AsyncGenerator[StreamEvent, None]:
    start_time = time.time()
    retrieved_context = []
    auto_saved = False
    
    try:
        # Step 1: Retrieve RAG context
        if use_rag:
            try:
                rag_start = time.time()
                retrieved_context = await self.rag_service.retrieve_context(
                    query=message,
                    top_k=5,
                    similarity_threshold=0.7
                )
                retrieval_time_ms = int((time.time() - rag_start) * 1000)
                
                # Yield context event
                yield StreamEvent(
                    type="context",
                    data={
                        "contexts": [
                            {
                                "content": ctx.content,
                                "metadata": ctx.metadata,
                                "similarity": ctx.similarity_score
                            }
                            for ctx in retrieved_context
                        ],
                        "retrieval_time_ms": retrieval_time_ms
                    }
                )
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        # Step 2: Build messages for LLM
        messages_for_llm = await self._build_llm_messages(
            current_message=message,
            conversation_history=conversation_history,
            retrieved_contexts=retrieved_context
        )
        
        # Step 3: Stream LLM response
        ai_response_content = ""
        
        async for token in self.llm_service.stream_complete(
            messages=messages_for_llm,
            temperature=0.7
        ):
            ai_response_content += token
            
            # Yield token event
            yield StreamEvent(
                type="token",
                data={"content": token}
            )
        
        # Step 4: Create AI message
        ai_message = Message(
            role="assistant",
            content=ai_response_content
        )
        
        # Step 5: Auto-save conversation to database
        try:
            # Build complete conversation including new messages
            user_message = Message(role="user", content=message)
            complete_conversation = conversation_history + [user_message, ai_message]
            
            # Generate title for new journals
            title = None
            journal_id = None
            
            if conversation_history:
                # This is a continuation - find existing conversation
                existing_journal = self.database_storage.get_journal_by_session_id(session_id)
                if existing_journal:
                    journal_id = existing_journal.id
                    title = existing_journal.title
                else:
                    # Generate title for new conversation
                    title = await self._generate_title(complete_conversation)
            else:
                # New conversation - generate title
                title = await self._generate_title(complete_conversation)
            
            # Save to database via journal service (includes RAG indexing)
            try:
                await self.journal_service.save_journal(
                    session_id=session_id,
                    messages=complete_conversation,
                    journal_id=journal_id,
                    title=title
                )
            except Exception as e:
                logger.warning(f"Journal service save failed: {e}")
            
            auto_saved = True
            logger.info("Auto-saved streaming journal")
            
        except Exception as e:
            logger.error(f"Auto-save failed during streaming: {e}")
        
        # Step 6: Yield completion event
        total_time_ms = int((time.time() - start_time) * 1000)
        
        yield StreamEvent(
            type="done",
            data={
                "metadata": {
                    "response_time_ms": total_time_ms,
                    "auto_saved": auto_saved,
                    "context_chunks_retrieved": len(retrieved_context)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        yield StreamEvent(
            type="error",
            data={"message": str(e)}
        )
```

**Functions Called**:
- `stream_message()` → `rag_service.retrieve_context()`
- `stream_message()` → `_build_llm_messages()`
- `stream_message()` → `llm_service.stream_complete()`
- `stream_message()` → `journal_service.save_journal()`

### 2. LLM Service

**Entry Point**: `backend/app/services/llm_service.py`

#### Non-Streaming Completion

```python
# llm_service.py:44-87
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
async def complete(
    self,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    try:
        client = self.get_async_client(self.api_key)
        
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content or ""
        
        logger.info(f"LLM completion: {response.usage.total_tokens} tokens used")
        
        return content
        
    except Exception as e:
        logger.error(f"LLM completion failed: {e}")
        raise LLMError(str(e))
```

**Functions Called**: `complete()` → OpenAI API `chat.completions.create()`

#### Streaming Completion

```python
# llm_service.py:89-125
async def stream_complete(
    self,
    messages: List[Dict[str, str]],
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    try:
        client = self.get_async_client(self.api_key)
        
        stream = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
        
        logger.info("LLM streaming completed")
        
    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        raise LLMError(str(e))
```

**Functions Called**: `stream_complete()` → OpenAI API `chat.completions.create(stream=True)`

### 3. RAG Service

**Entry Point**: `backend/app/services/rag_service.py`

#### Context Retrieval

```python
# rag_service.py:28-69
async def retrieve_context(
    self,
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7
) -> List[RetrievedContext]:
    try:
        # Perform similarity search
        results = await self.vector_storage.similarity_search(
            query=query,
            top_k=top_k
        )
        
        # Filter by similarity threshold
        filtered_results = [
            ctx for ctx in results
            if ctx.similarity_score >= similarity_threshold
        ]
        
        logger.info(
            f"Retrieved {len(filtered_results)}/{len(results)} contexts "
            f"above threshold {similarity_threshold}"
        )
        
        return filtered_results
        
    except Exception as e:
        logger.warning(f"Context retrieval failed: {e}")
        # Return empty list for graceful degradation
        return []
```

**Functions Called**: `retrieve_context()` → `vector_storage.similarity_search()`

#### Conversation Indexing

```python
# rag_service.py:71-129
async def index_conversation(
    self,
    messages: List[Message],
    session_id: str,
    metadata: Dict
) -> None:
    try:
        # Chunk conversation into user+assistant pairs
        chunks = self._chunk_conversation(messages)
        
        if not chunks:
            logger.warning("No chunks created from conversation")
            return
        
        # Prepare data for vector store
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk['content'])
            
            # Combine metadata
            chunk_metadata = {
                **metadata,
                'session_id': session_id,
                'chunk_index': i,
                'message_ids': chunk['message_ids']
            }
            metadatas.append(chunk_metadata)
            
            # Generate unique ID for this chunk
            chunk_id = f"{session_id}_chunk_{i}_{uuid4().hex[:8]}"
            ids.append(chunk_id)
        
        # Add to vector store
        await self.vector_storage.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Indexed {len(chunks)} chunks from session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to index conversation: {e}")
```

**Functions Called**: `index_conversation()` → `_chunk_conversation()` → `vector_storage.add_documents()`

### 4. Journal Service

**Entry Point**: `backend/app/services/journal_service.py`

#### Journal Saving

```python
# journal_service.py:42-97
async def save_journal(
    self,
    session_id: str,
    messages: List[Message],
    journal_id: Optional[str] = None,
    title: Optional[str] = None
) -> JournalMetadata:
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
```

**Functions Called**: 
- `save_journal()` → `database_storage.save_journal()`
- `save_journal()` → `rag_service.index_conversation()`

## Storage Layer

### 1. Database Storage

**Entry Point**: `backend/app/storage/database.py`

The `DatabaseStorage` class handles SQLite database operations for persistent storage of conversations and journals.

### 2. Vector Storage

**Entry Point**: `backend/app/storage/vector_storage.py`

The `VectorStorage` class handles ChromaDB operations for semantic search and RAG functionality.

## Data Models

### Frontend Types

**Entry Point**: `frontend/lib/types/chat.ts`

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any> | null;
}

export interface ChatRequest {
  message: string;
  session_id: string;
  conversation_history: Message[];
  use_rag?: boolean;
  stream?: boolean;
}

export interface ChatResponse {
  message: Message;
  retrieved_context: RetrievedContext[];
  metadata: Record<string, any>;
  auto_saved: boolean;
}

export interface StreamEvent {
  type: 'token' | 'context' | 'done' | 'error';
  data: Record<string, any>;
}
```

### Backend Models

**Entry Point**: `backend/app/models/chat.py`

```python
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str
    conversation_history: List[Message] = Field(default_factory=list)
    use_rag: bool = True
    stream: bool = False

class ChatResponse(BaseModel):
    message: Message
    retrieved_context: List[RetrievedContext] = []
    metadata: Dict = Field(default_factory=dict)
    auto_saved: bool = False

class StreamEvent(BaseModel):
    type: Literal["token", "context", "done", "error"]
    data: Dict
```

## Key Features

### 1. In-Conversation Memory

The system maintains conversation history by:
- Sending the full conversation history with each request
- Using token counting and dynamic summarization to manage context length
- Keeping recent messages in full while summarizing older ones

**Implementation**: `chat_service.py:_manage_conversation_history()`

### 2. RAG (Retrieval-Augmented Generation)

The system retrieves relevant context from past conversations by:
- Indexing conversations in a vector database (ChromaDB)
- Performing semantic similarity search on user queries
- Including retrieved context in the LLM prompt

**Implementation**: `rag_service.py:retrieve_context()` and `rag_service.py:index_conversation()`

### 3. Automatic Journal Saving

Every conversation is automatically saved as a journal entry:
- Conversations are saved to SQLite database
- Vector embeddings are generated for semantic search
- Titles are auto-generated using LLM

**Implementation**: `journal_service.py:save_journal()`

### 4. Streaming Support

The system supports both streaming and non-streaming responses:
- Streaming uses Server-Sent Events (SSE)
- Tokens are yielded as they are generated
- Graceful fallback to non-streaming on errors

**Implementation**: `chat_service.py:stream_message()` and `llm_service.py:stream_complete()`

## Error Handling

### Frontend Error Handling

**Entry Point**: `frontend/lib/utils/error-handlers.ts`

The frontend implements graceful error handling with:
- Retry mechanisms for recoverable errors
- Fallback from streaming to non-streaming
- User-friendly error messages

### Backend Error Handling

The backend implements comprehensive error handling:
- Service-level error handling with graceful degradation
- RAG failures don't prevent chat from working
- Journal save failures don't prevent AI responses
- Proper HTTP status codes and error messages

## Streaming vs Non-Streaming

### Streaming Flow

1. User sends message → `ChatInput.handleSend()`
2. `ChatContext.sendMessage()` → `handleStreamingMessage()`
3. `streamChatMessage()` → HTTP POST to `/api/v1/chat/stream`
4. `chat_stream()` → `chat_service.stream_message()`
5. `stream_message()` yields `StreamEvent` objects:
   - `context`: Retrieved RAG context
   - `token`: Individual AI response tokens
   - `done`: Completion metadata
   - `error`: Error information
6. Frontend processes SSE stream and updates UI in real-time

### Non-Streaming Flow

1. User sends message → `ChatInput.handleSend()`
2. `ChatContext.sendMessage()` → `handleNonStreamingMessage()`
3. `sendChatMessage()` → HTTP POST to `/api/v1/chat`
4. `chat()` → `chat_service.send_message()`
5. `send_message()` returns complete `ChatResponse`
6. Frontend updates UI with complete response

Both flows include the same features:
- RAG context retrieval
- Conversation history management
- Automatic journal saving
- Error handling and graceful degradation

## Summary

The chat system is a sophisticated application that combines multiple technologies:

- **Frontend**: React/Next.js with TypeScript for type safety
- **Backend**: FastAPI with Python for high-performance API
- **AI**: OpenAI GPT models for intelligent responses
- **Storage**: SQLite for persistence, ChromaDB for vector search
- **Architecture**: Layered design with dependency injection
- **Features**: Memory, RAG, streaming, auto-saving, error handling

The complete flow ensures users get intelligent, contextual responses while maintaining conversation history and enabling semantic search across past conversations.
