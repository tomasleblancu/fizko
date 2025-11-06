/**
 * TemplateForm Component
 *
 * Reusable form for creating and editing notification templates
 */

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { CreateNotificationTemplateForm } from '../../types';
import { TemplateVariablesPanel } from '../TemplateVariablesPanel';
import { API_BASE_URL } from '@/shared/lib/config';
import { apiFetch } from '@/shared/lib/api-client';
import { useAuth } from '@/app/providers/AuthContext';

interface TemplateFormProps {
  formData: CreateNotificationTemplateForm;
  onChange: (data: CreateNotificationTemplateForm) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  submitting: boolean;
  submitLabel: string;
  variables?: any;
  loadingVariables?: boolean;
}

export function TemplateForm({
  formData,
  onChange,
  onSubmit,
  onCancel,
  submitting,
  submitLabel,
  variables,
  loadingVariables,
}: TemplateFormProps) {
  const { session } = useAuth();
  const [syncing, setSyncing] = useState(false);

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {/* Code and Name */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Código *
          </label>
          <input
            type="text"
            required
            value={formData.code}
            onChange={(e) => onChange({ ...formData, code: e.target.value })}
            placeholder="ej: custom_reminder"
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Nombre *
          </label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => onChange({ ...formData, name: e.target.value })}
            placeholder="ej: Recordatorio Personalizado"
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Descripción
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => onChange({ ...formData, description: e.target.value })}
          rows={2}
          placeholder="Describe el propósito de esta notificación..."
          className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        />
      </div>

      {/* Category and Entity Type */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Categoría *
          </label>
          <select
            required
            value={formData.category}
            onChange={(e) => onChange({ ...formData, category: e.target.value })}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="calendar">Calendario</option>
            <option value="tax_document">Documento Tributario</option>
            <option value="payroll">Remuneraciones</option>
            <option value="system">Sistema</option>
            <option value="custom">Personalizado</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Tipo de Entidad
          </label>
          <input
            type="text"
            value={formData.entity_type}
            onChange={(e) => onChange({ ...formData, entity_type: e.target.value })}
            placeholder="ej: calendar_event, form29"
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
        </div>
      </div>

      {/* Message Template */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Mensaje *
        </label>
        <textarea
          required
          value={formData.message_template}
          onChange={(e) => onChange({ ...formData, message_template: e.target.value })}
          rows={4}
          placeholder="ej: Hola! Te recordamos que {{event_title}} vence el {{due_date}}."
          className="mt-1 block w-full rounded-lg border px-3 py-2 font-mono text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        />

        {/* Template Variables Panel */}
        <TemplateVariablesPanel
            templateCode={formData.is_summary_template ? undefined : formData.code}
            serviceMethod={formData.is_summary_template ? formData.service_method : undefined}
            variables={variables}
            isLoading={loadingVariables}
          />
      </div>

      {/* Timing Configuration */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Tipo de Timing *
          </label>
          <select
            required
            value={formData.timing_type}
            onChange={(e) => onChange({ ...formData, timing_type: e.target.value })}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="relative">Relativo</option>
            <option value="absolute">Absoluto</option>
            <option value="immediate">Inmediato</option>
          </select>
        </div>

        {formData.timing_type === 'relative' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Días Offset
            </label>
            <input
              type="number"
              value={formData.offset_days}
              onChange={(e) => onChange({ ...formData, offset_days: e.target.value })}
              placeholder="-1 (antes), 0 (mismo día), 1 (después)"
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
          </div>
        )}

        {formData.timing_type !== 'immediate' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Hora
            </label>
            <input
              type="time"
              value={formData.timing_time}
              onChange={(e) => onChange({ ...formData, timing_time: e.target.value })}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
          </div>
        )}
      </div>

      {/* Priority */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Prioridad *
        </label>
        <select
          required
          value={formData.priority}
          onChange={(e) => onChange({ ...formData, priority: e.target.value })}
          className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        >
          <option value="low">Baja</option>
          <option value="normal">Normal</option>
          <option value="high">Alta</option>
          <option value="urgent">Urgente</option>
        </select>
      </div>

      {/* Checkboxes */}
      <div className="space-y-3">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => onChange({ ...formData, is_active: e.target.checked })}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label
            htmlFor="is_active"
            className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Template activo
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="auto_assign"
            checked={formData.auto_assign_to_new_companies}
            onChange={(e) =>
              onChange({ ...formData, auto_assign_to_new_companies: e.target.checked })
            }
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label
            htmlFor="auto_assign"
            className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Asignar automáticamente a nuevas empresas
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_summary_template"
            checked={formData.is_summary_template}
            onChange={(e) => onChange({ ...formData, is_summary_template: e.target.checked })}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label
            htmlFor="is_summary_template"
            className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Es template de resumen de negocio
          </label>
        </div>

      </div>

      {/* Business Summary Configuration (conditional) */}
      {formData.is_summary_template && (
        <details className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-950" open>
          <summary className="cursor-pointer font-medium text-blue-900 dark:text-blue-100 mb-4">
            ⚙️ Configuración de Resumen de Negocio
          </summary>

          <div className="space-y-4 mt-4">
            <div className="rounded-md bg-blue-100 dark:bg-blue-900 p-3">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                💡 Esta configuración se guardará en el campo <code className="bg-blue-200 dark:bg-blue-800 px-1 rounded">metadata.summary_config</code> y será utilizada por la tarea genérica <code className="bg-blue-200 dark:bg-blue-800 px-1 rounded">process_template_notification</code>.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Service Method *
                <span className="text-xs text-gray-500 ml-2">Método del BusinessSummaryService</span>
              </label>
              <select
                value={formData.service_method}
                onChange={(e) => onChange({ ...formData, service_method: e.target.value })}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
              >
                <option value="get_daily_summary">get_daily_summary (Resumen Diario)</option>
                <option value="get_weekly_summary">get_weekly_summary (Resumen Semanal)</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Método que se ejecutará en el BusinessSummaryService para generar los datos
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Lookback Days *
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.lookback_days}
                  onChange={(e) => onChange({ ...formData, lookback_days: e.target.value })}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Días hacia atrás desde la fecha objetivo
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Date Offset *
                </label>
                <input
                  type="number"
                  value={formData.date_offset}
                  onChange={(e) => onChange({ ...formData, date_offset: e.target.value })}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Offset desde hoy (-1 = ayer, 0 = hoy)
                </p>
              </div>
            </div>

            <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-3">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                ⏰ <strong>Nota sobre el Timing:</strong> El horario de envío se configura en la <strong>Scheduled Task</strong>, no en el template. Después de crear este template, deberás crear una tarea periódica que lo ejecute.
              </p>
            </div>

            <div className="rounded-md bg-yellow-50 dark:bg-yellow-900 p-3">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <strong>Ejemplo configuración:</strong><br />
                • <strong>Diario</strong>: lookback=1, offset=-1, hora=8:00 → Resumen de ayer a las 8am<br />
                • <strong>Semanal</strong>: lookback=7, offset=-1, hora=9:00 → Resumen últimos 7 días a las 9am
              </p>
            </div>
          </div>
        </details>
      )}

      {/* WhatsApp Template ID (simple) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          📱 WhatsApp Template ID
          <span className="ml-2 text-xs text-gray-500 font-normal">(opcional)</span>
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={formData.whatsapp_template_id}
            onChange={(e) => onChange({ ...formData, whatsapp_template_id: e.target.value })}
            placeholder="ej: daily_business_summary_v2"
            className="flex-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          />
          {formData.whatsapp_template_id && (
            <button
              type="button"
              disabled={syncing || !session?.access_token}
              onClick={async () => {
                if (!session?.access_token) {
                  alert('No hay sesión activa');
                  return;
                }

                try {
                  setSyncing(true);
                  const response = await apiFetch(
                    `${API_BASE_URL}/notifications/notification-templates/sync-whatsapp/${formData.whatsapp_template_id}`,
                    {
                      method: 'POST',
                      headers: {
                        'Authorization': `Bearer ${session.access_token}`,
                        'Content-Type': 'application/json',
                      }
                    }
                  );

                  if (!response.ok) {
                    const error = await response.json();
                    alert(`Error: ${error.detail || 'Failed to sync template'}`);
                    return;
                  }

                  const result = await response.json();
                  const structure = result.data.whatsapp_template_structure;

                  // Update metadata with template structure
                  const currentMetadata = formData.metadata || {};
                  onChange({
                    ...formData,
                    metadata: {
                      ...currentMetadata,
                      whatsapp_template_structure: structure
                    }
                  });

                  alert(`✅ Template sincronizado!\nHeader params: ${structure.header_params.join(', ')}\nBody params: ${structure.body_params.join(', ')}`);
                } catch (error) {
                  console.error('Error syncing template:', error);
                  alert('Error al sincronizar template');
                } finally {
                  setSyncing(false);
                }
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed whitespace-nowrap text-sm font-medium flex items-center gap-2"
            >
              {syncing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Sincronizando...
                </>
              ) : (
                <>
                  🔄 Sincronizar
                </>
              )}
            </button>
          )}
        </div>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          💡 Nombre del template creado manualmente en <strong>Meta Business Manager</strong>. Si se especifica, las notificaciones se enviarán usando este template de WhatsApp. Haz clic en "Sincronizar" para obtener la estructura automáticamente.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-gray-400"
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {submitLabel}...
            </>
          ) : (
            submitLabel
          )}
        </button>
      </div>
    </form>
  );
}
