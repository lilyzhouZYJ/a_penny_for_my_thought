/**
 * Custom hook to persist sidebar width in localStorage.
 */

import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'sidebar-width';
const DEFAULT_WIDTH = 320;
const MIN_WIDTH = 240;
const MAX_WIDTH = 600;

export function useSidebarWidth() {
  const [sidebarWidth, setSidebarWidthState] = useState(DEFAULT_WIDTH);

  // Load width from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const width = parseInt(stored, 10);
        if (!isNaN(width) && width >= MIN_WIDTH && width <= MAX_WIDTH) {
          setSidebarWidthState(width);
        }
      }
    } catch (error) {
      console.warn('Failed to load sidebar width from localStorage:', error);
    }
  }, []);

  // Save width to localStorage whenever it changes
  const setSidebarWidth = useCallback((width: number) => {
    // Clamp width to valid range
    const clampedWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, width));
    
    setSidebarWidthState(clampedWidth);
    
    try {
      localStorage.setItem(STORAGE_KEY, clampedWidth.toString());
    } catch (error) {
      console.warn('Failed to save sidebar width to localStorage:', error);
    }
  }, []);

  return [sidebarWidth, setSidebarWidth] as const;
}
