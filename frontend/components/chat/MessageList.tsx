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
        <div className="text-center text-muted-foreground">
          <p className="text-lg mb-2">Start a conversation</p>
          <p className="text-sm">
            Type a message below to begin journaling with AI
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 px-4">
      <div className="max-w-4xl mx-auto py-4">
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
          <div className="flex w-full mb-4 justify-start">
            <div className="max-w-[80%] rounded-lg px-4 py-3 bg-gray-100 dark:bg-gray-800">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-75" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-150" />
                <span className="text-sm text-gray-500 ml-2">AI is thinking...</span>
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

