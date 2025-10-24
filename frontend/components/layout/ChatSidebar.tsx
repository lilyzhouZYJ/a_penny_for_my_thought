'use client';

/**
 * ChatSidebar component for conversation navigation.
 * Responsive: Fixed sidebar on desktop, drawer on mobile.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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

interface SidebarContentProps extends ChatSidebarProps {
  onItemClick?: () => void;
  sidebarWidth: number;
}

const SidebarContent = React.memo(function SidebarContent({
  onSelectConversation,
  onNewConversation,
  onNewWrite,
  currentSessionId,
  conversationRefreshTrigger,
  onItemClick,
  sidebarWidth,
}: SidebarContentProps) {
  const router = useRouter();
  
  const handleSelect = (sessionId: string) => {
    onSelectConversation(sessionId);
    onItemClick?.(); // Close drawer on mobile
  };

  const handleNewChat = () => {
    onNewConversation();
    onItemClick?.(); // Close drawer on mobile
  };

  const handleTitleClick = () => {
    router.push('/');
  };

  return (
    <>
      {/* Header */}
      <div className="p-6 space-y-6">
        <div className="space-y-2">
          <h1 
            className="text-xl font-bold text-claude-text cursor-pointer hover:text-claude-accent transition-colors"
            onClick={handleTitleClick}
            title="A Penny For My Thought - Click to go home"
          >
            {sidebarWidth > 400 ? 'A Penny For My Thought' : 
             sidebarWidth > 320 ? 'A Penny For My Thought' : 
             'A Penny For My Thought'}
          </h1>
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
  const [sidebarWidth, setSidebarWidth] = useState(320); // Default width in pixels
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Resize functionality
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    
    const newWidth = e.clientX;
    const minWidth = 240; // Minimum width
    const maxWidth = 600; // Maximum width
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setSidebarWidth(newWidth);
    }
  }, [isResizing]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

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
              sidebarWidth={320} // Mobile drawer uses fixed width
            />
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop: Fixed Sidebar */}
      <aside
        ref={sidebarRef}
        className={cn(
          'hidden md:flex flex-col h-full bg-claude-sidebar border-r border-claude-border relative',
          className
        )}
        style={{ width: `${sidebarWidth}px` }}
      >
        <SidebarContent
          onSelectConversation={onSelectConversation}
          onNewConversation={onNewConversation}
          onNewWrite={onNewWrite}
          currentSessionId={currentSessionId}
          conversationRefreshTrigger={conversationRefreshTrigger}
          sidebarWidth={sidebarWidth}
        />
        
        {/* Resize Handle */}
        <div
          className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-claude-accent/20 transition-colors"
          onMouseDown={handleMouseDown}
        />
      </aside>
    </>
  );
}

