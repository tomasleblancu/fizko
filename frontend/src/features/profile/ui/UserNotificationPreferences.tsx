import { Bell, Check, X, AlertCircle, BellOff } from 'lucide-react';
import { API_BASE_URL } from "@/shared/lib/config";
import { useAuth } from "@/app/providers/AuthContext";
import { apiFetch } from "@/shared/lib/api-client";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface NotificationTemplate {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category: string;
}

interface CompanySubscription {
  template: NotificationTemplate;
}

interface UserNotificationPreferencesProps {
  companyId: string;
  isInDrawer?: boolean;
}

export function UserNotificationPreferences({ companyId, isInDrawer = false }: UserNotificationPreferencesProps) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  // Fetch company subscriptions with React Query
  const { data: subscriptionsData, isLoading: loadingSubscriptions } = useQuery({
    queryKey: ['company-subscriptions', companyId],
    queryFn: async () => {
      const response = await apiFetch(
        `${API_BASE_URL}/admin/company/${companyId}/notification-subscriptions`,
        {
          headers: {
            'Authorization': `Bearer ${session?.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Error al cargar suscripciones de la empresa');
      }

      const data = await response.json();
      // Filter only enabled subscriptions
      return (data.data || []).filter((sub: any) => sub.is_enabled);
    },
    enabled: !!session?.access_token && !!companyId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });

  // Fetch user preferences with React Query
  const { data: preferencesData, isLoading: loadingPreferences, error } = useQuery({
    queryKey: ['user-notification-preferences', companyId],
    queryFn: async () => {
      const response = await apiFetch(
        `${API_BASE_URL}/user/notification-preferences?company_id=${companyId}`,
        {
          headers: {
            'Authorization': `Bearer ${session?.access_token}`,
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

  const companySubscriptions = subscriptionsData || [];
  const notificationsEnabled = preferencesData?.notifications_enabled ?? true;
  const mutedTemplates = preferencesData?.muted_templates || [];
  const loading = loadingSubscriptions || loadingPreferences;

  // Mutation for updating global notifications
  const toggleGlobalMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const response = await apiFetch(
        `${API_BASE_URL}/user/notification-preferences`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${session?.access_token}`,
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

  // Mutation for updating muted templates
  const toggleTemplateMutation = useMutation({
    mutationFn: async (payload: { newMutedTemplates: string[]; templateName: string; isMuting: boolean }) => {
      const response = await apiFetch(
        `${API_BASE_URL}/user/notification-preferences`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${session?.access_token}`,
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

  const toggleGlobalNotifications = () => {
    if (!session?.access_token) return;
    toggleGlobalMutation.mutate(!notificationsEnabled);
  };

  const toggleTemplateNotification = (templateId: string, templateName: string, currentlyMuted: boolean) => {
    if (!session?.access_token) return;
    if (!notificationsEnabled) return; // Can't change individual settings if all are disabled

    const newMutedTemplates = currentlyMuted
      ? mutedTemplates.filter(id => id !== templateId)
      : [...mutedTemplates, templateId];

    toggleTemplateMutation.mutate({
      newMutedTemplates,
      templateName,
      isMuting: !currentlyMuted,
    });
  };

  const isTemplateMuted = (templateId: string): boolean => {
    return mutedTemplates.includes(templateId);
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      calendar: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      tax_document: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      payroll: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
      system: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400',
      custom: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
    };
    return colors[category] || colors.system;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="mb-2 inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-emerald-600 border-r-transparent"></div>
          <p className="text-xs text-slate-600 dark:text-slate-400">Cargando notificaciones...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20">
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <p className="text-xs text-red-800 dark:text-red-200">
            {error instanceof Error ? error.message : 'Error al cargar notificaciones'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={isInDrawer ? "space-y-0 divide-y divide-slate-200/50 dark:divide-slate-700/50" : "space-y-3"}>
      {/* Global Toggle */}
      <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {notificationsEnabled ? (
              <Bell className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <BellOff className="h-5 w-5 text-slate-400" />
            )}
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Notificaciones WhatsApp
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {notificationsEnabled ? 'Activadas' : 'Desactivadas'}
              </p>
            </div>
          </div>
          <button
            onClick={toggleGlobalNotifications}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
              notificationsEnabled
                ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                : 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'
            }`}
          >
            {notificationsEnabled ? 'Activadas' : 'Desactivadas'}
          </button>
        </div>
      </div>

      {/* Individual Notifications */}
      {companySubscriptions.length > 0 ? (
        <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
          <h4 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
            Notificaciones Disponibles
          </h4>
          <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
            Personaliza qué notificaciones quieres recibir de tu empresa
          </p>

          <div className="space-y-2">
            {companySubscriptions.map(({ template }) => {
              const isMuted = isTemplateMuted(template.id);
              const isDisabled = !notificationsEnabled;

              return (
                <div
                  key={template.id}
                  className={`flex items-center justify-between rounded-lg border p-2.5 transition-colors ${
                    isDisabled
                      ? 'border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/50'
                      : 'border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h5 className={`text-xs font-medium truncate ${
                        isDisabled ? 'text-slate-400' : 'text-slate-900 dark:text-slate-100'
                      }`}>
                        {template.name}
                      </h5>
                      <span className={`flex-shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${getCategoryColor(template.category)}`}>
                        {template.category}
                      </span>
                    </div>
                    {template.description && (
                      <p className={`mt-0.5 text-[10px] truncate ${
                        isDisabled ? 'text-slate-400' : 'text-slate-600 dark:text-slate-400'
                      }`}>
                        {template.description}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() => toggleTemplateNotification(template.id, template.name, isMuted)}
                    disabled={isDisabled}
                    className={`ml-3 flex items-center space-x-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                      !notificationsEnabled
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed dark:bg-slate-800'
                        : isMuted
                        ? 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'
                        : 'bg-emerald-600 text-white hover:bg-emerald-700'
                    } disabled:opacity-50`}
                  >
                    {isMuted ? (
                      <>
                        <X className="h-3 w-3" />
                        <span>Silenciada</span>
                      </>
                    ) : (
                      <>
                        <Check className="h-3 w-3" />
                        <span>Activa</span>
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>

          {!notificationsEnabled && (
            <div className="mt-3 rounded-lg bg-amber-50 p-2 dark:bg-amber-950/30">
              <p className="text-xs text-amber-800 dark:text-amber-200">
                Activa las notificaciones globales para poder gestionar notificaciones individuales
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className={isInDrawer ? "py-4" : "rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"}>
          <div className="text-center py-6">
            <Bell className="mx-auto h-8 w-8 text-slate-400" />
            <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
              Tu empresa no está suscrita a ninguna notificación
            </p>
            <p className="mt-1 text-[10px] text-slate-500 dark:text-slate-500">
              Contacta al administrador para activar notificaciones
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
