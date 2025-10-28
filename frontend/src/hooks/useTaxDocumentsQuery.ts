import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import type { TaxDocument } from '../types/fizko';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

/**
 * React Query hook for fetching tax documents for a company.
 *
 * Query key: ['home', 'tax-documents', companyId, limit, period]
 * Stale time: 2 minutes
 *
 * @param companyId - The company ID to fetch documents for
 * @param limit - Maximum number of documents to fetch (default: 10)
 * @param period - Optional period filter (e.g., '2024-01' for January 2024)
 * @returns Query result with tax documents array, loading and error states
 *
 * @example
 * ```tsx
 * // Fetch recent 10 documents
 * const { data: documents = [], isLoading } = useTaxDocumentsQuery(companyId);
 *
 * // Fetch expanded 50 documents
 * const { data: documents = [] } = useTaxDocumentsQuery(companyId, 50);
 * ```
 */
export function useTaxDocumentsQuery(
  companyId: string | null,
  limit: number = 10,
  period?: string
) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['home', 'tax-documents', companyId, limit, period],
    queryFn: async (): Promise<TaxDocument[]> => {
      if (!session?.access_token || !companyId) {
        throw new Error('No authenticated session or company ID');
      }

      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (period) {
        params.append('period', period);
      }

      const url = `${API_BASE_URL}/tax-documents/${companyId}?${params.toString()}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 404 is expected for new companies without documents yet
        if (response.status === 404) {
          return [];
        }
        throw new Error(`Failed to fetch tax documents: ${response.statusText}`);
      }

      return await response.json();
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
