/**
 * Shared utilities for session navigation.
 */

import { getJournal } from '@/lib/api/journals';

/**
 * Handle session selection by checking the session's mode and routing accordingly.
 * 
 * @param selectedSessionId - The session ID to navigate to
 * @param router - Next.js router instance
 */
export async function handleSessionSelection(
  selectedSessionId: string,
  router: any
): Promise<void> {
  try {
    // Try to get the journal to check its mode
    const journal = await getJournal(selectedSessionId);
    
    // Route based on the journal's mode
    if (journal.mode === 'write') {
      router.push(`/write/${selectedSessionId}`);
    } else {
      router.push(`/chat/${selectedSessionId}`);
    }
  } catch (err) {
    // If we can't load the journal, default to chat mode
    console.warn('Could not determine session mode, defaulting to chat:', err);
    router.push(`/chat/${selectedSessionId}`);
  }
}
