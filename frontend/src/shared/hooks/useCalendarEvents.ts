import { useQuery } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";
import { queryKeys } from "@/shared/lib/query-keys";

interface CalendarEvent {
  id: string;
  title: string;
  description: string | null;
  event_template_code: string;
  event_template_name: string;
  category: string;
  due_date: string;
  period_start: string | null;
  period_end: string | null;
  status: string;
  completion_date: string | null;
  completion_data: any;
  auto_generated: boolean;
  created_at: string;
}

interface UseCalendarEventsOptions {
  status?: string;
  startDate?: string;
  endDate?: string;
}

/**
 * Hook to fetch calendar events for the selected company.
 * Uses CompanyContext to get the currently selected company ID.
 * Uses React Query for caching and automatic refetching.
 */
export function useCalendarEvents(
  options: UseCalendarEventsOptions = {}
) {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const { status, startDate, endDate } = options;

  return useQuery({
    queryKey: queryKeys.calendar.filtered(selectedCompanyId || '', status, startDate, endDate),
    queryFn: async (): Promise<CalendarEvent[]> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      if (!selectedCompanyId) {
        throw new Error('Company ID is required');
      }

      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const queryString = params.toString();
      const url = `${API_BASE_URL}/admin/company/${selectedCompanyId}/calendar-events${queryString ? `?${queryString}` : ''}`;

      const response = await apiFetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al cargar eventos del calendario');
      }

      return response.json();
    },
    enabled: !!session?.access_token && !!selectedCompanyId,
    staleTime: 2 * 60 * 1000, // 2 minutes (events can change frequently)
    refetchOnWindowFocus: true, // Calendar events change frequently, keep in sync
  });
}
