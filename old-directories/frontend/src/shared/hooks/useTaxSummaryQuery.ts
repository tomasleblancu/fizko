import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import type { TaxSummary } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

/**
 * React Query hook for fetching tax summary data for the selected company.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Query key: ['home', 'tax-summary', companyId, period]
 * Stale time: 3 minutes
 *
 * @param period - Optional period filter (e.g., '2024-01' for January 2024)
 * @param enabled - Whether the query should run (default: true)
 * @returns Query result with tax summary data, loading and error states
 *
 * @example
 * ```tsx
 * const { data: taxSummary, isLoading } = useTaxSummaryQuery('2024-01');
 * ```
 */
export function useTaxSummaryQuery(period?: string, enabled: boolean = true) {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();

  return useQuery({
    queryKey: queryKeys.taxSummary.byPeriod(selectedCompanyId || null, period),
    queryFn: async (): Promise<TaxSummary | null> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const params = new URLSearchParams();
      if (period) {
        params.append('period', period);
      }
      if (selectedCompanyId) {
        params.append('company_id', selectedCompanyId);
      }

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
    enabled: !!session?.access_token && !!selectedCompanyId && enabled,
    staleTime: 3 * 60 * 1000, // 3 minutes
    refetchOnWindowFocus: true, // Refetch financial data when user returns to window
  });
}
