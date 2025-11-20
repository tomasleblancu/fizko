/**
 * Backend V2 HTTP Client
 *
 * Centralized HTTP client for communicating with the FastAPI backend (backend-v2).
 * Provides a consistent interface for all backend API calls.
 */

/**
 * Backend client configuration
 */
export class BackendClient {
  private static readonly DEFAULT_URL = 'http://localhost:8089';

  /**
   * Get the backend URL from environment or use default
   */
  static getBaseUrl(): string {
    return process.env.NEXT_PUBLIC_BACKEND_URL || this.DEFAULT_URL;
  }

  /**
   * Get the full URL for an endpoint
   *
   * @param endpoint - API endpoint path (e.g., '/api/sii/login')
   * @returns Full URL
   */
  static getUrl(endpoint: string): string {
    const baseUrl = this.getBaseUrl();
    // Ensure endpoint starts with /
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${normalizedEndpoint}`;
  }

  /**
   * Make a GET request to the backend
   *
   * @param endpoint - API endpoint path
   * @param options - Optional fetch options
   * @returns Response data
   */
  static async get<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = this.getUrl(endpoint);
    console.log(`[Backend Client] GET ${url}`);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Backend Client] GET ${url} failed:`, errorText);
      throw new Error(
        `Backend error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Make a POST request to the backend
   *
   * @param endpoint - API endpoint path
   * @param body - Request body
   * @param options - Optional fetch options
   * @returns Response data
   */
  static async post<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit
  ): Promise<T> {
    const url = this.getUrl(endpoint);
    console.log(`[Backend Client] POST ${url}`);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Backend Client] POST ${url} failed:`, errorText);
      throw new Error(
        `Backend error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Make a PUT request to the backend
   *
   * @param endpoint - API endpoint path
   * @param body - Request body
   * @param options - Optional fetch options
   * @returns Response data
   */
  static async put<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit
  ): Promise<T> {
    const url = this.getUrl(endpoint);
    console.log(`[Backend Client] PUT ${url}`);

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Backend Client] PUT ${url} failed:`, errorText);
      throw new Error(
        `Backend error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Make a DELETE request to the backend
   *
   * @param endpoint - API endpoint path
   * @param options - Optional fetch options
   * @returns Response data
   */
  static async delete<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = this.getUrl(endpoint);
    console.log(`[Backend Client] DELETE ${url}`);

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Backend Client] DELETE ${url} failed:`, errorText);
      throw new Error(
        `Backend error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Make a PATCH request to the backend
   *
   * @param endpoint - API endpoint path
   * @param body - Request body
   * @param options - Optional fetch options
   * @returns Response data
   */
  static async patch<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit
  ): Promise<T> {
    const url = this.getUrl(endpoint);
    console.log(`[Backend Client] PATCH ${url}`);

    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Backend Client] PATCH ${url} failed:`, errorText);
      throw new Error(
        `Backend error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }
}
