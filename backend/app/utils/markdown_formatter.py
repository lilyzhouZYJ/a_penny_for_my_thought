from datetime import datetime
from typing import List, Optional

from app.models import Message

def format_journal_markdown(
    title: str,
    session_id: str,
    messages: List[Message],
    created_at: datetime,
    duration_seconds: Optional[int] = None
) -> str:
    """
    Format conversation as markdown journal entry.
    
    Each markdown journal entry includes:
    - Frontmatter with metadata
    - Title and session info
    - Conversation with speaker labels and timestamps
    
    Args:
        title: Journal title
        session_id: Session UUID
        messages: List of conversation messages
        created_at: When the conversation started
        duration_seconds: Optional conversation duration
    
    Returns:
        Formatted markdown content
    """
    # Format duration
    duration_str = ""
    if duration_seconds is not None:
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
    
    # Build frontmatter
    frontmatter = f"""---
title: {title}
date: {created_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
session_id: {session_id}
message_count: {len(messages)}"""
    
    if duration_seconds is not None:
        frontmatter += f"\nduration: {duration_seconds}"
    
    frontmatter += "\n---\n\n"
    
    # Build header
    header = f"""# {title}

**Session Date:** {created_at.strftime("%B %d, %Y at %I:%M %p")}"""
    
    if duration_str:
        header += f"  \n**Duration:** {duration_str}"
    
    header += "\n\n---\n\n## Conversation\n\n"
    
    # Build conversation
    conversation = ""
    for msg in messages:
        # Skip system messages in the saved journal
        if msg.role == "system":
            continue
        
        role_label = "User" if msg.role == "user" else "Assistant"
        timestamp_str = msg.timestamp.strftime("%H:%M:%S")
        
        conversation += f"**{role_label}** — *{timestamp_str}*  \n{msg.content}\n\n"
    
    # Build footer
    footer = "---\n\n*Journal entry automatically generated*\n"
    
    return frontmatter + header + conversation + footer

def parse_journal_markdown(content: str) -> dict:
    """
    Parse markdown journal to extract metadata and messages.
    
    Args:
        content: Markdown content
    
    Returns:
        Dictionary with session_id, title, messages list, etc.
    """
    # This is a simple parser - could be enhanced
    # Extract frontmatter
    metadata = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            for line in frontmatter.strip().split("\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    metadata[key.strip()] = value.strip()
    
    return metadata

