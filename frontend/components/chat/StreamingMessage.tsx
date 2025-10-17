'use client';

/**
 * StreamingMessage component for displaying messages being generated in real-time.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { cn } from '@/lib/utils';

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
}

export const StreamingMessage = React.memo(function StreamingMessage({
  content,
  isStreaming,
}: StreamingMessageProps) {
  return (
    <div className="flex w-full mb-4 justify-start">
      <div className="max-w-[80%] rounded-lg px-4 py-3 bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100">
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-sm font-semibold">AI</span>
          {isStreaming && (
            <span className="text-xs opacity-70 flex items-center gap-1">
              <span className="inline-block w-1 h-1 bg-current rounded-full animate-pulse" />
              <span className="inline-block w-1 h-1 bg-current rounded-full animate-pulse delay-75" />
              <span className="inline-block w-1 h-1 bg-current rounded-full animate-pulse delay-150" />
            </span>
          )}
        </div>
        
        <div className="prose prose-sm max-w-none prose-gray dark:prose-invert">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
});

