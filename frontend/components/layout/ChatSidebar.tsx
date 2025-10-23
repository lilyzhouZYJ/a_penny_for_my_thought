'use client';

/**
 * ChatSidebar component for conversation navigation.
 * Responsive: Fixed sidebar on desktop, drawer on mobile.
 */

import React, { useState } from 'react';
import { ConversationList } from '@/components/conversations/ConversationList';
import { NewConversationButton } from '@/components/conversations/NewConversationButton';
import { Separator } from '@/components/ui/separator';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatSidebarProps {
  onSelectConversation: (sessionId: string) => void;
  onNewConversation: () => void;
  currentSessionId?: string;
  className?: string;
  conversationRefreshTrigger?: number;
}

const SidebarContent = React.memo(function SidebarContent({
  onSelectConversation,
  onNewConversation,
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
      <div className="p-4 space-y-4">
        <div>
          <h1 className="text-xl font-bold">A Penny For My Thought</h1>
          <p className="text-sm text-muted-foreground">AI-powered journaling</p>
        </div>
        
        <NewConversationButton
          onClick={handleNewChat}
          className="w-full min-h-[44px]" // Touch-friendly
        />
      </div>

      <Separator />

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

export const ChatSidebar = React.memo(function ChatSidebar({
  onSelectConversation,
  onNewConversation,
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
          'hidden md:flex flex-col h-full bg-background border-r',
          className
        )}
      >
        <SidebarContent
          onSelectConversation={onSelectConversation}
          onNewConversation={onNewConversation}
          currentSessionId={currentSessionId}
          conversationRefreshTrigger={conversationRefreshTrigger}
        />
      </aside>
    </>
  );
});

