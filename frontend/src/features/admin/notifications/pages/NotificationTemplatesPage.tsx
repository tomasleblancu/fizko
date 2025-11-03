/**
 * NotificationTemplatesPage
 *
 * Admin page for managing notification templates
 * Refactored to use modular components and hooks
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  Plus,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  X,
  AlertTriangle,
  Trash2,
} from 'lucide-react';
import { useAuth } from '@/app/providers/AuthContext';
import { useTemplateVariables, useNotificationTemplates } from '../hooks';
import { TemplateCard, TemplateForm } from '../components/templates';
import { NotificationTemplate, CreateNotificationTemplateForm, INITIAL_FORM_DATA } from '../types';

export default function AdminNotificationTemplates() {
  const navigate = useNavigate();
  const { session } = useAuth();

  // State for modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<NotificationTemplate | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [formData, setFormData] = useState<CreateNotificationTemplateForm>(INITIAL_FORM_DATA);

  // Use custom hooks
  const {
    templates,
    loading,
    error,
    submitting,
    successMessage,
    createTemplate,
    updateTemplate,
    deleteTemplate,
  } = useNotificationTemplates(session?.access_token);

  const { variables, isLoading: loadingVariables } = useTemplateVariables({
    templateCode: formData.is_summary_template ? undefined : formData.code,
    serviceMethod: formData.is_summary_template ? formData.service_method : undefined,
    enabled: showCreateModal || showEditModal,
    accessToken: session?.access_token,
  });

  // Handlers
  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await createTemplate(formData);
    if (success) {
      setShowCreateModal(false);
      setFormData(INITIAL_FORM_DATA);
    }
  };

  const handleEditClick = (template: NotificationTemplate) => {
    setEditingTemplate(template);

    // Extract summary_config from metadata if it exists
    const summaryConfig = template.metadata?.summary_config;
    const hasSummaryConfig = !!summaryConfig;

    setFormData({
      code: template.code,
      name: template.name,
      description: template.description || '',
      category: template.category,
      entity_type: template.entity_type || '',
      message_template: template.message_template,
      timing_type: template.timing_config.type,
      offset_days: template.timing_config.offset_days?.toString() || '0',
      timing_time: template.timing_config.time || '09:00',
      priority: template.priority,
      is_active: template.is_active,
      auto_assign_to_new_companies: template.auto_assign_to_new_companies || false,
      // Summary config fields
      is_summary_template: hasSummaryConfig,
      service_method: summaryConfig?.service_method || 'get_daily_summary',
      lookback_days: summaryConfig?.lookback_days?.toString() || '1',
      date_offset: summaryConfig?.date_offset?.toString() || '-1',
    });
    setShowEditModal(true);
  };

  const handleUpdateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTemplate) return;

    const success = await updateTemplate(editingTemplate.id, formData);
    if (success) {
      setShowEditModal(false);
      setEditingTemplate(null);
      setFormData(INITIAL_FORM_DATA);
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    const success = await deleteTemplate(templateId);
    if (success) {
      setDeleteConfirm(null);
    }
  };

  const handleCancelModal = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setEditingTemplate(null);
    setFormData(INITIAL_FORM_DATA);
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Stats
  const activeCount = templates.filter((t) => t.is_active).length;
  const inactiveCount = templates.length - activeCount;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/admin')}
                className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
              <div className="flex items-center gap-3">
                <Bell className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Templates de Notificaciones
                  </h1>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Catálogo global de templates de notificaciones por WhatsApp
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Crear Template
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Success Message */}
        {successMessage && (
          <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-900/20">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
              <p className="text-sm text-green-700 dark:text-green-400">{successMessage}</p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-900/20">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          </div>
        )}

        {/* Info Banner */}
        <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-900/20">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-blue-600 dark:text-blue-400" />
            <div>
              <h3 className="font-medium text-blue-900 dark:text-blue-200">
                Templates Globales de Notificaciones
              </h3>
              <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                Estos son los templates de notificaciones disponibles para el sistema. Las empresas
                pueden suscribirse a las notificaciones que deseen recibir. Usa variables como{' '}
                {'{'}
                {'{'}event_title{'}'}
                {'}'}, {'{'}
                {'{'}due_date{'}'}
                {'}'} en los mensajes.
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Total de Templates
            </p>
            <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
              {templates.length}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Activos</p>
            <p className="mt-2 text-3xl font-bold text-green-600 dark:text-green-400">
              {activeCount}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Inactivos</p>
            <p className="mt-2 text-3xl font-bold text-gray-600 dark:text-gray-400">
              {inactiveCount}
            </p>
          </div>
        </div>

        {/* Templates List */}
        <div className="space-y-4">
          {templates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onEdit={handleEditClick}
              onDelete={setDeleteConfirm}
            />
          ))}
        </div>

        {/* Empty State */}
        {templates.length === 0 && !loading && (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
            <Bell className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
              No hay templates de notificaciones
            </h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Crea el primer template usando el botón "Crear Template" arriba.
            </p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Crear Nuevo Template de Notificación
              </h2>
              <button
                onClick={handleCancelModal}
                className="rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            <TemplateForm
              formData={formData}
              onChange={setFormData}
              onSubmit={handleCreateTemplate}
              onCancel={handleCancelModal}
              submitting={submitting}
              submitLabel="Crear Template"
              variables={variables}
              loadingVariables={loadingVariables}
            />
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Editar Template de Notificación
              </h2>
              <button
                onClick={handleCancelModal}
                className="rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            <TemplateForm
              formData={formData}
              onChange={setFormData}
              onSubmit={handleUpdateTemplate}
              onCancel={handleCancelModal}
              submitting={submitting}
              submitLabel="Actualizar Template"
              variables={variables}
              loadingVariables={loadingVariables}
            />
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-6 dark:bg-gray-800">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
                <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Confirmar Eliminación
              </h2>
            </div>

            <p className="mb-6 text-gray-600 dark:text-gray-400">
              ¿Estás seguro de que deseas eliminar este template? Esta acción no se puede deshacer.
              Si hay suscripciones activas a este template, no podrás eliminarlo.
            </p>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                disabled={submitting}
                className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                Cancelar
              </button>
              <button
                onClick={() => handleDeleteTemplate(deleteConfirm)}
                disabled={submitting}
                className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:bg-gray-400"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Eliminando...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Eliminar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
