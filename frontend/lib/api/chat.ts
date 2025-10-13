/**
 * Chat API client functions.
 */

import {
  ChatRequest,
  ChatResponse,
  Message,
  StreamEvent,
} from '@/lib/types/chat';

import { config } from '@/lib/config';

const API_URL = config.apiUrl;

/**
 * Send a chat message and get AI response.
 * 
 * Features:
 * - In-conversation memory (send full conversation history)
 * - RAG context from past conversations
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

