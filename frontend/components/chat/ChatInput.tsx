'use client';

/**
 * ChatInput component for user message input.
 */

import React, { useState, useCallback, KeyboardEvent } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export const ChatInput = React.memo(function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Type your message...',
  className,
}: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSend = useCallback(() => {
    const trimmedInput = input.trim();
    if (trimmedInput && !disabled) {
      onSend(trimmedInput);
      setInput('');
    }
  }, [input, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Send on Enter (without Shift)
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className={cn('flex gap-3 p-6 bg-claude-bg', className)}>
      <div className="max-w-4xl mx-auto w-full flex gap-3">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="min-h-[60px] max-h-[200px] resize-none text-xl claude-input flex-1" // text-xl prevents zoom on iOS
          rows={1}
        />
        <Button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          size="icon"
          className="h-[60px] w-[60px] shrink-0 min-w-[44px] min-h-[44px] !bg-claude-accent hover:!bg-claude-accent/90" // Touch-friendly minimum
          aria-label="Send message"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
});

