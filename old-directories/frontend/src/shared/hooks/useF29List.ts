import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

interface F29Download {
  id: string;
  sii_folio: string;
  sii_id_interno: string | null;
  period_year: number;
  period_month: number;
  period_display: string;
  contributor_rut: string;
  submission_date: string | null;
  status: string;
  amount_cents: number;
  pdf_storage_url: string | null;
  pdf_download_status: string;
  pdf_download_error: string | null;
  pdf_downloaded_at: string | null;
  has_pdf: boolean;
  can_download_pdf: boolean;
  extra_data: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

interface UseF29ListOptions {
  year?: number | 'all';
  status?: string | 'all';
}

/**
 * Hook to fetch F29 forms for a company
 * Uses React Query for caching and automatic refetching
 */
export function useF29List(companyId: string | undefined, options: UseF29ListOptions = {}) {
  const { session } = useAuth();
  const { year = 'all', status = 'all' } = options;

  return useQuery({
    queryKey: ['admin', 'f29', companyId, year, status],
    queryFn: async (): Promise<F29Download[]> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      if (!companyId) {
        throw new Error('Company ID is required');
      }

      const params = new URLSearchParams();
      if (year !== 'all') params.append('year', year.toString());
      if (status !== 'all') params.append('status', status);

      const url = `${API_BASE_URL}/admin/company/${companyId}/f29${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al cargar formularios F29');
      }

      return response.json();
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 3 * 60 * 1000, // 3 minutes
  });
}

/**
 * Hook to download F29 PDF
 */
export function useDownloadF29Pdf(companyId: string | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formId: string) => {
      if (!session?.access_token || !companyId) {
        throw new Error('Missing session or company ID');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/admin/company/${companyId}/f29/${formId}/download-pdf`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al descargar PDF');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate F29 list to refetch and show updated status
      queryClient.invalidateQueries({
        queryKey: ['admin', 'f29', companyId],
      });
    },
  });
}
