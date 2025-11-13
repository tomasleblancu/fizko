import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import type { TaxDocument } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

/**
 * React Query hook for fetching tax documents for a company.
 *
 * Query key: ['home', 'tax-documents', companyId, limit, period, contactRut]
 * Stale time: 2 minutes
 *
 * @param companyId - The company ID to fetch documents for
 * @param limit - Maximum number of documents to fetch (default: 10)
 * @param period - Optional period filter (e.g., '2024-01' for January 2024)
 * @param contactRut - Optional contact RUT filter (e.g., '12345678-9' to show only documents with this contact)
 * @param enabled - Whether the query should run (default: true)
 * @returns Query result with tax documents array, loading and error states
 *
 * @example
 * ```tsx
 * // Fetch recent 10 documents
 * const { data: documents = [], isLoading } = useTaxDocumentsQuery(companyId);
 *
 * // Fetch expanded 50 documents
 * const { data: documents = [] } = useTaxDocumentsQuery(companyId, 50);
 *
 * // Fetch documents for a specific contact
 * const { data: documents = [] } = useTaxDocumentsQuery(companyId, 50, undefined, '12345678-9');
 * ```
 */
export function useTaxDocumentsQuery(
  companyId?: string | null,
  limit: number = 10,
  period?: string,
  contactRut?: string,
  enabled: boolean = true
) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['home', 'tax-documents', companyId, limit, period, contactRut],
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

      // Use new endpoint that doesn't require company_id - backend will resolve it from user session
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
    enabled: !!session?.access_token && enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
