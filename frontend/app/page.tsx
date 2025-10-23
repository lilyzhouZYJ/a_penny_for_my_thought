'use client';

/**
 * Home page - Main chat interface with sidebar.
 */

import React, { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ChatSidebar } from '@/components/layout/ChatSidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { useChat } from '@/lib/context/ChatContext';

export default function HomePage() {
  const router = useRouter();
  const { sessionId, handleNewConversation, conversationRefreshTrigger } = useChat();

  const handleSelectConversation = useCallback(
    (selectedSessionId: string) => {
      // Navigate to the chat URL
      router.push(`/chat/${selectedSessionId}`);
    },
    [router]
  );

  return (
    <div className="flex h-screen bg-claude-bg">
      {/* Sidebar - Hidden on mobile, shown on md+ */}
      <ChatSidebar
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        currentSessionId={sessionId}
        className="w-80 shrink-0"
        conversationRefreshTrigger={conversationRefreshTrigger}
      />

      {/* Main chat area - Full width on mobile, flex-1 on desktop */}
      <main className="flex-1 w-full overflow-hidden bg-claude-bg">
        <ChatInterface />
      </main>
    </div>
  );
}
