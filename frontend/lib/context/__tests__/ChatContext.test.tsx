/**
 * Unit tests for ChatContext.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { ChatProvider, useChat } from '../ChatContext';
import * as chatApi from '@/lib/api/chat';
import * as journalsApi from '@/lib/api/journals';
import { Message } from '@/lib/types/chat';

// Mock the API modules
jest.mock('@/lib/api/chat');
jest.mock('@/lib/api/journals');

const mockSendChatMessage = chatApi.sendChatMessage as jest.MockedFunction<typeof chatApi.sendChatMessage>;
const mockStreamChatMessage = chatApi.streamChatMessage as jest.MockedFunction<typeof chatApi.streamChatMessage>;
const mockLoadChatHistory = chatApi.loadChatHistory as jest.MockedFunction<typeof chatApi.loadChatHistory>;
const mockGetJournal = journalsApi.getJournal as jest.MockedFunction<typeof journalsApi.getJournal>;

describe('ChatContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock streamChatMessage to return a simple async generator
    mockStreamChatMessage.mockImplementation(async function* () {
      yield { type: 'token', data: { content: 'AI ' } };
      yield { type: 'token', data: { content: 'response' } };
      yield { type: 'done', data: { metadata: { auto_saved: true } } };
    });
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <ChatProvider>{children}</ChatProvider>
  );

  describe('Initialization', () => {
    it('should initialize with empty messages', () => {
      const { result } = renderHook(() => useChat(), { wrapper });

      expect(result.current.messages).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.sessionId).toBeTruthy();
      expect(result.current.currentJournalId).toBeNull();
    });

    it('should generate a session ID on initialization', () => {
      const { result } = renderHook(() => useChat(), { wrapper });

      expect(result.current.sessionId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    });
  });

  describe('sendMessage', () => {
    it('should send message and update state', async () => {
      const mockResponse = {
        message: {
          id: 'ai-msg-1',
          role: 'assistant' as const,
          content: 'AI response',
          timestamp: new Date().toISOString(),
        },
        retrieved_context: [],
        metadata: {},
        auto_saved: true,
      };

      mockSendChatMessage.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat(), { wrapper });

      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      // Should have 2 messages (user + AI)
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('Hello');
      expect(result.current.messages[1].role).toBe('assistant');
      expect(result.current.messages[1].content).toBe('AI response');
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should include conversation history in API call', async () => {
      const mockResponse = {
        message: {
          id: 'ai-msg-1',
          role: 'assistant' as const,
          content: 'Response',
          timestamp: new Date().toISOString(),
        },
        retrieved_context: [],
        metadata: {},
        auto_saved: true,
      };

      mockSendChatMessage.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat(), { wrapper });

      // Send first message (non-streaming)
      await act(async () => {
        await result.current.sendMessage('First message', false);
      });

      // Send second message (non-streaming)
      await act(async () => {
        await result.current.sendMessage('Second message', false);
      });

      // Check that second call included conversation history
      const secondCall = mockSendChatMessage.mock.calls[1];
      // conversation_history should have 3 messages: 
      // [user1, ai1, user2] - includes current user message
      expect(secondCall[2]).toHaveLength(3);
    });

    it('should handle API errors gracefully', async () => {
      // Mock both streaming and non-streaming to fail
      mockStreamChatMessage.mockImplementation(async function* () {
        throw new Error('API Error');
      });
      mockSendChatMessage.mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useChat(), { wrapper });

      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      // Should set error
      expect(result.current.error).toBe('API Error');
      // Should not add messages on error
      expect(result.current.messages).toHaveLength(0);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('loadSession', () => {
    it('should load journal and update state', async () => {
      const mockMessages = [
        {
          id: 'msg-1',
          role: 'user' as const,
          content: 'Hello',
          timestamp: new Date().toISOString(),
        },
        {
          id: 'msg-2',
          role: 'assistant' as const,
          content: 'Hi there!',
          timestamp: new Date().toISOString(),
        },
      ];

      mockLoadChatHistory.mockResolvedValue(mockMessages);

      const { result } = renderHook(() => useChat(), { wrapper });

      await act(async () => {
        await result.current.loadSession('test-session-id');
      });

      // Should load messages
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].content).toBe('Hello');
      expect(result.current.messages[1].content).toBe('Hi there!');
      expect(result.current.currentJournalId).toBe('test-session-id');
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle load errors', async () => {
      mockLoadChatHistory.mockRejectedValue(new Error('Journal not found'));

      const { result } = renderHook(() => useChat(), { wrapper });

      await act(async () => {
        await result.current.loadSession('nonexistent-session');
      });

      expect(result.current.error).toBe('Journal not found');
      expect(result.current.messages).toHaveLength(0);
    });
  });

  describe('clearChat', () => {
    it('should reset conversation state', async () => {
      mockSendChatMessage.mockResolvedValue({
        message: {
          id: 'ai-1',
          role: 'assistant' as const,
          content: 'Response',
          timestamp: new Date().toISOString(),
        },
        retrieved_context: [],
        metadata: {},
        auto_saved: true,
      });

      const { result } = renderHook(() => useChat(), { wrapper });

      // Add some messages
      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      const oldSessionId = result.current.sessionId;
      expect(result.current.messages).toHaveLength(2);

      // Clear chat
      let newSessionId: string;
      act(() => {
        newSessionId = result.current.clearChat();
      });

      // Should reset everything and return new session ID
      expect(result.current.messages).toHaveLength(0);
      expect(result.current.sessionId).not.toBe(oldSessionId);
      expect(result.current.sessionId).toBe(newSessionId!);
      expect(result.current.currentJournalId).toBeNull();
      expect(result.current.error).toBeNull();
    });
  });

  describe('useChat hook', () => {
    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const originalError = console.error;
      console.error = jest.fn();

      expect(() => {
        renderHook(() => useChat());
      }).toThrow('useChat must be used within a ChatProvider');

      console.error = originalError;
    });
  });
});

