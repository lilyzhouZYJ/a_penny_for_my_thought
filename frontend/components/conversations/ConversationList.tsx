'use client';

/**
 * ConversationList component for displaying past conversations.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { JournalMetadata } from '@/lib/types/journal';
import { listJournals, deleteJournal } from '@/lib/api/chat';
import { cn } from '@/lib/utils';
import { FileText, Trash2 } from 'lucide-react';
import { parseApiError } from '@/lib/utils/error-handlers';
import { Button } from '@/components/ui/button';

interface ConversationListProps {
  onSelect: (sessionId: string) => void;
  currentSessionId?: string;
  className?: string;
  refreshTrigger?: number; // External trigger to refresh conversations
}

export const ConversationList = React.memo(function ConversationList({
  onSelect,
  currentSessionId,
  className,
  refreshTrigger,
}: ConversationListProps) {
  const [conversations, setConversations] = useState<JournalMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('Loading conversations from API...');
      const response = await listJournals(50, 0);
      console.log('API response:', response);
      setConversations(response.journals);
      console.log(`Loaded ${response.journals.length} conversations`);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load conversations';
      setError(errorMessage);
      console.error('Error details:', errorMessage);
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
      <div className={cn('p-4 text-sm text-muted-foreground text-center', className)}>
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No conversations yet</p>
        <p className="text-xs mt-1">Start a new conversation to begin</p>
      </div>
    );
  }

  return (
    <ScrollArea className={cn('h-full', className)}>
      <div className="space-y-2 p-2">
        {conversations.map((conversation) => (
          <Card
            key={conversation.id}
            className={cn(
              'p-3 hover:bg-accent transition-colors group',
              currentSessionId === conversation.id && 'bg-accent border-primary'
            )}
          >
            <div className="flex items-start justify-between">
              <div 
                className="flex-1 cursor-pointer space-y-1"
                onClick={() => onSelect(conversation.id)}
              >
                <h3 className="font-medium text-sm line-clamp-1">
                  {conversation.title || 'Untitled Conversation'}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {new Date(conversation.date).toLocaleDateString()}
                </p>
                {conversation.message_count !== undefined && (
                  <p className="text-xs text-muted-foreground">
                    {conversation.message_count} message{conversation.message_count !== 1 ? 's' : ''}
                  </p>
                )}
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConversation(conversation.id, conversation.title);
                }}
                title="Delete conversation"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
});

