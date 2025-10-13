/**
 * Journal-related TypeScript types.
 * 
 * These interfaces match the backend Pydantic models.
 */

import { Message } from './chat';

export interface JournalMetadata {
  id: string;
  filename: string;
  title: string;
  date: string;  // ISO string from backend
  message_count: number;
  duration_seconds: number | null;
}

export interface Journal extends JournalMetadata {
  messages: Message[];
  raw_content: string;
}

export interface CreateJournalRequest {
  session_id: string;
  journal_id: string | null;
  messages: Message[];
  title: string | null;
}

export interface JournalListResponse {
  journals: JournalMetadata[];
  total: number;
  limit: number;
  offset: number;
}

