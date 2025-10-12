from datetime import datetime
from typing import Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

class Message(BaseModel):
    """
    Individual message in a conversation.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
    metadata: Optional[Dict] = None

class RetrievedContext(BaseModel):
    """
    Context retrieved from vector store for RAG.
    """
    content: str
    metadata: Dict
    similarity_score: float

class ChatRequest(BaseModel):
    """
    Request for chat completion.
    """
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str
    use_rag: bool = True
    stream: bool = False

class ChatResponse(BaseModel):
    """
    Response from chat completion.
    """
    message: Message
    retrieved_context: List[RetrievedContext] = []
    metadata: Dict = Field(default_factory=dict)

class StreamEvent(BaseModel):
    """
    Event in a streaming response.
    """
    type: Literal["token", "context", "done", "error"]
    data: Dict

