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
    <div className="flex w-full mb-6 justify-start">
      <div className="max-w-[85%] sm:max-w-[80%] rounded-2xl px-4 py-3 claude-message-assistant">
        <div className="prose prose-base max-w-none prose-gray dark:prose-invert">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
});

