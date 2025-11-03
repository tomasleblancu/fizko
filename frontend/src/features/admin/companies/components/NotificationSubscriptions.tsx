import { useEffect, useState } from 'react';
import { Bell, Check, X, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from "@/shared/lib/config";
import { useAuth } from "@/app/providers/AuthContext";
import { apiFetch } from "@/shared/lib/api-client";

interface NotificationTemplate {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category: string;
  entity_type: string | null;
  is_active: boolean;
}

interface NotificationSubscription {
  id: string;
  notification_template_id: string;
  is_enabled: boolean;
  custom_timing_config: any;
  custom_message_template: string | null;
  created_at: string;
  template: NotificationTemplate;
}

interface NotificationSubscriptionsProps {
  companyId: string;
}

export default function NotificationSubscriptions({ companyId }: NotificationSubscriptionsProps) {
  const { session } = useAuth();
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [subscriptions, setSubscriptions] = useState<NotificationSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchData = async () => {
    if (!session?.access_token) return;

    try {
      setLoading(true);

      // Fetch all templates
      const templatesResponse = await apiFetch(
        `${API_BASE_URL}/notifications/notification-templates`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!templatesResponse.ok) {
        throw new Error('Error al cargar templates');
      }

      const templatesData = await templatesResponse.json();
      setTemplates(templatesData.data || []);

      // Fetch company subscriptions
      const subscriptionsResponse = await apiFetch(
        `${API_BASE_URL}/admin/company/${companyId}/notification-subscriptions`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!subscriptionsResponse.ok) {
        throw new Error('Error al cargar suscripciones');
      }

      const subscriptionsData = await subscriptionsResponse.json();
      setSubscriptions(subscriptionsData.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [companyId, session?.access_token]);

  const toggleSubscription = async (templateId: string, currentlyEnabled: boolean) => {
    if (!session?.access_token) return;

    setUpdating(templateId);
    try {
      const subscription = subscriptions.find(s => s.notification_template_id === templateId);

      if (subscription) {
        // Update existing subscription
        const response = await apiFetch(
          `${API_BASE_URL}/admin/company/${companyId}/notification-subscriptions/${subscription.id}`,
          {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              is_enabled: !currentlyEnabled,
            }),
          }
        );

        if (!response.ok) {
          throw new Error('Error al actualizar suscripción');
        }
      } else {
        // Create new subscription
        const response = await apiFetch(
          `${API_BASE_URL}/admin/company/${companyId}/notification-subscriptions`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              notification_template_id: templateId,
              is_enabled: true,
            }),
          }
        );

        if (!response.ok) {
          throw new Error('Error al crear suscripción');
        }
      }

      // Refresh data
      await fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setUpdating(null);
    }
  };

  const isSubscribed = (templateId: string): boolean => {
    const subscription = subscriptions.find(s => s.notification_template_id === templateId);
    return subscription ? subscription.is_enabled : false;
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
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="text-gray-600 dark:text-gray-400">Cargando notificaciones...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="mb-6 flex items-center space-x-2">
        <Bell className="h-6 w-6 text-blue-600" />
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Suscripciones a Notificaciones
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Gestiona las notificaciones que recibirán los empleados de esta empresa
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {templates.filter(t => t.is_active).map((template) => {
          const subscribed = isSubscribed(template.id);
          const isUpdating = updating === template.id;

          return (
            <div
              key={template.id}
              className="flex items-center justify-between rounded-lg border border-gray-200 p-4 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-750"
            >
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {template.name}
                  </h3>
                  <span className={`rounded-full px-2 py-1 text-xs font-semibold ${getCategoryColor(template.category)}`}>
                    {template.category}
                  </span>
                </div>
                {template.description && (
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {template.description}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                  Código: {template.code}
                </p>
              </div>

              <button
                onClick={() => toggleSubscription(template.id, subscribed)}
                disabled={isUpdating}
                className={`ml-4 flex items-center space-x-2 rounded-lg px-4 py-2 font-medium transition-colors ${
                  subscribed
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isUpdating ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Actualizando...</span>
                  </>
                ) : subscribed ? (
                  <>
                    <Check className="h-4 w-4" />
                    <span>Suscrito</span>
                  </>
                ) : (
                  <>
                    <X className="h-4 w-4" />
                    <span>No suscrito</span>
                  </>
                )}
              </button>
            </div>
          );
        })}

        {templates.filter(t => t.is_active).length === 0 && (
          <div className="py-12 text-center">
            <Bell className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              No hay templates de notificaciones disponibles
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
