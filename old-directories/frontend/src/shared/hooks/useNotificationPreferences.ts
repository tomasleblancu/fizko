/**
 * useNotificationPreferences Hooks
 *
 * Centralized hooks for managing user notification preferences and company subscriptions.
 * These hooks can be used anywhere in the app and share React Query cache.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from "@/app/providers/AuthContext";
import { API_BASE_URL } from "@/shared/lib/config";
import { apiFetch } from "@/shared/lib/api-client";

// ============================================================================
// Types
// ============================================================================

export interface NotificationTemplate {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category: string;
}

export interface CompanySubscription {
  template: NotificationTemplate;
  is_enabled: boolean;
}

export interface UserNotificationPreferences {
  notifications_enabled: boolean;
  muted_templates: string[];
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Hook to fetch company notification subscriptions
 *
 * @param companyId - Company UUID
 * @returns Query result with enabled subscriptions
 *
 * @example
 * ```typescript
 * const { data: subscriptions, isLoading } = useCompanySubscriptions(companyId);
 * ```
 */
export function useCompanySubscriptions(companyId: string | null | undefined) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['company-subscriptions', companyId],
    queryFn: async (): Promise<CompanySubscription[]> => {
      if (!session?.access_token || !companyId) {
        return [];
      }

      const response = await apiFetch(
        `${API_BASE_URL}/notifications/company/${companyId}/notification-subscriptions`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Error al cargar suscripciones de la empresa');
      }

      const data = await response.json();
      // Filter only enabled subscriptions
      return (data.data || []).filter((sub: CompanySubscription) => sub.is_enabled);
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });
}

/**
 * Hook to fetch user notification preferences
 *
 * @param companyId - Company UUID
 * @returns Query result with user preferences
 *
 * @example
 * ```typescript
 * const { data: preferences, isLoading } = useUserNotificationPreferences(companyId);
 * ```
 */
export function useUserNotificationPreferences(companyId: string | null | undefined) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['user-notification-preferences', companyId],
    queryFn: async (): Promise<UserNotificationPreferences | null> => {
      if (!session?.access_token || !companyId) {
        return null;
      }

      const response = await apiFetch(
        `${API_BASE_URL}/user/notification-preferences?company_id=${companyId}`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Error al cargar preferencias del usuario');
      }

      const data = await response.json();
      return data.data;
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook to toggle global notification settings
 *
 * @param companyId - Company UUID
 * @returns Mutation for toggling global notifications
 *
 * @example
 * ```typescript
 * const toggleGlobal = useToggleGlobalNotifications(companyId);
 * await toggleGlobal.mutateAsync(true); // Enable notifications
 * ```
 */
export function useToggleGlobalNotifications(companyId: string | null | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (enabled: boolean) => {
      if (!session?.access_token || !companyId) {
        throw new Error('No estás autenticado o no se especificó la empresa');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/user/notification-preferences`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            company_id: companyId,
            notifications_enabled: enabled,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Error al actualizar preferencias');
      }

      return enabled;
    },
    onMutate: async (enabled) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ['user-notification-preferences', companyId] });

      // Snapshot previous value
      const previousPrefs = queryClient.getQueryData(['user-notification-preferences', companyId]);

      // Optimistically update
      queryClient.setQueryData(['user-notification-preferences', companyId], (old: any) => ({
        ...old,
        notifications_enabled: enabled,
      }));

      return { previousPrefs };
    },
    onError: (err, _enabled, context) => {
      // Rollback on error silently
      queryClient.setQueryData(['user-notification-preferences', companyId], context?.previousPrefs);
      console.error('Error updating notification preferences:', err);
    },
  });
}

/**
 * Hook to toggle individual notification template
 *
 * @param companyId - Company UUID
 * @returns Mutation for toggling template notifications
 *
 * @example
 * ```typescript
 * const toggleTemplate = useToggleTemplateNotification(companyId);
 * await toggleTemplate.mutateAsync({
 *   newMutedTemplates: ['template-id-1', 'template-id-2'],
 *   templateName: 'F29 Reminder',
 *   isMuting: true
 * });
 * ```
 */
export function useToggleTemplateNotification(companyId: string | null | undefined) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { newMutedTemplates: string[]; templateName: string; isMuting: boolean }) => {
      if (!session?.access_token || !companyId) {
        throw new Error('No estás autenticado o no se especificó la empresa');
      }

      const response = await apiFetch(
        `${API_BASE_URL}/user/notification-preferences`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            company_id: companyId,
            muted_templates: payload.newMutedTemplates,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Error al actualizar preferencias');
      }

      return payload;
    },
    onMutate: async (payload) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ['user-notification-preferences', companyId] });

      // Snapshot previous value
      const previousPrefs = queryClient.getQueryData(['user-notification-preferences', companyId]);

      // Optimistically update
      queryClient.setQueryData(['user-notification-preferences', companyId], (old: any) => ({
        ...old,
        muted_templates: payload.newMutedTemplates,
      }));

      return { previousPrefs };
    },
    onError: (err, _payload, context) => {
      // Rollback on error silently
      queryClient.setQueryData(['user-notification-preferences', companyId], context?.previousPrefs);
      console.error('Error updating notification template preferences:', err);
    },
  });
}
