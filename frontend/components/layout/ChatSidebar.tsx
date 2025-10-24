'use client';

/**
 * ChatSidebar component for conversation navigation.
 * Responsive: Fixed sidebar on desktop, drawer on mobile.
 */

import React, { useState } from 'react';
import { ConversationList } from '@/components/conversations/ConversationList';
import { NewButton } from '@/components/conversations/NewButton';
import { Separator } from '@/components/ui/separator';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatSidebarProps {
  onSelectConversation: (sessionId: string) => void;
  onNewConversation: () => void;
  onNewWrite?: () => void;
  currentSessionId?: string;
  className?: string;
  conversationRefreshTrigger?: number;
}

const SidebarContent = React.memo(function SidebarContent({
  onSelectConversation,
  onNewConversation,
  onNewWrite,
  currentSessionId,
  conversationRefreshTrigger,
  onItemClick,
}: ChatSidebarProps & { onItemClick?: () => void }) {
  const handleSelect = (sessionId: string) => {
    onSelectConversation(sessionId);
    onItemClick?.(); // Close drawer on mobile
  };

  const handleNewChat = () => {
    onNewConversation();
    onItemClick?.(); // Close drawer on mobile
  };

  return (
    <>
      {/* Header */}
      <div className="p-6 space-y-6">
        <div className="space-y-2">
          <h1 className="text-xl font-bold text-claude-text">A Penny For My Thought</h1>
          <p className="text-sm text-claude-text-muted">AI-powered journaling</p>
        </div>
        
        <NewButton
          onNewChat={handleNewChat}
          onNewWrite={onNewWrite || (() => {})}
          className="w-full min-h-[48px] claude-button" // Touch-friendly
        />
      </div>

      <Separator className="bg-claude-border" />

      {/* Conversations list */}
      <div className="flex-1 overflow-hidden">
        <ConversationList
          onSelect={handleSelect}
          currentSessionId={currentSessionId}
          refreshTrigger={conversationRefreshTrigger}
        />
      </div>
    </>
  );
});

export function ChatSidebar({
  onSelectConversation,
  onNewConversation,
  onNewWrite,
  currentSessionId,
  className,
  conversationRefreshTrigger,
}: ChatSidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile: Drawer Trigger Button */}
      <div className="md:hidden fixed top-4 left-4 z-50">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="h-11 w-11" // Touch-friendly 44px
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-80 p-0 flex flex-col">
            <SidebarContent
              onSelectConversation={onSelectConversation}
              onNewConversation={onNewConversation}
              onNewWrite={onNewWrite}
              currentSessionId={currentSessionId}
              conversationRefreshTrigger={conversationRefreshTrigger}
              onItemClick={() => setMobileOpen(false)}
            />
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop: Fixed Sidebar */}
      <aside
        className={cn(
          'hidden md:flex flex-col h-full bg-claude-sidebar border-r border-claude-border',
          className
        )}
      >
        <SidebarContent
          onSelectConversation={onSelectConversation}
          onNewConversation={onNewConversation}
          onNewWrite={onNewWrite}
          currentSessionId={currentSessionId}
          conversationRefreshTrigger={conversationRefreshTrigger}
        />
      </aside>
    </>
  );
}

