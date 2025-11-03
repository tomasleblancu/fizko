import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import type { TaxSummary } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

/**
 * React Query hook for fetching tax summary data for a company.
 *
 * Query key: ['home', 'tax-summary', companyId, period]
 * Stale time: 3 minutes
 *
 * @param companyId - The company ID to fetch tax summary for
 * @param period - Optional period filter (e.g., '2024-01' for January 2024)
 * @returns Query result with tax summary data, loading and error states
 *
 * @example
 * ```tsx
 * const { data: taxSummary, isLoading } = useTaxSummaryQuery(companyId, '2024-01');
 * ```
 */
export function useTaxSummaryQuery(companyId?: string | null, period?: string, enabled: boolean = true) {
  const { session } = useAuth();

  return useQuery({
    queryKey: queryKeys.taxSummary.byPeriod(companyId, period),
    queryFn: async (): Promise<TaxSummary | null> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const params = new URLSearchParams();
      if (period) {
        params.append('period', period);
      }

      // Use new endpoint that doesn't require company_id - backend will resolve it from user session
      const url = `${API_BASE_URL}/tax-summary${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 404 is expected for new companies without tax data yet
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to fetch tax summary: ${response.statusText}`);
      }

      return await response.json();
    },
    enabled: !!session?.access_token && enabled,
    staleTime: 3 * 60 * 1000, // 3 minutes
    refetchOnWindowFocus: true, // Refetch financial data when user returns to window
  });
}
