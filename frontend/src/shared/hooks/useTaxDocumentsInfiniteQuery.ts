import { useInfiniteQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import type { TaxDocument } from "@/shared/types/fizko";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

/**
 * React Query infinite query hook for fetching tax documents with pagination.
 *
 * Uses CompanyContext to get the currently selected company ID.
 * Query key: ['home', 'tax-documents-infinite', companyId, limit, period, contactRut]
 * Stale time: 2 minutes
 *
 * @param limit - Number of documents per page (default: 50)
 * @param period - Optional period filter (e.g., '2024-01' for January 2024)
 * @param contactRut - Optional contact RUT filter
 * @param enabled - Whether the query should run (default: true)
 * @returns Infinite query result with pages of tax documents
 *
 * @example
 * ```tsx
 * const {
 *   data,
 *   fetchNextPage,
 *   hasNextPage,
 *   isFetchingNextPage,
 *   isLoading
 * } = useTaxDocumentsInfiniteQuery();
 *
 * // Flatten all pages
 * const documents = data?.pages.flat() ?? [];
 * ```
 */
export function useTaxDocumentsInfiniteQuery(
  limit: number = 50,
  period?: string,
  contactRut?: string,
  enabled: boolean = true
) {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();

  return useInfiniteQuery({
    queryKey: ['home', 'tax-documents-infinite', selectedCompanyId, limit, period, contactRut],
    queryFn: async ({ pageParam = 0 }): Promise<TaxDocument[]> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      params.append('offset', pageParam.toString());
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
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      // If the last page has fewer documents than the limit, we've reached the end
      if (lastPage.length < limit) {
        return undefined;
      }
      // Calculate the next offset
      return allPages.length * limit;
    },
    enabled: !!session?.access_token && !!selectedCompanyId && enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
