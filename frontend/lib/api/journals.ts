/**
 * Journals API client functions.
 */

import {
  Journal,
  JournalMetadata,
  JournalListResponse,
  CreateJournalRequest,
  UpdateWriteContentRequest,
  AskAIRequest,
  UpdateJournalTitleRequest,
} from '@/lib/types/journal';

import { Message } from '@/lib/types/chat';
import { config } from '@/lib/config';

const API_URL = config.apiUrl;

/**
 * Get all journal entries with pagination.
 * 
 * @param limit - Maximum number of journals to return
 * @param offset - Number of journals to skip
 * @returns Paginated list of journal metadata
 */
export async function getAllJournals(
  limit: number = 50,
  offset: number = 0
): Promise<JournalListResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const response = await fetch(`${API_URL}/api/v1/journals?${params}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to fetch journals',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * Get a specific journal by ID.
 * 
 * Used to load past conversations into the chat interface.
 * Loads from markdown file, NOT from vector database.
 * 
 * @param journalId - Journal filename
 * @returns Full journal with messages
 */
export async function getJournal(journalId: string): Promise<Journal> {
  const response = await fetch(`${API_URL}/api/v1/journals/${journalId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Journal not found');
    }

    const error = await response.json().catch(() => ({
      detail: 'Failed to fetch journal',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * Save or update a journal entry.
 * 
 * If journalId is provided, updates existing journal.
 * If journalId is null/undefined, creates new journal.
 * 
 * @param sessionId - Session UUID
 * @param messages - All messages in conversation
 * @param journalId - Optional existing journal filename (for updates)
 * @param title - Optional custom title
 * @returns JournalMetadata for saved journal
 */
export async function saveJournal(
  sessionId: string,
  messages: Message[],
  journalId?: string | null,
  title?: string | null,
  mode: "chat" | "write" = "chat"
): Promise<JournalMetadata> {
  const request: CreateJournalRequest = {
    session_id: sessionId,
    journal_id: journalId || null,
    messages,
    title: title || null,
    mode,
  };

  const response = await fetch(`${API_URL}/api/v1/journals`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to save journal',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * Delete a journal entry.
 * 
 * Removes from both filesystem and vector database.
 * 
 * @param journalId - Journal filename to delete
 */
export async function deleteJournal(journalId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/journals/${journalId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Journal not found');
    }

    const error = await response.json().catch(() => ({
      detail: 'Failed to delete journal',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}

/**
 * Update write mode content.
 * 
 * @param sessionId - Session UUID
 * @param writeContent - The main journal content
 * @param journalId - Optional existing journal ID (for updates)
 * @param title - Optional custom title
 * @returns JournalMetadata for updated journal
 */
export async function updateWriteContent(
  sessionId: string,
  content: string,
  journalId?: string | null,
  title?: string | null
): Promise<JournalMetadata> {
  const request: UpdateWriteContentRequest = {
    session_id: sessionId,
    journal_id: journalId || null,
    content: content,
    title: title || null,
  };

  const response = await fetch(`${API_URL}/api/v1/journals/write-content`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to update write content',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * Ask AI for input on write mode content.
 * 
 * @param sessionId - Session UUID
 * @param writeContent - The main journal content
 * @param conversationHistory - Previous AI interactions
 * @param journalId - Optional journal ID
 * @returns AI response message and updated conversation history
 */
export async function askAIForInput(
  sessionId: string,
  content: string,
  conversationHistory: Message[],
  journalId?: string | null
): Promise<{ message: Message; conversation_history: Message[] }> {
  const request: AskAIRequest = {
    session_id: sessionId,
    journal_id: journalId || null,
    content: content,
    conversation_history: conversationHistory,
  };

  const response = await fetch(`${API_URL}/api/v1/journals/ask-ai`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to get AI input',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

export async function updateJournalTitle(
  journalId: string,
  title: string
): Promise<JournalMetadata> {
  const request: UpdateJournalTitleRequest = {
    journal_id: journalId,
    title: title,
  };

  const response = await fetch(`${API_URL}/api/v1/journals/title`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to update journal title',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

