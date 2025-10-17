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
import { getAllJournals } from '@/lib/api/journals';
import { cn } from '@/lib/utils';
import { FileText } from 'lucide-react';
import { parseApiError } from '@/lib/utils/error-handlers';

interface ConversationListProps {
  onSelect: (sessionId: string) => void;
  currentSessionId?: string;
  className?: string;
}

export const ConversationList = React.memo(function ConversationList({
  onSelect,
  currentSessionId,
  className,
}: ConversationListProps) {
  const [conversations, setConversations] = useState<JournalMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getAllJournals(50, 0);
      setConversations(response.journals);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError('Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations, refreshKey]);

  // Auto-refresh every 5 seconds to pick up new conversations
  useEffect(() => {
    const interval = setInterval(() => {
      setRefreshKey(prev => prev + 1);
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

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
              'p-3 cursor-pointer hover:bg-accent transition-colors',
              currentSessionId === conversation.id && 'bg-accent border-primary'
            )}
            onClick={() => onSelect(conversation.id)}
          >
            <div className="space-y-1">
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
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
});

