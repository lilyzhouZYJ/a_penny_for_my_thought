/**
 * Shared utilities for session navigation.
 */

/**
 * Handle session selection by checking the session's mode and routing accordingly.
 * 
 * @param selectedSessionId - The session ID to navigate to
 * @param router - Next.js router instance
 * @param mode - Optional mode hint to avoid API call
 */
export async function handleSessionSelection(
  selectedSessionId: string,
  router: any,
  mode?: "chat" | "write"
): Promise<void> {
  try {
    // If mode is provided, use it directly to avoid API call
    if (mode) {
      if (mode === 'write') {
        router.push(`/write/${selectedSessionId}`);
      } else {
        router.push(`/chat/${selectedSessionId}`);
      }
      return;
    }

    // Fallback: Try to get the journal to check its mode (only if mode not provided)
    const { getJournal } = await import('@/lib/api/journals');
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
