'use client';

/**
 * Chat Context for global chat state management.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { Message } from '@/lib/types/chat';
import { JournalMetadata } from '@/lib/types/journal';
import { sendChatMessage, streamChatMessage } from '@/lib/api/chat';
import { getJournal } from '@/lib/api/journals';

interface ChatContextType {
  // State
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;
  currentJournalId: string | null;
  journalRefreshTrigger: number;
  
  // Actions
  sendMessage: (content: string, useStreaming?: boolean) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  clearChat: () => string;
  handleNewJournal: () => void;
  
  // Utility
  setError: (error: string | null) => void;
  refreshJournals: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [currentJournalId, setCurrentJournalId] = useState<string | null>(null);
  const [journalRefreshTrigger, setJournalRefreshTrigger] = useState(0);
  
  const sendMessage = useCallback(async (content: string, useStreaming: boolean = true) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Check if this is the first message before adding it
      const wasFirstMessage = messages.length === 0;
      
      // Create user message
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      
      // Add user message to state so that it displays in the chat interface
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      
      // Try streaming first, fallback to non-streaming on error
      if (useStreaming) {
        try {
          await handleStreamingMessage(content, updatedMessages);
        } catch (streamError) {
          await handleNonStreamingMessage(content, updatedMessages);
        }
      } else {
        await handleNonStreamingMessage(content, updatedMessages);
      }
      
      // If this was the first message in a new conversation, refresh the conversation list
      if (wasFirstMessage) {
        setJournalRefreshTrigger(prev => prev + 1);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Remove the user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingContent('');
    }
  }, [messages, sessionId]);

  const handleStreamingMessage = useCallback(async (content: string, conversationHistory: Message[]) => {
    setIsStreaming(true);
    setStreamingContent('');
    
    let fullContent = '';
    
    for await (const event of streamChatMessage(
      content,
      sessionId,
      conversationHistory,
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
        
        // Add the AI message to the conversation history
        setMessages(prev => [...prev, aiMessage]);
        setIsStreaming(false);
        setStreamingContent('');
      } else if (event.type === 'error') {
        throw new Error(event.data.message || 'Streaming error');
      }
    }
  }, [sessionId]);

  const handleNonStreamingMessage = useCallback(async (content: string, conversationHistory: Message[]) => {
    const response = await sendChatMessage(
      content,
      sessionId,
      conversationHistory,
      true
    );
    
    // Add the AI message to the conversation history
    setMessages(prev => [...prev, response.message]);
  }, [sessionId]);
  
  const loadSession = useCallback(async (journalIdToLoad: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load journal from database
      const journal = await getJournal(journalIdToLoad);
      
      // Set state from loaded journal
      setMessages(journal.messages);
      setSessionId(journalIdToLoad);
      setCurrentJournalId(journalIdToLoad);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load journal';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  const clearChat = useCallback(() => {
    const newSessionId = crypto.randomUUID();
    setMessages([]);
    setSessionId(newSessionId);
    setCurrentJournalId(null);
    setError(null);
    return newSessionId;
  }, []);
  
  const refreshJournals = useCallback(() => {
    // Trigger journal list refresh by incrementing the trigger
    setJournalRefreshTrigger(prev => prev + 1);
  }, []);
  
  const handleNewJournal = useCallback(() => {
    const newSessionId = clearChat();
    router.push(`/chat/${newSessionId}`);
  }, [clearChat, router]);
  
  const value: ChatContextType = {
    sessionId,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    error,
    currentJournalId,
    journalRefreshTrigger,
    sendMessage,
    loadSession,
    clearChat,
    handleNewJournal,
    setError,
    refreshJournals,
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

