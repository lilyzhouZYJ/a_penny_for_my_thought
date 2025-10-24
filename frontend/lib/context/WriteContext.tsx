'use client';

/**
 * Write Context for global write mode state management.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { Message } from '@/lib/types/chat';
import { JournalMetadata } from '@/lib/types/journal';
import { updateWriteContent, askAIForInput, getJournal } from '@/lib/api/journals';

interface WriteContextType {
  // State
  sessionId: string;
  writeContent: string;  // Current write content (draft)
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;
  currentJournalId: string | null;
  conversationRefreshTrigger: number;
  
  // Actions
  updateWriteContent: (content: string) => Promise<void>;
  askAIForInput: (content: string) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  clearWrite: () => string;
  handleNewWrite: () => void;
  
  // Utility
  setError: (error: string | null) => void;
  refreshConversations: () => void;
}

const WriteContext = createContext<WriteContextType | undefined>(undefined);

export function WriteProvider({ children }: { children: ReactNode }) {
  // Use router if available (in app), otherwise use a mock for tests
  let router: any;
  try {
    router = useRouter();
  } catch {
    // Mock router for tests
    router = {
      push: (path: string) => {
        console.log('Mock router push:', path);
      }
    };
  }
  
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [writeContent, setWriteContent] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [currentJournalId, setCurrentJournalId] = useState<string | null>(null);
  const [conversationRefreshTrigger, setConversationRefreshTrigger] = useState(0);
  
  const updateWriteContentAction = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await updateWriteContent(
        sessionId,
        content,
        currentJournalId,
        undefined // Let AI generate title
      );
      
      setWriteContent(content);
      setCurrentJournalId(result.id);
      
      // If this was the first write, refresh the conversation list
      if (!currentJournalId) {
        setConversationRefreshTrigger(prev => prev + 1);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update write content';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, currentJournalId]);
  
  const askAIForInputAction = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await askAIForInput(
        sessionId,
        content,
        messages,
        currentJournalId
      );
      
      // Add the AI message to the conversation history
      setMessages(prev => [...prev, response.message]);
      
      // Update the conversation history
      setMessages(response.conversation_history);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get AI input';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, messages, currentJournalId]);
  
  const loadSession = useCallback(async (sessionIdToLoad: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load journal from database
      const journal = await getJournal(sessionIdToLoad);
      
      // Extract write content from the first user message (if any)
      const firstUserMessage = journal.messages.find(msg => msg.role === 'user');
      const writeContent = firstUserMessage?.content || '';
      
      // Set state from loaded journal
      setWriteContent(writeContent);
      setMessages(journal.messages);
      setSessionId(sessionIdToLoad);
      setCurrentJournalId(sessionIdToLoad);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load session';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  const clearWrite = useCallback(() => {
    const newSessionId = crypto.randomUUID();
    setWriteContent('');
    setMessages([]);
    setSessionId(newSessionId);
    setCurrentJournalId(null);
    setError(null);
    return newSessionId;
  }, []);
  
  const refreshConversations = useCallback(() => {
    // Trigger conversation list refresh by incrementing the trigger
    setConversationRefreshTrigger(prev => prev + 1);
  }, []);
  
  const handleNewWrite = useCallback(() => {
    const newSessionId = clearWrite();
    router.push(`/write/${newSessionId}`);
  }, [clearWrite, router]);
  
  const value: WriteContextType = {
    sessionId,
    writeContent,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    currentJournalId,
    conversationRefreshTrigger,
    updateWriteContent: updateWriteContentAction,
    askAIForInput: askAIForInputAction,
    loadSession,
    clearWrite,
    handleNewWrite,
    setError,
    refreshConversations,
  };
  
  return <WriteContext.Provider value={value}>{children}</WriteContext.Provider>;
}

export function useWrite() {
  const context = useContext(WriteContext);
  
  if (context === undefined) {
    throw new Error('useWrite must be used within a WriteProvider');
  }
  
  return context;
}
