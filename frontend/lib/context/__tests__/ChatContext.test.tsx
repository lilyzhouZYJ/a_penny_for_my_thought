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
const mockGetJournal = journalsApi.getJournal as jest.MockedFunction<typeof journalsApi.getJournal>;
const mockSaveJournal = journalsApi.saveJournal as jest.MockedFunction<typeof journalsApi.saveJournal>;

describe('ChatContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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

      // Send first message
      await act(async () => {
        await result.current.sendMessage('First message');
      });

      // Send second message
      await act(async () => {
        await result.current.sendMessage('Second message');
      });

      // Check that second call included conversation history
      const secondCall = mockSendChatMessage.mock.calls[1];
      // conversation_history should have 3 messages: 
      // [user1, ai1, user2] - includes current user message
      expect(secondCall[2]).toHaveLength(3);
    });

    it('should handle API errors gracefully', async () => {
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
      const mockJournal = {
        id: 'journal-1',
        filename: 'test.md',
        title: 'Test Journal',
        date: new Date().toISOString(),
        message_count: 2,
        duration_seconds: null,
        messages: [
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
        ],
        raw_content: '# Test',
      };

      mockGetJournal.mockResolvedValue(mockJournal);

      const { result } = renderHook(() => useChat(), { wrapper });

      await act(async () => {
        await result.current.loadSession('test.md');
      });

      // Should load messages
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].content).toBe('Hello');
      expect(result.current.messages[1].content).toBe('Hi there!');
      expect(result.current.currentJournalId).toBe('test.md');
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle load errors', async () => {
      mockGetJournal.mockRejectedValue(new Error('Journal not found'));

      const { result } = renderHook(() => useChat(), { wrapper });

      await act(async () => {
        await result.current.loadSession('nonexistent.md');
      });

      expect(result.current.error).toBe('Journal not found');
      expect(result.current.messages).toHaveLength(0);
    });
  });

  describe('saveSession', () => {
    it('should save conversation', async () => {
      const mockMetadata = {
        id: 'journal-1',
        filename: 'test.md',
        title: 'Test',
        date: new Date().toISOString(),
        message_count: 2,
        duration_seconds: null,
      };

      mockSaveJournal.mockResolvedValue(mockMetadata);
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

      // Add some messages first
      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      // Save session
      let savedMetadata;
      await act(async () => {
        savedMetadata = await result.current.saveSession();
      });

      expect(mockSaveJournal).toHaveBeenCalled();
      expect(savedMetadata).toEqual(mockMetadata);
      expect(result.current.currentJournalId).toBe('test.md');
    });

    it('should not save empty conversation', async () => {
      const { result } = renderHook(() => useChat(), { wrapper });

      let savedMetadata;
      await act(async () => {
        savedMetadata = await result.current.saveSession();
      });

      expect(mockSaveJournal).not.toHaveBeenCalled();
      expect(savedMetadata).toBeNull();
      expect(result.current.error).toBe('No messages to save');
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
      act(() => {
        result.current.clearChat();
      });

      // Should reset everything
      expect(result.current.messages).toHaveLength(0);
      expect(result.current.sessionId).not.toBe(oldSessionId);
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

