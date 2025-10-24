'use client';

/**
 * WriteInterface component - Main write mode interface for journaling.
 */

import React, { useCallback, useState, useRef, useEffect } from 'react';
import { MessageList } from '@/components/chat/MessageList';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useWrite } from '@/lib/context/WriteContext';
import { cn } from '@/lib/utils';
import { parseApiError, isRecoverableError } from '@/lib/utils/error-handlers';
import { MessageCircle, Save } from 'lucide-react';

interface WriteInterfaceProps {
  className?: string;
}

export const WriteInterface = React.memo(function WriteInterface({
  className,
}: WriteInterfaceProps) {
  const { 
    writeContent, 
    messages, 
    isLoading, 
    isStreaming, 
    streamingContent, 
    error, 
    updateWriteContent, 
    askAIForInput,
    setError 
  } = useWrite();
  
  const [localContent, setLocalContent] = useState(writeContent);
  const [isSaving, setIsSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout>();

  // Update local content when writeContent changes
  useEffect(() => {
    setLocalContent(writeContent);
  }, [writeContent]);

  // Auto-save functionality
  const handleContentChange = useCallback((content: string) => {
    setLocalContent(content);
    
    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    // Set new timeout for auto-save
    saveTimeoutRef.current = setTimeout(async () => {
      if (content.trim() && content !== writeContent) {
        try {
          await updateWriteContent(content);
        } catch (err) {
          console.error('Auto-save failed:', err);
        }
      }
    }, 2000); // Auto-save after 2 seconds of inactivity
  }, [writeContent, updateWriteContent]);

  const handleManualSave = useCallback(async () => {
    if (!localContent.trim()) return;
    
    setIsSaving(true);
    try {
      await updateWriteContent(localContent);
    } catch (err) {
      console.error('Manual save failed:', err);
    } finally {
      setIsSaving(false);
    }
  }, [localContent, updateWriteContent]);

  const handleAskAI = useCallback(async () => {
    if (!localContent.trim()) return;
    
    try {
      await askAIForInput(localContent);
    } catch (err) {
      console.error('Failed to ask AI:', err);
    }
  }, [localContent, askAIForInput]);

  const handleDismissError = useCallback(() => {
    setError(null);
  }, [setError]);

  const handleRetry = useCallback(() => {
    if (localContent.trim()) {
      handleAskAI();
    }
  }, [localContent, handleAskAI]);

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

      {/* Write area */}
      <div className="flex-1 flex flex-col p-4">
        <div className="flex-1 flex flex-col space-y-4">
          {/* Write content textarea */}
          <div className="flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold text-claude-text">Your Journal</h2>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={handleManualSave}
                  disabled={isSaving || !localContent.trim()}
                  variant="outline"
                  size="sm"
                >
                  <Save className="h-4 w-4 mr-1" />
                  {isSaving ? 'Saving...' : 'Save'}
                </Button>
                <Button
                  onClick={handleAskAI}
                  disabled={isLoading || !localContent.trim()}
                  variant="default"
                  size="sm"
                >
                  <MessageCircle className="h-4 w-4 mr-1" />
                  Ask AI
                </Button>
              </div>
            </div>
            
            <Textarea
              ref={textareaRef}
              value={localContent}
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder="Write your thoughts here... (Auto-saves as you type)"
              className="flex-1 resize-none text-base leading-relaxed"
              disabled={isLoading}
            />
          </div>

          {/* AI Messages */}
          {messages.length > 0 && (
            <div className="flex-shrink-0">
              <div className="border-t border-claude-border pt-4">
                <h3 className="text-sm font-medium text-claude-text-muted mb-3">AI Responses</h3>
                <MessageList 
                  messages={messages} 
                  isLoading={isLoading} 
                  isStreaming={isStreaming}
                  streamingContent={streamingContent}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
