/**
 * Frontend configuration.
 * 
 * Centralizes environment variable access and provides defaults.
 */

// Next.js replaces process.env.NEXT_PUBLIC_* at build time
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
} as const;

