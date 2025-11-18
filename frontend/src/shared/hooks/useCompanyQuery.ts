import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import type { Company } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

/**
 * React Query hook for fetching the selected company's data.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Query key: ['home', 'company', companyId]
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
  const { selectedCompanyId, selectedCompany } = useCompanyContext();

  return useQuery({
    queryKey: queryKeys.company.byId(selectedCompanyId),
    queryFn: async (): Promise<Company | null> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      if (!selectedCompanyId) {
        // No company selected yet, return basic info from context
        return selectedCompany ? {
          id: selectedCompany.id,
          rut: selectedCompany.rut,
          business_name: selectedCompany.business_name,
          trade_name: selectedCompany.trade_name,
        } as Company : null;
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
      // Find the selected company from the response
      const companies = result.data || [];
      return companies.find((c: Company) => c.id === selectedCompanyId) || null;
    },
    enabled: !!session?.access_token && !!selectedCompanyId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
