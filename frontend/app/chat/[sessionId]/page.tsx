'use client';

/**
 * Dynamic chat session page - loads specific conversation.
 */

import React, { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChatSidebar } from '@/components/layout/ChatSidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { useChat } from '@/lib/context/ChatContext';

export default function ChatSessionPage() {
  const params = useParams();
  const router = useRouter();
  const { sessionId, loadSession, clearChat } = useChat();
  const urlSessionId = params.sessionId as string;

  // Load the session when the page loads
  useEffect(() => {
    if (urlSessionId && urlSessionId !== sessionId) {
      loadSession(urlSessionId).catch((err) => {
        console.error('Failed to load session:', err);
        router.push('/');
      });
    }
  }, [urlSessionId, sessionId, loadSession, router]);

  const handleSelectConversation = React.useCallback(
    async (selectedSessionId: string) => {
      router.push(`/chat/${selectedSessionId}`);
    },
    [router]
  );

  const handleNewConversation = React.useCallback(() => {
    clearChat();
    router.push('/');
  }, [clearChat, router]);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Hidden on mobile, shown on md+ */}
      <ChatSidebar
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        currentSessionId={sessionId}
        className="w-80 shrink-0"
      />

      {/* Main chat area - Full width on mobile, flex-1 on desktop */}
      <main className="flex-1 w-full overflow-hidden">
        <ChatInterface />
      </main>
    </div>
  );
}

