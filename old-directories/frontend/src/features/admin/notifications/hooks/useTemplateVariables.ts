/**
 * Custom hook for fetching template variables from the API
 */

import { useState, useEffect } from 'react';
import { API_BASE_URL } from '@/shared/lib/config';
import { apiFetch } from '@/shared/lib/api-client';
import type { TemplateVariable, TemplateVariablesResponse } from '../types/template-variables';

interface UseTemplateVariablesOptions {
  /** Template code (legacy, for non-summary templates) */
  templateCode?: string | null;
  /** Service method name (for summary templates) */
  serviceMethod?: string | null;
  enabled?: boolean;
  accessToken?: string;
}

interface UseTemplateVariablesReturn {
  variables: TemplateVariable[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch template variables based on template code or service method
 *
 * @param options - Configuration options
 * @returns Template variables data and loading state
 *
 * @example
 * ```tsx
 * // For summary templates (preferred)
 * const { variables, isLoading } = useTemplateVariables({
 *   serviceMethod: 'get_daily_summary',
 *   enabled: true,
 *   accessToken: session?.access_token
 * });
 *
 * // For regular templates (legacy)
 * const { variables, isLoading } = useTemplateVariables({
 *   templateCode: 'calendar_reminder',
 *   enabled: true,
 *   accessToken: session?.access_token
 * });
 * ```
 */
export function useTemplateVariables({
  templateCode,
  serviceMethod,
  enabled = true,
  accessToken,
}: UseTemplateVariablesOptions): UseTemplateVariablesReturn {
  const [variables, setVariables] = useState<TemplateVariable[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVariables = async () => {
    if (!accessToken || !enabled) {
      setVariables([]);
      return;
    }

    // Prefer serviceMethod over templateCode
    const endpoint = serviceMethod
      ? `${API_BASE_URL}/template-variables/by-method/${serviceMethod}`
      : templateCode
      ? `${API_BASE_URL}/template-variables/${templateCode}`
      : null;

    if (!endpoint) {
      setVariables([]);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiFetch(endpoint, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // If variables not found, just return empty array (not an error)
        setVariables([]);
        return;
      }

      const data: TemplateVariablesResponse = await response.json();
      setVariables(data.data?.variables || []);
    } catch (err) {
      console.error('Error fetching template variables:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setVariables([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVariables();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateCode, serviceMethod, enabled, accessToken]);

  return {
    variables,
    isLoading,
    error,
    refetch: fetchVariables,
  };
}
