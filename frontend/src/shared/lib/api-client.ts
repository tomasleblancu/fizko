/**
 * Centralized API client for making fetch requests to the backend.
 *
 * This wrapper automatically adds necessary headers including:
 * - ngrok-skip-browser-warning: Bypasses ngrok's browser warning page
 * - Content-Type: application/json (when applicable)
 *
 * Usage:
 *   import { apiFetch } from '../shared/lib/api-client';
 *   const response = await apiFetch('/api/sessions', {
 *     headers: { 'Authorization': `Bearer ${token}` }
 *   });
 */

interface ApiFetchOptions extends RequestInit {
  headers?: Record<string, string>;
}

/**
 * Enhanced fetch wrapper that automatically adds ngrok bypass header
 * and other common headers needed for API requests.
 */
export async function apiFetch(
  url: string,
  options: ApiFetchOptions = {}
): Promise<Response> {
  const defaultHeaders: Record<string, string> = {
    // Bypass ngrok browser warning page (required for ngrok free tier)
    'ngrok-skip-browser-warning': 'true',
  };

  // Merge headers, with user-provided headers taking precedence
  const headers = {
    ...defaultHeaders,
    ...options.headers,
  };

  // Make the fetch request with merged headers
  return fetch(url, {
    ...options,
    headers,
  });
}

/**
 * Convenience wrapper for JSON responses.
 * Automatically parses JSON and throws on non-OK responses.
 */
export async function apiFetchJson<T = any>(
  url: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const response = await apiFetch(url, options);

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // If JSON parsing fails, use default error message
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
