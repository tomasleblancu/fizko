import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { useCompanyContext } from "@/app/providers/CompanyContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

interface EventTemplateConfig {
  event_template_id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  authority: string;
  is_mandatory: boolean;
  default_recurrence: {
    frequency: string;
    day_of_month?: number;
    month_of_year?: number;
  };
  is_active: boolean;
  company_event_id: string | null;
  custom_config: any;
}

interface CalendarConfigData {
  company_id: string;
  company_name: string;
  event_templates: EventTemplateConfig[];
  total_available: number;
  total_active: number;
}

/**
 * Hook to fetch calendar configuration for the selected company.
 * Uses CompanyContext to get the currently selected company ID.
 * Uses React Query for caching and automatic refetching.
 */
export function useCalendarConfig() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();

  return useQuery({
    queryKey: ['admin', 'calendar-config', selectedCompanyId],
    queryFn: async (): Promise<CalendarConfigData> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      if (!selectedCompanyId) {
        throw new Error('Company ID is required');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${selectedCompanyId}/calendar-config`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Error al cargar configuración');
      }

      return response.json();
    },
    enabled: !!session?.access_token && !!selectedCompanyId,
    staleTime: 3 * 60 * 1000, // 3 minutes
  });
}

/**
 * Hook to toggle event template activation for the selected company.
 * Uses CompanyContext to get the currently selected company ID.
 * Uses optimistic updates for instant UI feedback.
 */
export function useToggleEventTemplate() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      eventTemplateId,
      isActive,
    }: {
      eventTemplateId: string;
      isActive: boolean;
    }) => {
      if (!session?.access_token || !selectedCompanyId) {
        throw new Error('Missing session or company ID');
      }

      const endpoint = isActive ? 'deactivate' : 'activate';
      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${selectedCompanyId}/calendar-config/${endpoint}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ event_template_id: eventTemplateId }),
        }
      );

      if (!response.ok) {
        throw new Error('Error al actualizar evento');
      }

      return response.json();
    },
    // Optimistic update: update UI immediately before API responds
    onMutate: async ({ eventTemplateId, isActive }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ['admin', 'calendar-config', selectedCompanyId],
      });

      // Snapshot the previous value
      const previousConfig = queryClient.getQueryData<CalendarConfigData>([
        'admin',
        'calendar-config',
        selectedCompanyId,
      ]);

      // Optimistically update to the new value
      if (previousConfig) {
        queryClient.setQueryData<CalendarConfigData>(
          ['admin', 'calendar-config', selectedCompanyId],
          {
            ...previousConfig,
            event_templates: previousConfig.event_templates.map((template) =>
              template.event_template_id === eventTemplateId
                ? { ...template, is_active: !isActive }
                : template
            ),
            total_active: isActive
              ? previousConfig.total_active - 1
              : previousConfig.total_active + 1,
          }
        );
      }

      // Return context with the previous value
      return { previousConfig };
    },
    // If mutation fails, roll back to the previous value
    onError: (_err, _variables, context) => {
      if (context?.previousConfig) {
        queryClient.setQueryData(
          ['admin', 'calendar-config', selectedCompanyId],
          context.previousConfig
        );
      }
    },
    // On success, update cache with server response (no refetch needed)
    onSuccess: (serverResponse, { eventTemplateId }) => {
      // Update cache with confirmed server state
      const currentConfig = queryClient.getQueryData<CalendarConfigData>([
        'admin',
        'calendar-config',
        selectedCompanyId,
      ]);

      if (currentConfig) {
        // Server has confirmed the change, update with server data
        queryClient.setQueryData<CalendarConfigData>(
          ['admin', 'calendar-config', selectedCompanyId],
          {
            ...currentConfig,
            event_templates: currentConfig.event_templates.map((template) =>
              template.event_template_id === eventTemplateId
                ? {
                    ...template,
                    is_active: serverResponse.is_active,
                    company_event_id: serverResponse.company_event_id,
                  }
                : template
            ),
          }
        );
      }
      // No invalidation - we trust our optimistic update + server confirmation
    },
  });
}

/**
 * Hook to sync calendar events for the selected company.
 * Uses CompanyContext to get the currently selected company ID.
 */
export function useSyncCalendar() {
  const { session } = useAuth();
  const { selectedCompanyId } = useCompanyContext();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (!session?.access_token || !selectedCompanyId) {
        throw new Error('Missing session or company ID');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${selectedCompanyId}/sync-calendar`,
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
        throw new Error(errorData.detail || 'Error al sincronizar calendario');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate both calendar config and events to refetch
      queryClient.invalidateQueries({
        queryKey: ['admin', 'calendar-config', selectedCompanyId],
      });
      queryClient.invalidateQueries({
        queryKey: ['admin', 'calendar-events', selectedCompanyId],
      });
    },
  });
}
