'use client';

/**
 * NewButton component with dropdown for creating new Chat or Write sessions.
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, MessageSquare, PenTool } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface NewButtonProps {
  onNewChat: () => void;
  onNewWrite: () => void;
  disabled?: boolean;
  className?: string;
}

export const NewButton = React.memo(function NewButton({
  onNewChat,
  onNewWrite,
  disabled = false,
  className,
}: NewButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleNewChat = () => {
    onNewChat();
    setIsOpen(false);
  };

  const handleNewWrite = () => {
    onNewWrite();
    setIsOpen(false);
  };

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          disabled={disabled}
          variant="default"
          className={className}
          size="default"
        >
          <Plus className="h-4 w-4 mr-2" />
          <span className="text-sm">New</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-48">
        <DropdownMenuItem onClick={handleNewChat} className="cursor-pointer">
          <MessageSquare className="h-4 w-4 mr-2" />
          <span>Chat</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleNewWrite} className="cursor-pointer">
          <PenTool className="h-4 w-4 mr-2" />
          <span>Write</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
});
