import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import type { TaxDocument } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

/**
 * React Query hook for fetching tax documents for the selected company.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Query key: ['home', 'tax-documents', companyId, limit, period, contactRut]
 * Stale time: 2 minutes
 *
 * @param limit - Maximum number of documents to fetch (default: 10)
 * @param period - Optional period filter (e.g., '2024-01' for January 2024)
 * @param contactRut - Optional contact RUT filter (e.g., '12345678-9' to show only documents with this contact)
 * @param enabled - Whether the query should run (default: true)
 * @returns Query result with tax documents array, loading and error states
 *
 * @example
 * ```tsx
 * // Fetch recent 10 documents
 * const { data: documents = [], isLoading } = useTaxDocumentsQuery();
 *
 * // Fetch expanded 50 documents
 * const { data: documents = [] } = useTaxDocumentsQuery(50);
 *
 * // Fetch documents for a specific contact
 * const { data: documents = [] } = useTaxDocumentsQuery(50, undefined, '12345678-9');
 * ```
 */
export function useTaxDocumentsQuery(
  limit: number = 10,
  period?: string,
  contactRut?: string,
  enabled: boolean = true
) {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();

  return useQuery({
    queryKey: ['home', 'tax-documents', selectedCompanyId, limit, period, contactRut],
    queryFn: async (): Promise<TaxDocument[]> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (period) {
        params.append('period', period);
      }
      if (contactRut) {
        params.append('contact_rut', contactRut);
      }
      if (selectedCompanyId) {
        params.append('company_id', selectedCompanyId);
      }

      const url = `${API_BASE_URL}/tax-documents?${params.toString()}`;

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
    enabled: !!session?.access_token && !!selectedCompanyId && Boolean(enabled),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
