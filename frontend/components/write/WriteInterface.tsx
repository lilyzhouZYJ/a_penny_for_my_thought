'use client';

/**
 * WriteInterface component - Main write mode interface for journaling.
 */

import React, { useCallback, useState, useRef, useEffect } from 'react';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { Button } from '@/components/ui/button';
import { MarkdownEditor } from './MarkdownEditor';
import { useWrite } from '@/lib/context/WriteContext';
import { cn } from '@/lib/utils';
import { parseApiError, isRecoverableError } from '@/lib/utils/error-handlers';
import { Save } from 'lucide-react';

interface WriteInterfaceProps {
  className?: string;
}

export const WriteInterface = React.memo(function WriteInterface({
  className,
}: WriteInterfaceProps) {
  const { 
    writeContent, 
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

  const handleAskAI = useCallback(async (content: string, cursorPosition: number) => {
    if (!content.trim()) return;
    
    try {
      await askAIForInput(content);
    } catch (err) {
      console.error('Failed to ask AI:', err);
    }
  }, [askAIForInput]);

  const handleDismissError = useCallback(() => {
    setError(null);
  }, [setError]);

  const handleRetry = useCallback(() => {
    if (localContent.trim()) {
      handleAskAI(localContent, 0);
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
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold text-claude-text">Your Journal</h2>
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
          </div>
        </div>
        
        {/* Markdown Editor */}
        <div className="flex-1">
          <MarkdownEditor
            content={localContent}
            onContentChange={handleContentChange}
            onAskAI={handleAskAI}
            isLoading={isLoading}
            isStreaming={isStreaming}
            streamingContent={streamingContent}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
});
