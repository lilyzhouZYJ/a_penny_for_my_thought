'use client';

/**
 * Chat Context for global chat state management.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Message } from '@/lib/types/chat';
import { JournalMetadata } from '@/lib/types/journal';
import { sendChatMessage } from '@/lib/api/chat';
import { getJournal, saveJournal as saveJournalApi } from '@/lib/api/journals';

interface ChatContextType {
  // State
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  currentJournalId: string | null;
  
  // Actions
  sendMessage: (content: string) => Promise<void>;
  loadSession: (journalId: string) => Promise<void>;
  saveSession: () => Promise<JournalMetadata | null>;
  clearChat: () => void;
  
  // Utility
  setError: (error: string | null) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentJournalId, setCurrentJournalId] = useState<string | null>(null);
  
  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Create user message
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      
      // Add user message to state immediately
      setMessages(prev => [...prev, userMessage]);
      
      // Send to backend with full conversation history
      const response = await sendChatMessage(
        content,
        sessionId,
        [...messages, userMessage],  // Include new message in history
        true  // use_rag
      );
      
      // Add AI response to state
      setMessages(prev => [...prev, response.message]);
      
      // If auto-saved and we don't have a journal ID yet, we should track it
      // (Note: Backend returns metadata in response if needed)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      console.error('Send message error:', err);
      
      // Remove the user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  }, [messages, sessionId]);
  
  const loadSession = useCallback(async (journalId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch journal from backend
      const journal = await getJournal(journalId);
      
      // Set state from loaded journal
      setMessages(journal.messages);
      setSessionId(journal.id);  // Use journal's session ID
      setCurrentJournalId(journalId);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load session';
      setError(errorMessage);
      console.error('Load session error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  const saveSession = useCallback(async (): Promise<JournalMetadata | null> => {
    if (messages.length === 0) {
      setError('No messages to save');
      return null;
    }
    
    setError(null);
    
    try {
      const metadata = await saveJournalApi(
        sessionId,
        messages,
        currentJournalId,  // Update existing if we have a journal ID
        null  // Auto-generate title
      );
      
      // Update current journal ID if this was a new save
      if (!currentJournalId) {
        setCurrentJournalId(metadata.filename);
      }
      
      return metadata;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save session';
      setError(errorMessage);
      console.error('Save session error:', err);
      return null;
    }
  }, [sessionId, messages, currentJournalId]);
  
  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId(crypto.randomUUID());
    setCurrentJournalId(null);
    setError(null);
  }, []);
  
  const value: ChatContextType = {
    sessionId,
    messages,
    isLoading,
    error,
    currentJournalId,
    sendMessage,
    loadSession,
    saveSession,
    clearChat,
    setError,
  };
  
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  
  return context;
}

