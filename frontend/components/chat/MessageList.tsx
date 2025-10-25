'use client';

/**
 * MessageList component for displaying scrollable list of messages.
 */

import React, { useEffect, useRef } from 'react';
import { Message as MessageComponent } from './Message';
import { StreamingMessage } from './StreamingMessage';
import { Message as MessageType } from '@/lib/types/chat';
import { ScrollArea } from '@/components/ui/scroll-area';

interface MessageListProps {
  messages: MessageType[];
  isLoading?: boolean;
  isStreaming?: boolean;
  streamingContent?: string;
}

export const MessageList = React.memo(function MessageList({
  messages,
  isLoading = false,
  isStreaming = false,
  streamingContent = '',
}: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevMessagesLengthRef = useRef(messages.length);
  
  // Auto-scroll to bottom when new messages arrive or streaming content updates
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, streamingContent]);

  if (messages.length === 0 && !isLoading && !isStreaming) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-claude-text-muted">
          <p className="text-2xl mb-2 font-medium">Start a conversation</p>
          <p className="text-xl">
            Type a message below to begin journaling with AI
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 px-6">
      <div className="max-w-4xl mx-auto py-6">
        {messages.map((message) => (
          <MessageComponent
            key={message.id}
            message={message}
            showTimestamp={false}
          />
        ))}
        
        {/* Streaming message */}
        {isStreaming && streamingContent && (
          <StreamingMessage
            content={streamingContent}
            isStreaming={true}
          />
        )}
        
        {/* Loading indicator (non-streaming) */}
        {isLoading && !isStreaming && (
          <div className="flex w-full mb-6 justify-start">
            <div className="max-w-[80%] rounded-2xl px-4 py-3 claude-message-assistant">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-claude-text-muted rounded-full animate-pulse" />
                <div className="w-2 h-2 bg-claude-text-muted rounded-full animate-pulse delay-75" />
                <div className="w-2 h-2 bg-claude-text-muted rounded-full animate-pulse delay-150" />
                <span className="text-lg text-claude-text-muted ml-2">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Scroll anchor */}
        <div ref={scrollRef} />
      </div>
    </ScrollArea>
  );
});

