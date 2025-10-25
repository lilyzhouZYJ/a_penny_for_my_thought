'use client';

/**
 * Write Context for global write mode state management.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Message } from '@/lib/types/chat';
import { JournalMetadata } from '@/lib/types/journal';
import { updateWriteContent, askAIForInput, getJournal } from '@/lib/api/journals';
import { config } from '@/lib/config';

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
  journalRefreshTrigger: number;
  
  // Actions
  updateWriteContent: (content: string) => Promise<void>;
  askAIForInput: (content: string) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  clearWrite: () => string;
  handleNewWrite: () => void;
  
  // Utility
  setError: (error: string | null) => void;
  refreshJournals: () => void;
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
  const [journalRefreshTrigger, setJournalRefreshTrigger] = useState(0);
  
  // Debounce timer ref
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Immediate update function (for internal use)
  const updateWriteContentImmediate = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);
    
    console.log('Saving content:', JSON.stringify(content)); // Debug log
    
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
        setJournalRefreshTrigger(prev => prev + 1);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update write content';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, currentJournalId]);

  // Debounced update function (for user typing)
  const updateWriteContentAction = useCallback(async (content: string) => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Return a promise that resolves when the debounce timer is set
    return new Promise<void>((resolve) => {
      debounceTimerRef.current = setTimeout(() => {
        updateWriteContentImmediate(content).finally(() => resolve());
      }, 1000); // 1 second debounce
    });
  }, [updateWriteContentImmediate]);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);
  
  const askAIForInputAction = useCallback(async (content: string) => {
    setIsLoading(true);
    setIsStreaming(true);
    setError(null);
    setStreamingContent('');
    
    try {
      // Use streaming API
      const response = await fetch(`${config.apiUrl}/api/v1/journals/ask-ai/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          journal_id: currentJournalId,
          content: content,
          conversation_history: messages,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let fullResponse = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'token') {
                  fullResponse += data.data.token;
                  setStreamingContent(fullResponse);
                } else if (data.type === 'done') {
                  // Create AI message
                  const aiMessage: Message = {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: fullResponse,
                    timestamp: new Date().toISOString()
                  };
                  
                  // Update conversation history
                  const updatedMessages = [...messages, aiMessage];
                  setMessages(updatedMessages);
                  
                  // Append AI response to the write content as italicized text
                  const aiResponse = `*${fullResponse}*`;
                  const updatedContent = content.trim() 
                    ? `${content}\n\n${aiResponse}`
                    : aiResponse;
                  
                  setWriteContent(updatedContent);
                  
                  // Auto-save the updated content (use immediate save for AI responses)
                  try {
                    await updateWriteContentImmediate(updatedContent);
                  } catch (saveErr) {
                    console.error('Failed to auto-save AI response:', saveErr);
                  }
                } else if (data.type === 'error') {
                  throw new Error(data.data.message);
                }
              } catch (parseErr) {
                console.error('Failed to parse SSE data:', parseErr);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get AI input';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingContent('');
    }
  }, [sessionId, messages, currentJournalId, updateWriteContentAction]);
  
  const loadSession = useCallback(async (sessionIdToLoad: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load journal from database
      const journal = await getJournal(sessionIdToLoad);
      
      // Extract write content from the most recent user message (if any)
      const userMessages = journal.messages.filter(msg => msg.role === 'user');
      const mostRecentUserMessage = userMessages[userMessages.length - 1];
      const writeContent = mostRecentUserMessage?.content || '';
      
      console.log('Loaded journal:', {
        totalMessages: journal.messages.length,
        userMessages: userMessages.length,
        writeContent: JSON.stringify(writeContent)
      });
      
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
  
  const refreshJournals = useCallback(() => {
    // Trigger journal list refresh by incrementing the trigger
    setJournalRefreshTrigger(prev => prev + 1);
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
    journalRefreshTrigger,
    updateWriteContent: updateWriteContentAction,
    askAIForInput: askAIForInputAction,
    loadSession,
    clearWrite,
    handleNewWrite,
    setError,
    refreshJournals,
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
