'use client';

/**
 * Chat Context for global chat state management.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Message } from '@/lib/types/chat';
import { JournalMetadata } from '@/lib/types/journal';
import { sendChatMessage, streamChatMessage } from '@/lib/api/chat';
import { getJournal, saveJournal as saveJournalApi } from '@/lib/api/journals';

interface ChatContextType {
  // State
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;
  currentJournalId: string | null;
  
  // Actions
  sendMessage: (content: string, useStreaming?: boolean) => Promise<void>;
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
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [currentJournalId, setCurrentJournalId] = useState<string | null>(null);
  
  const sendMessage = useCallback(async (content: string, useStreaming: boolean = true) => {
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
      
      // Try streaming first, fallback to non-streaming on error
      if (useStreaming) {
        try {
          await handleStreamingMessage(content, userMessage);
        } catch (streamError) {
          console.warn('Streaming failed, falling back to non-streaming:', streamError);
          await handleNonStreamingMessage(content, userMessage);
        }
      } else {
        await handleNonStreamingMessage(content, userMessage);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      console.error('Send message error:', err);
      
      // Remove the user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingContent('');
    }
  }, [messages, sessionId]);

  const handleStreamingMessage = useCallback(async (content: string, userMessage: Message) => {
    setIsStreaming(true);
    setStreamingContent('');
    
    let fullContent = '';
    
    for await (const event of streamChatMessage(
      content,
      sessionId,
      [...messages, userMessage],
      true
    )) {
      if (event.type === 'token') {
        fullContent += event.data.content;
        setStreamingContent(fullContent);
      } else if (event.type === 'done') {
        // Create final AI message
        const aiMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: fullContent,
          timestamp: new Date().toISOString(),
        };
        
        setMessages(prev => [...prev, aiMessage]);
        setIsStreaming(false);
        setStreamingContent('');
      } else if (event.type === 'error') {
        throw new Error(event.data.message || 'Streaming error');
      }
    }
  }, [messages, sessionId]);

  const handleNonStreamingMessage = useCallback(async (content: string, userMessage: Message) => {
    const response = await sendChatMessage(
      content,
      sessionId,
      [...messages, userMessage],
      true
    );
    
    setMessages(prev => [...prev, response.message]);
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
    isStreaming,
    streamingContent,
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

