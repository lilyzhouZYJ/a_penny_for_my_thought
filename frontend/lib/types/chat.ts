/**
 * Chat-related TypeScript types.
 * 
 * These interfaces match the backend Pydantic models to ensure type safety
 * across the frontend-backend boundary.
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;  // ISO string from backend
  metadata?: Record<string, any> | null;
}

export interface RetrievedContext {
  content: string;
  metadata: Record<string, any>;
  similarity_score: number;
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

export interface ChatConfig {
  storageDirectory: string;
  retrievalCount: number;
  streamingEnabled: boolean;
  modelName: string;
}

