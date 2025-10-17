'use client';

/**
 * ChatInterface component - Main chat interaction area.
 */

import React, { useCallback } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { useChat } from '@/lib/context/ChatContext';
import { cn } from '@/lib/utils';
import { parseApiError, isRecoverableError } from '@/lib/utils/error-handlers';

interface ChatInterfaceProps {
  className?: string;
}

export const ChatInterface = React.memo(function ChatInterface({
  className,
}: ChatInterfaceProps) {
  const { messages, isLoading, isStreaming, streamingContent, error, sendMessage, setError } = useChat();
  const [lastMessage, setLastMessage] = React.useState<string>('');

  const handleSend = useCallback(
    async (message: string) => {
      try {
        setLastMessage(message);
        await sendMessage(message, true); // Enable streaming by default
      } catch (err) {
        console.error('Failed to send message:', err);
      }
    },
    [sendMessage]
  );

  const handleRetry = useCallback(() => {
    if (lastMessage) {
      handleSend(lastMessage);
    }
  }, [lastMessage, handleSend]);

  const handleDismissError = useCallback(() => {
    setError(null);
  }, [setError]);

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Error banner */}
      {error && (
        <div className="px-4 pt-4">
          <ErrorMessage
            message={parseApiError(error)}
            onRetry={isRecoverableError(error) ? handleRetry : undefined}
            onDismiss={handleDismissError}
          />
        </div>
      )}

      {/* Messages */}
      <MessageList 
        messages={messages} 
        isLoading={isLoading} 
        isStreaming={isStreaming}
        streamingContent={streamingContent}
      />

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={isLoading || isStreaming}
        placeholder={
          isStreaming
            ? 'AI is responding...'
            : isLoading
            ? 'Waiting for response...'
            : 'Type your message... (Enter to send, Shift+Enter for new line)'
        }
      />
    </div>
  );
});

