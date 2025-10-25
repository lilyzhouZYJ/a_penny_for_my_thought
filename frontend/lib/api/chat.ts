/**
 * Chat API client functions.
 */

import {
  ChatRequest,
  ChatResponse,
  Message,
  StreamEvent,
} from '@/lib/types/chat';
import { JournalMetadata } from '@/lib/types/journal';

import { config } from '@/lib/config';

const API_URL = config.apiUrl;

/**
 * Send a chat message and get AI response.
 * 
 * Features:
 * - In-conversation memory (send full conversation history)
 * - RAG context from past journals
 * - Automatic saving after response
 * 
 * @param message - User's message
 * @param sessionId - Session UUID
 * @param conversationHistory - Full conversation history for memory
 * @param useRag - Whether to use RAG for context retrieval
 * @returns ChatResponse with AI message and auto-save status
 */
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

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to send message',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}


/**
 * Stream chat message response using Server-Sent Events.
 * 
 * Yields tokens as they are generated for real-time UI updates.
 * 
 * @param message - User's message
 * @param sessionId - Session UUID
 * @param conversationHistory - Full conversation history
 * @param useRag - Whether to use RAG
 * @yields StreamEvent objects (token, context, done, error)
 */
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

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to stream message',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Parse SSE stream
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Split by SSE event boundaries
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // Remove "data: " prefix

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

/**
 * Load chat history for a session.
 * 
 * @param sessionId - Session UUID
 * @returns List of messages in chronological order
 */
export async function loadChatHistory(sessionId: string): Promise<Message[]> {
  // This function is deprecated - use getJournal from journals.ts instead
  // The backend doesn't have a chat/history endpoint
  throw new Error('loadChatHistory is deprecated. Use getJournal from journals API instead.');
}

/**
 * List all journals with pagination.
 * 
 * @param limit - Maximum number of journals to return
 * @param offset - Number of journals to skip
 * @param sortBy - Sort field ('created_at' or 'updated_at')
 * @returns Object with journals list and pagination info
 */
export async function listJournals(
  limit: number = 50,
  offset: number = 0,
  sortBy: string = 'created_at'
): Promise<{ journals: JournalMetadata[]; total: number; limit: number; offset: number }> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    sort_by: sortBy,
  });

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(`${API_URL}/api/v1/chat/journals?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: 'Failed to list journals',
      }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please check your connection and try again.');
    }
    throw error;
  }
}

/**
 * Delete a journal by ID.
 * 
 * @param journalId - The ID of the journal to delete
 * @returns Success message
 */
export async function deleteJournal(journalId: string): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/api/v1/chat/journals/${journalId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Failed to delete journal',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}