"""Unit tests for markdown formatting utilities."""

import pytest
from datetime import datetime

from app.models import Message
from app.utils.markdown_formatter import format_journal_markdown, parse_journal_markdown


class TestMarkdownFormatter:
    """Tests for markdown formatting functions."""
    
    def test_format_journal_markdown_basic(self):
        """Test basic markdown formatting."""
        messages = [
            Message(
                id="msg-1",
                role="user",
                content="Hello, how are you?",
                timestamp=datetime(2025, 1, 15, 10, 30, 0)
            ),
            Message(
                id="msg-2",
                role="assistant",
                content="I'm doing well, thank you!",
                timestamp=datetime(2025, 1, 15, 10, 30, 5)
            )
        ]
        
        result = format_journal_markdown(
            title="Test Conversation",
            session_id="session-123",
            messages=messages,
            created_at=datetime(2025, 1, 15, 10, 30, 0)
        )
        
        # Check frontmatter
        assert "---" in result
        assert "title: Test Conversation" in result
        assert "session_id: session-123" in result
        assert "message_count: 2" in result
        
        # Check title header
        assert "# Test Conversation" in result
        
        # Check messages
        assert "**User** — *10:30:00*" in result
        assert "Hello, how are you?" in result
        assert "**Assistant** — *10:30:05*" in result
        assert "I'm doing well, thank you!" in result
        
        # Check footer
        assert "Journal entry automatically generated" in result
    
    def test_format_journal_markdown_with_duration(self):
        """Test markdown formatting with duration."""
        messages = [
            Message(role="user", content="Hi")
        ]
        
        result = format_journal_markdown(
            title="Quick Chat",
            session_id="session-123",
            messages=messages,
            created_at=datetime.now(),
            duration_seconds=125  # 2 minutes 5 seconds
        )
        
        # Check duration in frontmatter
        assert "duration: 125" in result
        
        # Check duration in header
        assert "2m 5s" in result
    
    def test_format_skips_system_messages(self):
        """Test that system messages are not included in saved journal."""
        messages = [
            Message(role="system", content="System message"),
            Message(role="user", content="User message"),
            Message(role="assistant", content="Assistant message")
        ]
        
        result = format_journal_markdown(
            title="Test",
            session_id="session-123",
            messages=messages,
            created_at=datetime.now()
        )
        
        # System message should not appear
        assert "System message" not in result
        
        # User and assistant should appear
        assert "User message" in result
        assert "Assistant message" in result
    
    def test_parse_journal_markdown(self):
        """Test parsing markdown to extract metadata."""
        markdown = """---
title: Test Journal
date: 2025-01-15 10:30:00 UTC
session_id: session-123
message_count: 2
---

# Test Journal

Content here...
"""
        
        metadata = parse_journal_markdown(markdown)
        
        assert metadata["title"] == "Test Journal"
        assert metadata["session_id"] == "session-123"
        assert metadata["message_count"] == "2"
    
    def test_parse_markdown_without_frontmatter(self):
        """Test parsing markdown without frontmatter."""
        markdown = "# Just a title\n\nSome content"
        
        metadata = parse_journal_markdown(markdown)
        
        # Should return empty dict
        assert metadata == {}

