/**
 * API Client for Fizko Backend
 *
 * This client handles communication with the FastAPI backend,
 * including authentication, error handling, and request/response formatting.
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8089';

export interface ApiClientConfig {
  headers?: Record<string, string>;
  companyId?: string;
  userId?: string;
}

/**
 * Base API client for backend communication
 */
export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = BACKEND_URL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    };

    if (config.companyId) {
      this.defaultHeaders['X-Company-ID'] = config.companyId;
    }
  }

  /**
   * GET request
   */
  async get<T = any>(
    path: string,
    options: {
      params?: Record<string, any>;
      headers?: Record<string, string>;
    } = {}
  ): Promise<T> {
    const url = new URL(path, this.baseUrl);

    // Add query params
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }

    return response.json();
  }

  /**
   * POST request
   */
  async post<T = any>(
    path: string,
    data?: any,
    options: {
      headers?: Record<string, string>;
    } = {}
  ): Promise<T> {
    const url = new URL(path, this.baseUrl);

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }

    return response.json();
  }
}

/**
 * API Error class
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public body: string
  ) {
    super(`API Error ${status}: ${body}`);
    this.name = 'ApiError';
  }
}

/**
 * Create an API client instance with context
 */
export function createApiClient(config: ApiClientConfig = {}): ApiClient {
  return new ApiClient(config);
}
