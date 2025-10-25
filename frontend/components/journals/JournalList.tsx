'use client';

/**
 * JournalList component for displaying past journals.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { EditableTitle } from '@/components/journals/EditableTitle';
import { JournalMetadata } from '@/lib/types/journal';
import { listJournals, deleteJournal } from '@/lib/api/chat';
import { updateJournalTitle } from '@/lib/api/journals';
import { cn } from '@/lib/utils';
import { FileText, Trash2, MessageSquare, PenTool, MoreHorizontal, Edit2 } from 'lucide-react';
import { parseApiError } from '@/lib/utils/error-handlers';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface JournalListProps {
  onSelect: (sessionId: string, mode: "chat" | "write") => void;
  currentSessionId?: string;
  className?: string;
  refreshTrigger?: number; // External trigger to refresh journals
  sidebarWidth?: number; // Width of the sidebar for responsive adjustments
}

export const JournalList = React.memo(function JournalList({
  onSelect,
  currentSessionId,
  className,
  refreshTrigger,
  sidebarWidth = 320,
}: JournalListProps) {
  const [journals, setJournals] = useState<JournalMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingJournalId, setEditingJournalId] = useState<string | null>(null);

  // Helper function to get the appropriate icon for the mode
  const getModeIcon = (mode: "chat" | "write") => {
    return mode === "chat" ? MessageSquare : PenTool;
  };

  const loadJournals = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await listJournals(50, 0);
      setJournals(response.journals);
    } catch (err) {
      console.error('Failed to load journals:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load journals';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleDeleteJournal = useCallback(async (journalId: string, journalTitle: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${journalTitle}"?\n\nThis action cannot be undone and will permanently remove all messages in this journal.`
    );
    
    if (!confirmed) return;
    
    try {
      await deleteJournal(journalId);
      console.log(`Deleted journal: ${journalTitle}`);
      
      // Refresh the journal list by reloading
      loadJournals();
    } catch (err) {
      console.error('Failed to delete journal:', err);
      setError('Failed to delete journal');
    }
  }, [loadJournals]);

  const handleUpdateTitle = useCallback(async (journalId: string, newTitle: string) => {
    try {
      await updateJournalTitle(journalId, newTitle);
      
      // Update the local state to reflect the change immediately
      setJournals(prev => 
        prev.map(journal => 
          journal.id === journalId 
            ? { ...journal, title: newTitle }
            : journal
        )
      );
      setEditingJournalId(null);
    } catch (err) {
      console.error('Failed to update journal title:', err);
      throw err; // Re-throw to let EditableTitle handle the error
    }
  }, []);

  const handleStartRename = useCallback((journalId: string) => {
    setEditingJournalId(journalId);
  }, []);

  const handleFinishEditing = useCallback(() => {
    setEditingJournalId(null);
  }, []);

  useEffect(() => {
    loadJournals();
  }, [loadJournals]);

  // Refresh when external trigger changes (e.g., new journal created)
  useEffect(() => {
    if (refreshTrigger !== undefined) {
      loadJournals();
    }
  }, [refreshTrigger, loadJournals]);

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center p-4', className)}>
        <LoadingSpinner size="sm" text="Loading journals..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('p-4', className)}>
        <ErrorMessage
          title="Failed to load journals"
          message={parseApiError(error)}
          onRetry={loadJournals}
        />
      </div>
    );
  }

  if (journals.length === 0) {
    return (
      <div className={cn('p-4 text-sm text-claude-text-muted text-center', className)}>
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No journals yet</p>
        <p className="text-[11px] mt-1">Start a new journal to begin</p>
      </div>
    );
  }

  return (
    <ScrollArea className={cn('h-full', className)}>
      <div className="space-y-1 p-3">
        {journals.map((journal) => (
          <div
            key={journal.id}
            className={cn(
              'w-full p-2 hover:bg-claude-hover transition-colors group cursor-pointer rounded-md',
              currentSessionId === journal.id && 'bg-claude-hover'
            )}
            onClick={() => onSelect(journal.id, journal.mode)}
            style={{ 
              minWidth: `${sidebarWidth - 24}px`, // Account for padding (12px * 2)
              maxWidth: `${sidebarWidth - 24}px`
            }}
          >
            <div className="flex items-start justify-between w-full">
              <div className="flex items-start gap-2 flex-1 min-w-0">
                {/* Mode Icon - positioned to align with center of title */}
                <div 
                  className="flex-shrink-0 mt-2"
                  title={journal.mode === "chat" ? "Chat journal" : "Write session"}
                >
                  {React.createElement(getModeIcon(journal.mode), {
                    className: "h-4 w-4 text-claude-text-muted"
                  })}
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  {editingJournalId === journal.id ? (
                    <EditableTitle
                      title={journal.title || 'Untitled Journal'}
                      onUpdate={(newTitle) => handleUpdateTitle(journal.id, newTitle)}
                      className="mb-0"
                      startEditing={true}
                      onFinishEditing={handleFinishEditing}
                    />
                  ) : (
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium text-claude-text truncate block">
                        {journal.title || 'Untitled Journal'}
                      </span>
                      <p className="text-[11px] text-claude-text-muted truncate -mt-0.5">
                        {new Date(journal.date).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
              
              {editingJournalId !== journal.id && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 text-claude-text-muted hover:text-claude-text flex-shrink-0 ml-2 focus:ring-0 focus:outline-none border-0"
                      onClick={(e) => e.stopPropagation()}
                      title="Journal options"
                    >
                      <MoreHorizontal className="h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-32">
                  <DropdownMenuItem 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartRename(journal.id);
                    }}
                    className="text-[17px] cursor-pointer py-0"
                  >
                    <Edit2 className="h-3 w-3 mr-2" />
                    Rename
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteJournal(journal.id, journal.title);
                    }}
                    className="text-[17px] cursor-pointer text-destructive focus:text-destructive py-0"
                  >
                    <Trash2 className="h-3 w-3 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
});
