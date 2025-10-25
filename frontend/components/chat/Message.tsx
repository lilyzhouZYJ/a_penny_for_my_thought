'use client';

/**
 * Message component for displaying chat messages.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message as MessageType } from '@/lib/types/chat';
import { cn } from '@/lib/utils';

interface MessageProps {
  message: MessageType;
  showTimestamp?: boolean;
}

export const Message = React.memo(function Message({
  message,
  showTimestamp = false,
}: MessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  // Don't render system messages in UI
  if (message.role === 'system') {
    return null;
  }

  return (
    <div
      className={cn(
        'w-full mb-6',
        isUser ? 'flex justify-start' : 'flex justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[85%] sm:max-w-[80%]',
          isUser
            ? 'text-claude-text prose prose-lg max-w-none border-l-2 border-claude-light-accent pl-4' // User messages with subtle left border
            : 'claude-message-assistant' // AI messages in chat bubbles
        )}
      >
        <div
          className={cn(
            isUser
              ? 'prose-gray dark:prose-invert'
              : 'prose prose-lg max-w-none prose-gray dark:prose-invert'
          )}
        >
          <ReactMarkdown
            components={{
              code(props) {
                const { node, className, children, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';
                const inline = !className;
                
                return !inline && language ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus as any}
                    language={language}
                    PreTag="div"
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...rest}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
});

