from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel

from .chat import Message

class JournalMetadata(BaseModel):
    """
    Metadata for a journal entry.
    """
    id: str
    filename: str
    title: str
    date: datetime
    message_count: int
    duration_seconds: Optional[int] = None
    mode: Literal["chat", "write"] = "chat"

class Journal(JournalMetadata):
    """
    Full journal entry with messages.
    """
    messages: List[Message]
    raw_content: str

class CreateJournalRequest(BaseModel):
    """
    Request to create or update a journal entry.
    """
    session_id: str
    journal_id: Optional[str] = None  # If provided, updates existing journal
    messages: List[Message]
    title: Optional[str] = None  # Auto-generate if null
    mode: Literal["chat", "write"] = "chat"

class UpdateWriteContentRequest(BaseModel):
    """
    Request to update write mode content (as a user message).
    """
    session_id: str
    journal_id: Optional[str] = None
    content: str  # The write mode content as a user message
    title: Optional[str] = None

class AskAIRequest(BaseModel):
    """
    Request to ask AI for input on write mode content.
    """
    session_id: str
    journal_id: Optional[str] = None
    content: str  # The write mode content
    conversation_history: List[Message] = []

class UpdateJournalTitleRequest(BaseModel):
    """
    Request to update journal title.
    """
    journal_id: str
    title: str

