import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import type { Company } from '../types/fizko';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

/**
 * React Query hook for fetching the user's company data.
 *
 * Query key: ['home', 'company', userId]
 * Stale time: 5 minutes
 *
 * @returns Query result with company data, loading and error states
 *
 * @example
 * ```tsx
 * const { data: company, isLoading, error } = useCompanyQuery();
 * ```
 */
export function useCompanyQuery() {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['home', 'company', session?.user.id],
    queryFn: async (): Promise<Company | null> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const response = await apiFetch(`${API_BASE_URL}/companies`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch companies: ${response.statusText}`);
      }

      const result = await response.json();
      // Get first company from the list or null if empty
      return result.data && result.data.length > 0 ? result.data[0] : null;
    },
    enabled: !!session?.access_token,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
