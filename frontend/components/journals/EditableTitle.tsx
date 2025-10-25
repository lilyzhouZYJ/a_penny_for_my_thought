'use client';

/**
 * EditableTitle component for inline title editing.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Edit2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface EditableTitleProps {
  title: string;
  onUpdate: (newTitle: string) => Promise<void>;
  className?: string;
  maxLength?: number;
}

export const EditableTitle = React.memo(function EditableTitle({
  title,
  onUpdate,
  className,
  maxLength = 100,
}: EditableTitleProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(title);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when editing starts
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleStartEdit = useCallback(() => {
    setEditValue(title);
    setIsEditing(true);
  }, [title]);

  const handleSave = useCallback(async () => {
    const trimmedValue = editValue.trim();
    
    if (trimmedValue === title || trimmedValue.length === 0) {
      setIsEditing(false);
      return;
    }

    setIsLoading(true);
    try {
      await onUpdate(trimmedValue);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update title:', error);
      // Keep editing mode open on error
    } finally {
      setIsLoading(false);
    }
  }, [editValue, title, onUpdate]);

  const handleBlur = useCallback(() => {
    // Auto-save when user clicks away
    handleSave();
  }, [handleSave]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setEditValue(title);
      setIsEditing(false);
    }
  }, [handleSave, title]);

  if (isEditing) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <input
          ref={inputRef}
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          maxLength={maxLength}
          disabled={isLoading}
          className="flex-1 px-2 py-1 text-sm border border-claude-border rounded bg-claude-bg text-claude-text focus:outline-none focus:ring-2 focus:ring-claude-accent"
        />
        {isLoading && (
          <div className="h-4 w-4 border-2 border-claude-accent border-t-transparent rounded-full animate-spin" />
        )}
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-2 group', className)}>
      <span className="flex-1 text-sm font-medium text-claude-text truncate">
        {title}
      </span>
      <Button
        size="sm"
        variant="ghost"
        onClick={handleStartEdit}
        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <Edit2 className="h-4 w-4" />
      </Button>
    </div>
  );
});
