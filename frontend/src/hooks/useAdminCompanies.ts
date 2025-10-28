import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { CompanySummary } from '../types/admin';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

/**
 * Hook to fetch all companies for admin view
 * Uses React Query for caching and automatic refetching
 */
export function useAdminCompanies() {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['admin', 'companies'],
    queryFn: async (): Promise<CompanySummary[]> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      const response = await apiFetch(`${API_BASE_URL}/admin/companies`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }

      return response.json();
    },
    enabled: !!session?.access_token,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
