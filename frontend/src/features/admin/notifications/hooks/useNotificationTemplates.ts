/**
 * useNotificationTemplates Hook
 *
 * Custom hook for managing notification templates
 * Handles fetching, creating, updating, and deleting templates
 */

import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '@/shared/lib/config';
import { apiFetch } from '@/shared/lib/api-client';
import { NotificationTemplate, CreateNotificationTemplateForm, INITIAL_FORM_DATA } from '../types';
import { buildTimingConfig } from '../utils';

interface UseNotificationTemplatesReturn {
  // State
  templates: NotificationTemplate[];
  loading: boolean;
  error: string | null;
  submitting: boolean;
  successMessage: string | null;

  // Actions
  fetchTemplates: () => Promise<void>;
  createTemplate: (formData: CreateNotificationTemplateForm) => Promise<boolean>;
  updateTemplate: (templateId: string, formData: CreateNotificationTemplateForm) => Promise<boolean>;
  deleteTemplate: (templateId: string) => Promise<boolean>;
  clearMessages: () => void;
}

export function useNotificationTemplates(
  accessToken: string | undefined
): UseNotificationTemplatesReturn {
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch all templates
  const fetchTemplates = useCallback(async () => {
    if (!accessToken) return;

    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`${API_BASE_URL}/notifications/notification-templates`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al cargar templates de notificaciones');
      }

      const data = await response.json();
      setTemplates(data.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  // Initial fetch
  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  // Create template
  const createTemplate = useCallback(
    async (formData: CreateNotificationTemplateForm): Promise<boolean> => {
      if (!accessToken) return false;

      setSubmitting(true);
      setError(null);

      try {
        const timing_config = buildTimingConfig(
          formData.timing_type,
          formData.offset_days,
          formData.timing_time
        );

        // Build metadata with summary_config if applicable
        const metadata: any = {};
        if (formData.is_summary_template) {
          metadata.summary_config = {
            service_method: formData.service_method,
            lookback_days: parseInt(formData.lookback_days, 10),
            date_offset: parseInt(formData.date_offset, 10),
          };
        }

        const response = await apiFetch(`${API_BASE_URL}/notifications/notification-templates`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code: formData.code,
            name: formData.name,
            description: formData.description,
            category: formData.category,
            entity_type: formData.entity_type || null,
            message_template: formData.message_template,
            timing_config,
            priority: formData.priority,
            is_active: formData.is_active,
            auto_assign_to_new_companies: formData.auto_assign_to_new_companies,
            metadata: Object.keys(metadata).length > 0 ? metadata : null,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al crear template de notificación');
        }

        const result = await response.json();
        const newTemplate = result.data;

        // Optimistic update
        setTemplates((prevTemplates) => [...prevTemplates, newTemplate]);
        setSuccessMessage('Template de notificación creado exitosamente');

        setTimeout(() => setSuccessMessage(null), 3000);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al crear template de notificación');
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [accessToken]
  );

  // Update template
  const updateTemplate = useCallback(
    async (templateId: string, formData: CreateNotificationTemplateForm): Promise<boolean> => {
      if (!accessToken) return false;

      setSubmitting(true);
      setError(null);

      try {
        const timing_config = buildTimingConfig(
          formData.timing_type,
          formData.offset_days,
          formData.timing_time
        );

        // Build metadata with summary_config if applicable
        const metadata: any = {};
        if (formData.is_summary_template) {
          metadata.summary_config = {
            service_method: formData.service_method,
            lookback_days: parseInt(formData.lookback_days, 10),
            date_offset: parseInt(formData.date_offset, 10),
          };
        }

        const response = await apiFetch(
          `${API_BASE_URL}/notifications/notification-templates/${templateId}`,
          {
            method: 'PUT',
            headers: {
              Authorization: `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              code: formData.code,
              name: formData.name,
              description: formData.description,
              category: formData.category,
              entity_type: formData.entity_type || null,
              message_template: formData.message_template,
              timing_config,
              priority: formData.priority,
              is_active: formData.is_active,
              auto_assign_to_new_companies: formData.auto_assign_to_new_companies,
              metadata: Object.keys(metadata).length > 0 ? metadata : null,
            }),
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al actualizar template de notificación');
        }

        const result = await response.json();
        const updatedTemplate = result.data;

        // Optimistic update
        setTemplates((prevTemplates) =>
          prevTemplates.map((t) => (t.id === templateId ? updatedTemplate : t))
        );
        setSuccessMessage('Template de notificación actualizado exitosamente');

        setTimeout(() => setSuccessMessage(null), 3000);
        return true;
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Error al actualizar template de notificación'
        );
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [accessToken]
  );

  // Delete template
  const deleteTemplate = useCallback(
    async (templateId: string): Promise<boolean> => {
      if (!accessToken) return false;

      setSubmitting(true);
      setError(null);

      try {
        const response = await apiFetch(
          `${API_BASE_URL}/notifications/notification-templates/${templateId}`,
          {
            method: 'DELETE',
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al eliminar template de notificación');
        }

        // Optimistic update
        setTemplates((prevTemplates) => prevTemplates.filter((t) => t.id !== templateId));
        setSuccessMessage('Template de notificación eliminado exitosamente');

        setTimeout(() => setSuccessMessage(null), 3000);
        return true;
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Error al eliminar template de notificación'
        );
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [accessToken]
  );

  // Clear messages
  const clearMessages = useCallback(() => {
    setError(null);
    setSuccessMessage(null);
  }, []);

  return {
    templates,
    loading,
    error,
    submitting,
    successMessage,
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    clearMessages,
  };
}
