import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/shared/lib/supabase';

export type FormType = 'all' | 'monthly' | 'annual';
export type FormStatus = 'all' | 'Vigente' | 'Rectificado' | 'Anulado';
export type PDFStatus = 'all' | 'pending' | 'downloaded' | 'error';

export interface F29Form {
  id: string;
  folio: string;
  period_year: number;
  period_month: number;
  period_display: string;
  submission_date: string | null;
  status: string;
  amount_cents: number;
  pdf_download_status: string;
  has_pdf: boolean;
  pdf_url: string | null;
  created_at: string;
}

export interface F29FormsResponse {
  forms: F29Form[];
  total: number;
  filtered: number;
}

interface UseF29FormsQueryOptions {
  companyId: string | undefined;
  formType?: FormType;
  year?: number;
  status?: FormStatus;
  pdfStatus?: PDFStatus;
}

export function useF29FormsQuery({
  companyId,
  formType = 'all',
  year,
  status = 'all',
  pdfStatus = 'all'
}: UseF29FormsQueryOptions) {
  return useQuery<F29FormsResponse>({
    queryKey: ['f29-forms', companyId, formType, year, status, pdfStatus],
    queryFn: async () => {
      if (!companyId) {
        throw new Error('Company ID is required');
      }

      // Get session for authorization
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('Not authenticated');
      }

      // Build query parameters
      const params = new URLSearchParams({
        company_id: companyId,
      });

      if (formType && formType !== 'all') {
        params.append('form_type', formType);
      }

      if (year) {
        params.append('year', year.toString());
      }

      if (status && status !== 'all') {
        params.append('status', status);
      }

      if (pdfStatus && pdfStatus !== 'all') {
        params.append('pdf_status', pdfStatus);
      }

      const response = await fetch(
        `${import.meta.env.VITE_BACKEND_URL}/api/sii/forms/f29?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to fetch F29 forms' }));
        throw new Error(error.detail || 'Failed to fetch F29 forms');
      }

      return response.json();
    },
    enabled: !!companyId,
  });
}
