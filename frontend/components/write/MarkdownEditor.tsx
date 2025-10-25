'use client';

/**
 * MarkdownEditor component - A Notion-like editor with section-based editing.
 */

import React, { useCallback, useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MarkdownEditorProps {
  content: string;
  onContentChange: (content: string) => void;
  onAskAI: (content: string, cursorPosition: number) => void;
  isLoading?: boolean;
  isStreaming?: boolean;
  streamingContent?: string;
  className?: string;
}

export const MarkdownEditor = React.memo(function MarkdownEditor({
  content,
  onContentChange,
  onAskAI,
  isLoading = false,
  isStreaming = false,
  streamingContent = '',
  className,
}: MarkdownEditorProps) {
  const [showAskAIButton, setShowAskAIButton] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);
  const askAIButtonRef = useRef<HTMLButtonElement>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [lastContent, setLastContent] = useState(content);

  // Handle input changes
  const handleInput = useCallback((e: React.FormEvent<HTMLDivElement>) => {
    // Get content with proper line break handling
    const htmlContent = e.currentTarget.innerHTML || '';
    
    // Convert HTML line breaks to text line breaks
    let textContent = htmlContent
      .replace(/<br\s*\/?>/gi, '\n')  // Convert <br> to \n
      .replace(/<div>/gi, '\n')       // Convert <div> to \n
      .replace(/<\/div>/gi, '')       // Remove closing </div>
      .replace(/<p>/gi, '\n')        // Convert <p> to \n
      .replace(/<\/p>/gi, '')        // Remove closing </p>
      .replace(/<[^>]*>/g, '');      // Remove any remaining HTML tags
    
    // Clean up multiple consecutive newlines
    textContent = textContent.replace(/\n{3,}/g, '\n\n');
    
    console.log('Saving content:', JSON.stringify(textContent)); // Debug log
    setLastContent(textContent);
    onContentChange(textContent);
  }, [onContentChange]);

  // Handle focus to track editing state and show Ask AI button
  const handleFocus = useCallback(() => {
    setIsEditing(true);
    setShowAskAIButton(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
    // Don't hide the button immediately on blur, let the click handler manage it
  }, []);

  // Set initial content on mount and handle updates
  useEffect(() => {
    if (editorRef.current) {
      // Only update if content is different and we're not actively editing
      if (!isEditing && content !== lastContent) {
        const htmlContent = content.replace(/\n/g, '<br>');
        editorRef.current.innerHTML = htmlContent;
        setLastContent(content);
      } else if (!editorRef.current.innerHTML && content) {
        // Set initial content
        console.log('Loading content:', JSON.stringify(content)); // Debug log
        const htmlContent = content.replace(/\n/g, '<br>');
        editorRef.current.innerHTML = htmlContent;
        setLastContent(content);
      }
    }
  }, [content, isEditing, lastContent]);

  // Handle document clicks to hide Ask AI button when clicking outside
  useEffect(() => {
    const handleDocumentClick = (event: MouseEvent) => {
      if (editorRef.current && !editorRef.current.contains(event.target as Node) && 
          askAIButtonRef.current && !askAIButtonRef.current.contains(event.target as Node)) {
        setShowAskAIButton(false);
      }
    };

    document.addEventListener('click', handleDocumentClick);
    return () => document.removeEventListener('click', handleDocumentClick);
  }, []);

  // Handle cursor position for Ask AI button
  const handleCursorMove = useCallback((event: React.MouseEvent | React.KeyboardEvent) => {
    // No longer needed since button is fixed to the right
  }, []);

  // Hide Ask AI button when clicking elsewhere
  const handleEditorClick = useCallback((event: React.MouseEvent) => {
    if (askAIButtonRef.current && askAIButtonRef.current.contains(event.target as Node)) {
      return; // Don't hide if clicking the button itself
    }
    // Don't hide the button on editor click, only hide when clicking outside
  }, []);

  // Handle streaming content
  useEffect(() => {
    if (isStreaming && streamingContent && editorRef.current) {
      // Update the editor content with streaming content
      const currentContent = editorRef.current.textContent || '';
      const aiResponse = `*${streamingContent}*`;
      const updatedContent = currentContent.trim() 
        ? `${currentContent}\n\n${aiResponse}`
        : aiResponse;
      
      // Save cursor position
      const selection = window.getSelection();
      const range = selection?.getRangeAt(0);
      const cursorOffset = range?.startOffset || 0;
      
      // Update content with proper line break handling
      const htmlContent = updatedContent.replace(/\n/g, '<br>');
      editorRef.current.innerHTML = htmlContent;
      
      // Restore cursor position
      if (range && selection) {
        try {
          range.setStart(editorRef.current.firstChild || editorRef.current, cursorOffset);
          range.collapse(true);
          selection.removeAllRanges();
          selection.addRange(range);
        } catch (e) {
          // If cursor restoration fails, place at end
          const newRange = document.createRange();
          newRange.selectNodeContents(editorRef.current);
          newRange.collapse(false);
          selection.removeAllRanges();
          selection.addRange(newRange);
        }
      }
    }
  }, [isStreaming, streamingContent]);

  // Handle Ask AI button click
  const handleAskAIClick = useCallback(() => {
    onAskAI(content, 0);
    setShowAskAIButton(false);
  }, [content, onAskAI]);

  // Handle scroll events (simplified - no timeout needed)
  const handleScroll = useCallback(() => {
    // Just ensure scrollbar stays visible while scrolling
    // No timeout needed since hover state handles visibility
  }, []);

  // Handle mouse enter/leave for hover scrollbar
  const handleMouseEnter = useCallback(() => {
    setIsHovering(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovering(false);
  }, []);

  // Handle mouse wheel events for scrolling
  const handleWheel = useCallback((e: React.WheelEvent) => {
    // Allow scrolling even when not focused
    e.preventDefault();
    const container = e.currentTarget;
    container.scrollTop += e.deltaY;
  }, []);

  return (
    <div className={cn('relative h-full', className)}>
      {/* Text Editor Area - Fixed width, scrollable */}
      <div 
        className={cn(
          "max-w-4xl mx-auto overflow-y-auto transition-all duration-300",
          isHovering ? "scrollbar-visible" : "scrollbar-hidden"
        )}
        style={{ height: 'calc(100vh - 120px)' }}
        onScroll={handleScroll}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onWheel={handleWheel}
        tabIndex={-1}
      >
        <div
          ref={editorRef}
          className="w-full p-6 text-lg leading-relaxed focus:outline-none bg-transparent border-none"
          contentEditable
          suppressContentEditableWarning
          onInput={handleInput}
          onClick={handleEditorClick}
          onMouseUp={handleCursorMove}
          onKeyUp={handleCursorMove}
          onFocus={handleFocus}
          onBlur={handleBlur}
          style={{ 
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            backgroundColor: 'transparent',
            border: 'none',
            outline: 'none',
            boxShadow: 'none'
          }}
        >
        </div>
      </div>

      {/* Ask AI Button - Fixed positioned, stays visible during scroll */}
      {showAskAIButton && (
        <div className="fixed top-6 right-6 z-50">
          <Button
            ref={askAIButtonRef}
            size="sm"
            variant="outline"
            className="shadow-lg bg-background/95 backdrop-blur-sm"
            onClick={handleAskAIClick}
            disabled={isLoading}
          >
            <MessageCircle className="h-4 w-4 mr-1" />
            Ask AI
          </Button>
        </div>
      )}
    </div>
  );
});
