from datetime import datetime
from typing import List, Optional

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

