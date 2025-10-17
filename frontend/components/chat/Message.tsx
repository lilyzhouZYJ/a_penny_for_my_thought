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
        'flex w-full mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[85%] sm:max-w-[80%] rounded-lg px-3 py-2 sm:px-4 sm:py-3',
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
        )}
      >
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-sm font-semibold">
            {isUser ? 'You' : 'AI'}
          </span>
          {showTimestamp && (
            <span className="text-xs opacity-70">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
        
        <div
          className={cn(
            'prose prose-sm max-w-none',
            isUser
              ? 'prose-invert'
              : 'prose-gray dark:prose-invert'
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

