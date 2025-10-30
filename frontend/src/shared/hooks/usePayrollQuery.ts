import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import type { PayrollSummary } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

/**
 * React Query hook for fetching payroll summary for a company.
 *
 * Query key: ['home', 'payroll', companyId, period]
 * Stale time: 5 minutes
 *
 * @param companyId - The company ID to fetch payroll for
 * @param period - Optional period filter (e.g., '2024-01' for January 2024)
 * @returns Query result with payroll summary data, loading and error states
 *
 * @example
 * ```tsx
 * // Fetch current payroll summary
 * const { data: payrollSummary, isLoading } = usePayrollQuery(companyId);
 *
 * // Fetch for specific period
 * const { data } = usePayrollQuery(companyId, '2024-01');
 * ```
 */
export function usePayrollQuery(companyId: string | null, period?: string) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['home', 'payroll', companyId, period],
    queryFn: async (): Promise<PayrollSummary | null> => {
      if (!session?.access_token || !companyId) {
        throw new Error('No authenticated session or company ID');
      }

      const params = new URLSearchParams();
      if (period) {
        params.append('period', period);
      }

      const url = `${API_BASE_URL}/payroll-summary/${companyId}${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 404 is expected for new companies without payroll data yet
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to fetch payroll summary: ${response.statusText}`);
      }

      return await response.json();
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
