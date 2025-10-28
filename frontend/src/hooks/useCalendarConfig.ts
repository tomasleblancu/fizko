import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

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
 * Hook to fetch calendar configuration for a company
 * Uses React Query for caching and automatic refetching
 */
export function useCalendarConfig(companyId: string | undefined) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['admin', 'calendar-config', companyId],
    queryFn: async (): Promise<CalendarConfigData> => {
      if (!session?.access_token) {
        throw new Error('No authenticated session');
      }

      if (!companyId) {
        throw new Error('Company ID is required');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${companyId}/calendar-config`,
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
    enabled: !!session?.access_token && !!companyId,
    staleTime: 3 * 60 * 1000, // 3 minutes
  });
}

/**
 * Hook to toggle event template activation for a company
 * Uses optimistic updates for instant UI feedback
 */
export function useToggleEventTemplate(companyId: string | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      eventTemplateId,
      isActive,
    }: {
      eventTemplateId: string;
      isActive: boolean;
    }) => {
      if (!session?.access_token || !companyId) {
        throw new Error('Missing session or company ID');
      }

      const endpoint = isActive ? 'deactivate' : 'activate';
      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${companyId}/calendar-config/${endpoint}`,
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
        queryKey: ['admin', 'calendar-config', companyId],
      });

      // Snapshot the previous value
      const previousConfig = queryClient.getQueryData<CalendarConfigData>([
        'admin',
        'calendar-config',
        companyId,
      ]);

      // Optimistically update to the new value
      if (previousConfig) {
        queryClient.setQueryData<CalendarConfigData>(
          ['admin', 'calendar-config', companyId],
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
          ['admin', 'calendar-config', companyId],
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
        companyId,
      ]);

      if (currentConfig) {
        // Server has confirmed the change, update with server data
        queryClient.setQueryData<CalendarConfigData>(
          ['admin', 'calendar-config', companyId],
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
 * Hook to sync calendar events for a company
 */
export function useSyncCalendar(companyId: string | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (!session?.access_token || !companyId) {
        throw new Error('Missing session or company ID');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/admin/companies/${companyId}/sync-calendar`,
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
        queryKey: ['admin', 'calendar-config', companyId],
      });
      queryClient.invalidateQueries({
        queryKey: ['admin', 'calendar-events', companyId],
      });
    },
  });
}
