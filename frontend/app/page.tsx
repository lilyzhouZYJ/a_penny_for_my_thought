'use client';

/**
 * Home page - Main chat interface with sidebar.
 */

import React, { useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChatSidebar } from '@/components/layout/ChatSidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { useChat } from '@/lib/context/ChatContext';
import { useWrite } from '@/lib/context/WriteContext';
import { handleSessionSelection } from '@/lib/utils/session-navigation';

export default function HomePage() {
  const router = useRouter();
  const { sessionId, handleNewConversation, conversationRefreshTrigger, clearChat } = useChat();
  const { handleNewWrite } = useWrite();

  // Clear chat state when home page loads
  useEffect(() => {
    clearChat();
  }, [clearChat]);

  const handleSelectConversation = useCallback(
    async (selectedSessionId: string) => {
      await handleSessionSelection(selectedSessionId, router);
    },
    [router]
  );

  return (
    <div className="flex h-screen bg-claude-bg">
      {/* Sidebar - Hidden on mobile, shown on md+ */}
      <ChatSidebar
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onNewWrite={handleNewWrite}
        currentSessionId={sessionId}
        className="shrink-0"
        conversationRefreshTrigger={conversationRefreshTrigger}
      />

      {/* Main chat area - Full width on mobile, flex-1 on desktop */}
      <main className="flex-1 w-full overflow-hidden bg-claude-bg">
        <ChatInterface />
      </main>
    </div>
  );
}
