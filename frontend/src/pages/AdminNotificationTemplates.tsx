import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Plus, Trash2, Edit2, ArrowLeft, Loader2, CheckCircle2, X, AlertTriangle } from 'lucide-react';
import { API_BASE_URL } from '../lib/config';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../lib/api-client';

interface NotificationTemplate {
  id: string;
  code: string;
  name: string;
  description: string;
  category: string;
  entity_type: string | null;
  message_template: string;
  timing_config: {
    type: string;
    offset_days?: number;
    time?: string;
  };
  priority: string;
  is_active: boolean;
  metadata: any;
}

interface CreateNotificationTemplateForm {
  code: string;
  name: string;
  description: string;
  category: string;
  entity_type: string;
  message_template: string;
  timing_type: string;
  offset_days: string;
  timing_time: string;
  priority: string;
  is_active: boolean;
}

export default function AdminNotificationTemplates() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<NotificationTemplate | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [formData, setFormData] = useState<CreateNotificationTemplateForm>({
    code: '',
    name: '',
    description: '',
    category: 'calendar',
    entity_type: '',
    message_template: '',
    timing_type: 'relative',
    offset_days: '-1',
    timing_time: '09:00',
    priority: 'normal',
    is_active: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchTemplates = async () => {
    if (!session?.access_token) return;

    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`${API_BASE_URL}/notifications/notification-templates`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
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
  };

  useEffect(() => {
    fetchTemplates();
  }, [session?.access_token]);

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      calendar: 'Calendario',
      tax_document: 'Documento Tributario',
      payroll: 'Remuneraciones',
      system: 'Sistema',
      custom: 'Personalizado',
    };
    return labels[category] || category;
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      calendar: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      tax_document: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      payroll: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      system: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      custom: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
    };
    return colors[category] || colors.custom;
  };

  const getPriorityLabel = (priority: string) => {
    const labels: Record<string, string> = {
      low: 'Baja',
      normal: 'Normal',
      high: 'Alta',
      urgent: 'Urgente',
    };
    return labels[priority] || priority;
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
      normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      urgent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    };
    return colors[priority] || colors.normal;
  };

  const getTimingDescription = (timing: any) => {
    if (timing.type === 'immediate') return 'Inmediato';
    if (timing.type === 'absolute') {
      return `Hora fija: ${timing.time || 'No definido'}`;
    }
    if (timing.type === 'relative') {
      const days = timing.offset_days || 0;
      const time = timing.time || '09:00';
      if (days === 0) return `El mismo día a las ${time}`;
      if (days < 0) return `${Math.abs(days)} día(s) antes a las ${time}`;
      return `${days} día(s) después a las ${time}`;
    }
    return 'No definido';
  };

  const buildTimingConfig = () => {
    if (formData.timing_type === 'immediate') {
      return { type: 'immediate' };
    }
    if (formData.timing_type === 'absolute') {
      return {
        type: 'absolute',
        time: formData.timing_time,
      };
    }
    // relative
    return {
      type: 'relative',
      offset_days: parseInt(formData.offset_days) || 0,
      time: formData.timing_time,
    };
  };

  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.access_token) return;

    setSubmitting(true);
    setError(null);

    try {
      const timing_config = buildTimingConfig();

      const response = await apiFetch(`${API_BASE_URL}/notifications/notification-templates`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
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
      setShowCreateModal(false);
      setFormData({
        code: '',
        name: '',
        description: '',
        category: 'calendar',
        entity_type: '',
        message_template: '',
        timing_type: 'relative',
        offset_days: '-1',
        timing_time: '09:00',
        priority: 'normal',
        is_active: true,
      });

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear template de notificación');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    if (!session?.access_token) return;

    setSubmitting(true);
    setError(null);

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/notifications/notification-templates/${templateId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar template de notificación');
    } finally {
      setSubmitting(false);
      setDeleteConfirm(null);
    }
  };

  const handleEditClick = (template: NotificationTemplate) => {
    setEditingTemplate(template);
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
    });
    setShowEditModal(true);
  };

  const handleUpdateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.access_token || !editingTemplate) return;

    setSubmitting(true);
    setError(null);

    try {
      const timing_config = buildTimingConfig();

      const response = await apiFetch(
        `${API_BASE_URL}/notifications/notification-templates/${editingTemplate.id}`,
        {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
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
        prevTemplates.map((t) => (t.id === editingTemplate.id ? updatedTemplate : t))
      );
      setSuccessMessage('Template de notificación actualizado exitosamente');
      setShowEditModal(false);
      setEditingTemplate(null);
      setFormData({
        code: '',
        name: '',
        description: '',
        category: 'calendar',
        entity_type: '',
        message_template: '',
        timing_type: 'relative',
        offset_days: '-1',
        timing_time: '09:00',
        priority: 'normal',
        is_active: true,
      });

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar template de notificación');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

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
            <div
              key={template.id}
              className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {template.name}
                    </h3>
                    <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                      {template.code}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1 text-sm font-medium ${getCategoryColor(
                        template.category
                      )}`}
                    >
                      {getCategoryLabel(template.category)}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1 text-sm font-medium ${getPriorityColor(
                        template.priority
                      )}`}
                    >
                      {getPriorityLabel(template.priority)}
                    </span>
                    {!template.is_active && (
                      <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700 dark:bg-gray-900/30 dark:text-gray-400">
                        Inactivo
                      </span>
                    )}
                  </div>

                  <p className="mt-2 text-gray-600 dark:text-gray-400">{template.description}</p>

                  <div className="mt-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-900/50">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Mensaje:
                    </p>
                    <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
                      {template.message_template}
                    </p>
                  </div>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                        Timing
                      </p>
                      <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                        {getTimingDescription(template.timing_config)}
                      </p>
                    </div>

                    {template.entity_type && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Tipo de Entidad
                        </p>
                        <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                          {template.entity_type}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="ml-4 flex gap-2">
                  <button
                    onClick={() => handleEditClick(template)}
                    className="rounded-lg p-2 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
                    title="Editar template"
                  >
                    <Edit2 className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(template.id)}
                    className="rounded-lg p-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                    title="Eliminar template"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

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
                onClick={() => setShowCreateModal(false)}
                className="rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleCreateTemplate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Código *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="ej: Recordatorio Personalizado"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Descripción
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  placeholder="Describe el propósito de esta notificación..."
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Categoría *
                  </label>
                  <select
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                    placeholder="ej: calendar_event, form29"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Mensaje * (usa variables como {'{'}
                  {'{'}variable{'}'}
                  {'}'})
                </label>
                <textarea
                  required
                  value={formData.message_template}
                  onChange={(e) => setFormData({ ...formData, message_template: e.target.value })}
                  rows={3}
                  placeholder="ej: Hola! Te recordamos que {​{event_title}} vence el {​{due_date}}."
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Tipo de Timing *
                  </label>
                  <select
                    required
                    value={formData.timing_type}
                    onChange={(e) => setFormData({ ...formData, timing_type: e.target.value })}
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
                      onChange={(e) => setFormData({ ...formData, offset_days: e.target.value })}
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
                      onChange={(e) => setFormData({ ...formData, timing_time: e.target.value })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Prioridad *
                </label>
                <select
                  required
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                >
                  <option value="low">Baja</option>
                  <option value="normal">Normal</option>
                  <option value="high">Alta</option>
                  <option value="urgent">Urgente</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label
                  htmlFor="is_active"
                  className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Template activo
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
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
                      Creando...
                    </>
                  ) : (
                    'Crear Template'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal - Same structure as Create but with update logic */}
      {showEditModal && editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Editar Template de Notificación
              </h2>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingTemplate(null);
                }}
                className="rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleUpdateTemplate} className="space-y-4">
              {/* Same fields as create form */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Código *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Descripción
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Categoría *
                  </label>
                  <select
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Mensaje *
                </label>
                <textarea
                  required
                  value={formData.message_template}
                  onChange={(e) => setFormData({ ...formData, message_template: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Tipo de Timing *
                  </label>
                  <select
                    required
                    value={formData.timing_type}
                    onChange={(e) => setFormData({ ...formData, timing_type: e.target.value })}
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
                      onChange={(e) => setFormData({ ...formData, offset_days: e.target.value })}
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
                      onChange={(e) => setFormData({ ...formData, timing_time: e.target.value })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Prioridad *
                </label>
                <select
                  required
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                >
                  <option value="low">Baja</option>
                  <option value="normal">Normal</option>
                  <option value="high">Alta</option>
                  <option value="urgent">Urgente</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active_edit"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label
                  htmlFor="is_active_edit"
                  className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Template activo
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingTemplate(null);
                  }}
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
                      Actualizando...
                    </>
                  ) : (
                    'Actualizar Template'
                  )}
                </button>
              </div>
            </form>
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
