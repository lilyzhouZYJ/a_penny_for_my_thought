'use client';

/**
 * NewConversationButton component for starting new conversations.
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

interface NewConversationButtonProps {
  onClick: () => void;
  disabled?: boolean;
  className?: string;
}

export const NewConversationButton = React.memo(function NewConversationButton({
  onClick,
  disabled = false,
  className,
}: NewConversationButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      variant="default"
      className={className}
      size="default"
    >
      <Plus className="h-4 w-4 mr-2" />
      New Conversation
    </Button>
  );
});

