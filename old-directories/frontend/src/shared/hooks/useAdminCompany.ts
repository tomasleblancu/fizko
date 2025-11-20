import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { CompanyDetail } from "@/shared/types/admin";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

/**
 * Hook to fetch detailed company information for admin view
 * Uses React Query for caching and automatic refetching
 */
export function useAdminCompany(companyId: string | undefined) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['admin', 'company', companyId],
    queryFn: async (): Promise<CompanyDetail> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      if (!companyId) {
        throw new Error('Company ID is required');
      }

      const response = await apiFetch(`${API_BASE_URL}/admin/company/${companyId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch company data');
      }

      return response.json();
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 3 * 60 * 1000, // 3 minutes (more frequent for detail view)
  });
}
