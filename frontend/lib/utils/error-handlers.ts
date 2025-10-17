/**
 * Error handling utilities for parsing and formatting API errors.
 */

/**
 * Parse API error into user-friendly message.
 * 
 * @param error - Error object from API call
 * @returns User-friendly error message
 */
export function parseApiError(error: unknown): string {
  // Handle Error objects
  if (error instanceof Error) {
    // Check for common error patterns
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      return 'Unable to connect to the server. Please check your internet connection.';
    }
    
    if (error.message.includes('timeout')) {
      return 'The request timed out. Please try again.';
    }
    
    if (error.message.includes('API Error')) {
      return 'There was a problem processing your request. Please try again.';
    }
    
    if (error.message.includes('Journal not found')) {
      return 'The conversation could not be found. It may have been deleted.';
    }
    
    if (error.message.includes('Failed to send message')) {
      return 'Failed to send your message. Please check your connection and try again.';
    }
    
    if (error.message.includes('Failed to load')) {
      return 'Failed to load the conversation. Please try again.';
    }
    
    // Return the original error message if no pattern matches
    return error.message;
  }
  
  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }
  
  // Handle objects with detail property (FastAPI error format)
  if (error && typeof error === 'object' && 'detail' in error) {
    return String((error as { detail: unknown }).detail);
  }
  
  // Fallback for unknown error types
  return 'An unexpected error occurred. Please try again.';
}

/**
 * Check if error is a network error.
 * 
 * @param error - Error object
 * @returns True if network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes('Failed to fetch') ||
      error.message.includes('NetworkError') ||
      error.message.includes('Network request failed')
    );
  }
  return false;
}

/**
 * Check if error is recoverable (user can retry).
 * 
 * @param error - Error object
 * @returns True if error is recoverable
 */
export function isRecoverableError(error: unknown): boolean {
  if (error instanceof Error) {
    // Network errors are recoverable
    if (isNetworkError(error)) {
      return true;
    }
    
    // Timeout errors are recoverable
    if (error.message.includes('timeout')) {
      return true;
    }
    
    // Server errors (5xx) are recoverable
    if (error.message.includes('HTTP 5')) {
      return true;
    }
    
    // Rate limit errors are recoverable
    if (error.message.includes('429') || error.message.includes('rate limit')) {
      return true;
    }
  }
  
  return false;
}

/**
 * Get retry delay based on error type (in milliseconds).
 * 
 * @param error - Error object
 * @param attempt - Retry attempt number (0-based)
 * @returns Delay in milliseconds
 */
export function getRetryDelay(error: unknown, attempt: number = 0): number {
  // Base delay with exponential backoff
  const baseDelay = 1000; // 1 second
  const maxDelay = 10000; // 10 seconds
  
  // Exponential backoff: 1s, 2s, 4s, 8s, 10s (capped)
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  
  // Add jitter to prevent thundering herd
  const jitter = Math.random() * 500;
  
  return delay + jitter;
}

