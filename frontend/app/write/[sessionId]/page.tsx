'use client';

/**
 * Dynamic write session page - loads specific write session.
 */

import React, { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChatSidebar } from '@/components/layout/ChatSidebar';
import { WriteInterface } from '@/components/write/WriteInterface';
import { useWrite } from '@/lib/context/WriteContext';
import { useChat } from '@/lib/context/ChatContext';
import { handleSessionSelection } from '@/lib/utils/session-navigation';

export default function WriteSessionPage() {
  const params = useParams();
  const router = useRouter();
  const { sessionId, loadSession, handleNewWrite, journalRefreshTrigger } = useWrite();
  const { handleNewJournal } = useChat();
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

  const handleSelectJournal = React.useCallback(
    async (selectedSessionId: string, mode: "chat" | "write") => {
      await handleSessionSelection(selectedSessionId, router, mode);
    },
    [router]
  );

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Hidden on mobile, shown on md+ */}
      <ChatSidebar
        onSelectJournal={handleSelectJournal}
        onNewJournal={handleNewJournal}
        onNewWrite={handleNewWrite}
        currentSessionId={sessionId}
        className="shrink-0"
        journalRefreshTrigger={journalRefreshTrigger}
      />

      {/* Main write area - Full width on mobile, flex-1 on desktop */}
      <main className="flex-1 w-full overflow-hidden">
        <WriteInterface />
      </main>
    </div>
  );
}
