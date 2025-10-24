'use client';

/**
 * ConversationList component for displaying past conversations.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { EditableTitle } from '@/components/conversations/EditableTitle';
import { JournalMetadata } from '@/lib/types/journal';
import { listJournals, deleteJournal } from '@/lib/api/chat';
import { updateJournalTitle } from '@/lib/api/journals';
import { cn } from '@/lib/utils';
import { FileText, Trash2, MessageSquare, PenTool } from 'lucide-react';
import { parseApiError } from '@/lib/utils/error-handlers';
import { Button } from '@/components/ui/button';

interface ConversationListProps {
  onSelect: (sessionId: string) => void;
  currentSessionId?: string;
  className?: string;
  refreshTrigger?: number; // External trigger to refresh conversations
  sidebarWidth?: number; // Width of the sidebar for responsive adjustments
}

export const ConversationList = React.memo(function ConversationList({
  onSelect,
  currentSessionId,
  className,
  refreshTrigger,
  sidebarWidth = 320,
}: ConversationListProps) {
  const [conversations, setConversations] = useState<JournalMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helper function to get the appropriate icon for the mode
  const getModeIcon = (mode: "chat" | "write") => {
    return mode === "chat" ? MessageSquare : PenTool;
  };

  const loadConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await listJournals(50, 0);
      setConversations(response.journals);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load conversations';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleDeleteConversation = useCallback(async (conversationId: string, conversationTitle: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${conversationTitle}"?\n\nThis action cannot be undone and will permanently remove all messages in this conversation.`
    );
    
    if (!confirmed) return;
    
    try {
      await deleteJournal(conversationId);
      console.log(`Deleted conversation: ${conversationTitle}`);
      
      // Refresh the conversation list by reloading
      loadConversations();
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError('Failed to delete conversation');
    }
  }, [loadConversations]);

  const handleUpdateTitle = useCallback(async (conversationId: string, newTitle: string) => {
    try {
      await updateJournalTitle(conversationId, newTitle);
      
      // Update the local state to reflect the change immediately
      setConversations(prev => 
        prev.map(conv => 
          conv.id === conversationId 
            ? { ...conv, title: newTitle }
            : conv
        )
      );
    } catch (err) {
      console.error('Failed to update conversation title:', err);
      throw err; // Re-throw to let EditableTitle handle the error
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Refresh when external trigger changes (e.g., new conversation created)
  useEffect(() => {
    if (refreshTrigger !== undefined) {
      loadConversations();
    }
  }, [refreshTrigger, loadConversations]);

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center p-4', className)}>
        <LoadingSpinner size="md" text="Loading conversations..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('p-4', className)}>
        <ErrorMessage
          title="Failed to load conversations"
          message={parseApiError(error)}
          onRetry={loadConversations}
        />
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className={cn('p-4 text-sm text-claude-text-muted text-center', className)}>
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No conversations yet</p>
        <p className="text-xs mt-1">Start a new conversation to begin</p>
      </div>
    );
  }

  return (
    <ScrollArea className={cn('h-full', className)}>
      <div className="space-y-1 p-3">
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={cn(
              'w-full p-3 hover:bg-claude-hover transition-colors group cursor-pointer rounded-md',
              currentSessionId === conversation.id && 'bg-claude-hover'
            )}
            onClick={() => onSelect(conversation.id)}
            style={{ 
              minWidth: `${sidebarWidth - 24}px`, // Account for padding (12px * 2)
              maxWidth: `${sidebarWidth - 24}px`
            }}
          >
            <div className="flex items-start justify-between w-full">
              <div className="flex items-start gap-2 flex-1 min-w-0">
                {/* Mode Icon - positioned to align with center of title */}
                <div 
                  className="flex-shrink-0 mt-2.5"
                  title={conversation.mode === "chat" ? "Chat conversation" : "Write session"}
                >
                  {React.createElement(getModeIcon(conversation.mode), {
                    className: "h-4 w-4 text-claude-text-muted"
                  })}
                </div>
                
                {/* Content */}
                <div className="flex-1 space-y-1 min-w-0">
                  <EditableTitle
                    title={conversation.title || 'Untitled Conversation'}
                    onUpdate={(newTitle) => handleUpdateTitle(conversation.id, newTitle)}
                    className="mb-1"
                  />
                  <p className="text-xs text-claude-text-muted truncate">
                    {new Date(conversation.date).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 text-claude-text-muted hover:text-destructive flex-shrink-0 ml-2"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConversation(conversation.id, conversation.title);
                }}
                title="Delete conversation"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
});

