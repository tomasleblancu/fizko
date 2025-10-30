import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Plus, Trash2, Edit2, ArrowLeft, Loader2, CheckCircle2, X, AlertTriangle } from 'lucide-react';
import { API_BASE_URL } from "@/shared/lib/config";
import { useAuth } from "@/app/providers/AuthContext";
import { apiFetch } from "@/shared/lib/api-client";

interface EventTemplate {
  id: string;
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
    business_days_adjustment?: string;
  };
  metadata: any;
  created_at: string;
  updated_at: string;
}

interface CreateEventTemplateForm {
  code: string;
  name: string;
  description: string;
  category: string;
  authority: string;
  is_mandatory: boolean;
  frequency: string;
  day_of_month: string;
  month_of_year: string;
}

export default function AdminEventTemplates() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [eventTemplates, setEventTemplates] = useState<EventTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState<EventTemplate | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [formData, setFormData] = useState<CreateEventTemplateForm>({
    code: '',
    name: '',
    description: '',
    category: 'impuesto_mensual',
    authority: 'SII',
    is_mandatory: true,
    frequency: 'monthly',
    day_of_month: '12',
    month_of_year: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchEventTemplates = async () => {
    if (!session?.access_token) return;

    try {
      setLoading(true);
      setError(null);
      const response = await apiFetch(`${API_BASE_URL}/calendar/event-templates`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al cargar tipos de eventos');
      }

      const data = await response.json();
      setEventTemplates(data.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEventTemplates();
  }, [session?.access_token]);

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      impuesto_mensual: 'Impuesto Mensual',
      impuesto_anual: 'Impuesto Anual',
      prevision: 'Previsión',
      declaracion_jurada: 'Declaración Jurada',
      libros: 'Libros Contables',
      otros: 'Otros',
    };
    return labels[category] || category;
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      impuesto_mensual: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      impuesto_anual: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      prevision: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      declaracion_jurada: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      libros: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
      otros: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
    };
    return colors[category] || colors.otros;
  };

  const getFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      monthly: 'Mensual',
      quarterly: 'Trimestral',
      annual: 'Anual',
      biannual: 'Semestral',
    };
    return labels[frequency] || frequency;
  };

  const handleCreateEventTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.access_token) return;

    setSubmitting(true);
    setError(null);

    try {
      const default_recurrence: any = {
        frequency: formData.frequency,
        business_days_adjustment: 'after',
      };

      if (formData.day_of_month) {
        default_recurrence.day_of_month = parseInt(formData.day_of_month);
      }

      if (formData.month_of_year) {
        default_recurrence.month_of_year = parseInt(formData.month_of_year);
      }

      const response = await apiFetch(`${API_BASE_URL}/calendar/event-templates`, {
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
          authority: formData.authority,
          is_mandatory: formData.is_mandatory,
          default_recurrence,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear tipo de evento');
      }

      const result = await response.json();
      const newEventTemplate = result.data;

      // Optimistic update: agregar el nuevo evento a la lista local sin recargar
      setEventTemplates((prevEvents) => [...prevEvents, newEventTemplate]);
      setSuccessMessage('Tipo de evento creado exitosamente');
      setShowCreateModal(false);
      setFormData({
        code: '',
        name: '',
        description: '',
        category: 'impuesto_mensual',
        authority: 'SII',
        is_mandatory: true,
        frequency: 'monthly',
        day_of_month: '12',
        month_of_year: '',
      });

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear tipo de evento');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteEventTemplate = async (eventTypeId: string) => {
    if (!session?.access_token) return;

    setSubmitting(true);
    setError(null);

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/calendar/event-templates/${eventTypeId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al eliminar tipo de evento');
      }

      // Optimistic update: remover el evento de la lista local sin recargar
      setEventTemplates((prevEvents) => prevEvents.filter((event) => event.id !== eventTypeId));
      setSuccessMessage('Tipo de evento eliminado exitosamente');

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar tipo de evento');
    } finally {
      setSubmitting(false);
      setDeleteConfirm(null); // Siempre cerrar el modal, incluso si hay error
    }
  };

  const handleEditClick = (eventType: EventTemplate) => {
    setEditingEvent(eventType);
    setFormData({
      code: eventType.code,
      name: eventType.name,
      description: eventType.description || '',
      category: eventType.category,
      authority: eventType.authority,
      is_mandatory: eventType.is_mandatory,
      frequency: eventType.default_recurrence.frequency,
      day_of_month: eventType.default_recurrence.day_of_month?.toString() || '',
      month_of_year: eventType.default_recurrence.month_of_year?.toString() || '',
    });
    setShowEditModal(true);
  };

  const handleUpdateEventTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.access_token || !editingEvent) return;

    setSubmitting(true);
    setError(null);

    try {
      const default_recurrence: any = {
        frequency: formData.frequency,
        business_days_adjustment: 'after',
      };

      if (formData.day_of_month) {
        default_recurrence.day_of_month = parseInt(formData.day_of_month);
      }

      if (formData.month_of_year) {
        default_recurrence.month_of_year = parseInt(formData.month_of_year);
      }

      const response = await apiFetch(
        `${API_BASE_URL}/calendar/event-templates/${editingEvent.id}`,
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
            authority: formData.authority,
            is_mandatory: formData.is_mandatory,
            default_recurrence,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al actualizar tipo de evento');
      }

      const result = await response.json();
      const updatedEventTemplate = result.data;

      // Optimistic update: actualizar el evento en la lista local sin recargar
      setEventTemplates((prevEvents) =>
        prevEvents.map((event) => (event.id === editingEvent.id ? updatedEventTemplate : event))
      );
      setSuccessMessage('Tipo de evento actualizado exitosamente');
      setShowEditModal(false);
      setEditingEvent(null);
      setFormData({
        code: '',
        name: '',
        description: '',
        category: 'impuesto_mensual',
        authority: 'SII',
        is_mandatory: true,
        frequency: 'monthly',
        day_of_month: '12',
        month_of_year: '',
      });

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar tipo de evento');
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

  const mandatoryCount = eventTemplates.filter((et) => et.is_mandatory).length;
  const optionalCount = eventTemplates.length - mandatoryCount;

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
                <Calendar className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Tipos de Eventos Tributarios
                  </h1>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Catálogo global de eventos tributarios disponibles
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Crear Evento
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
                Eventos Globales del Sistema
              </h3>
              <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                Estos son los tipos de eventos disponibles para todas las empresas. Las empresas
                pueden activar los eventos que apliquen a su situación tributaria desde su panel
                de configuración.
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Total de Eventos
            </p>
            <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
              {eventTemplates.length}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Obligatorios</p>
            <p className="mt-2 text-3xl font-bold text-red-600 dark:text-red-400">
              {mandatoryCount}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Opcionales</p>
            <p className="mt-2 text-3xl font-bold text-blue-600 dark:text-blue-400">
              {optionalCount}
            </p>
          </div>
        </div>

        {/* Event Types List */}
        <div className="space-y-4">
          {eventTemplates.map((eventType) => (
            <div
              key={eventType.id}
              className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                      {eventType.name}
                    </h3>
                    <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                      {eventType.code}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1 text-sm font-medium ${getCategoryColor(
                        eventType.category
                      )}`}
                    >
                      {getCategoryLabel(eventType.category)}
                    </span>
                    {eventType.is_mandatory && (
                      <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
                        Obligatorio
                      </span>
                    )}
                  </div>

                  <p className="mt-2 text-gray-600 dark:text-gray-400">{eventType.description}</p>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                        Frecuencia
                      </p>
                      <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                        {getFrequencyLabel(eventType.default_recurrence.frequency)}
                      </p>
                    </div>

                    {eventType.default_recurrence.day_of_month && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Día de Vencimiento
                        </p>
                        <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                          Día {eventType.default_recurrence.day_of_month}
                        </p>
                      </div>
                    )}

                    {eventType.default_recurrence.month_of_year && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Mes de Vencimiento
                        </p>
                        <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                          {new Date(
                            2000,
                            eventType.default_recurrence.month_of_year - 1
                          ).toLocaleDateString('es-CL', { month: 'long' })}
                        </p>
                      </div>
                    )}

                    {eventType.authority && (
                      <div>
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Autoridad
                        </p>
                        <p className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                          {eventType.authority}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="ml-4 flex gap-2">
                  <button
                    onClick={() => handleEditClick(eventType)}
                    className="rounded-lg p-2 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
                    title="Editar evento"
                  >
                    <Edit2 className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(eventType.id)}
                    className="rounded-lg p-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                    title="Eliminar evento"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {eventTemplates.length === 0 && !loading && (
          <div className="rounded-lg border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-800">
            <Calendar className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
              No hay tipos de eventos
            </h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Crea el primer tipo de evento usando el botón "Crear Evento" arriba.
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
                Crear Nuevo Tipo de Evento
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleCreateEventTemplate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Código *
                </label>
                <input
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="ej: f50, dj1879"
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
                  placeholder="ej: Formulario 50"
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Descripción *
                </label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  placeholder="Describe el evento tributario..."
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
                    <option value="impuesto_mensual">Impuesto Mensual</option>
                    <option value="impuesto_anual">Impuesto Anual</option>
                    <option value="prevision">Previsión</option>
                    <option value="declaracion_jurada">Declaración Jurada</option>
                    <option value="libros">Libros Contables</option>
                    <option value="otros">Otros</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Autoridad *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.authority}
                    onChange={(e) => setFormData({ ...formData, authority: e.target.value })}
                    placeholder="ej: SII, Previred"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Frecuencia *
                  </label>
                  <select
                    required
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="monthly">Mensual</option>
                    <option value="quarterly">Trimestral</option>
                    <option value="biannual">Semestral</option>
                    <option value="annual">Anual</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Día de Vencimiento
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={formData.day_of_month}
                    onChange={(e) => setFormData({ ...formData, day_of_month: e.target.value })}
                    placeholder="1-31"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              {formData.frequency === 'annual' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Mes de Vencimiento (solo para anual)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={formData.month_of_year}
                    onChange={(e) => setFormData({ ...formData, month_of_year: e.target.value })}
                    placeholder="1-12"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_mandatory"
                  checked={formData.is_mandatory}
                  onChange={(e) => setFormData({ ...formData, is_mandatory: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label
                  htmlFor="is_mandatory"
                  className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Es obligatorio para todas las empresas
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
                    'Crear Evento'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 dark:bg-gray-800">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Editar Tipo de Evento
              </h2>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingEvent(null);
                }}
                className="rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleUpdateEventTemplate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Código *
                </label>
                <input
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="ej: f50, dj1879"
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
                  placeholder="ej: Formulario 50"
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Descripción *
                </label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  placeholder="Describe el evento tributario..."
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
                    <option value="impuesto_mensual">Impuesto Mensual</option>
                    <option value="impuesto_anual">Impuesto Anual</option>
                    <option value="prevision">Previsión</option>
                    <option value="declaracion_jurada">Declaración Jurada</option>
                    <option value="libros">Libros Contables</option>
                    <option value="otros">Otros</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Autoridad *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.authority}
                    onChange={(e) => setFormData({ ...formData, authority: e.target.value })}
                    placeholder="ej: SII, Previred"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Frecuencia *
                  </label>
                  <select
                    required
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="monthly">Mensual</option>
                    <option value="quarterly">Trimestral</option>
                    <option value="biannual">Semestral</option>
                    <option value="annual">Anual</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Día de Vencimiento
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={formData.day_of_month}
                    onChange={(e) => setFormData({ ...formData, day_of_month: e.target.value })}
                    placeholder="1-31"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>

              {formData.frequency === 'annual' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Mes de Vencimiento (solo para anual)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={formData.month_of_year}
                    onChange={(e) => setFormData({ ...formData, month_of_year: e.target.value })}
                    placeholder="1-12"
                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_mandatory_edit"
                  checked={formData.is_mandatory}
                  onChange={(e) => setFormData({ ...formData, is_mandatory: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label
                  htmlFor="is_mandatory_edit"
                  className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Es obligatorio para todas las empresas
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingEvent(null);
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
                    'Actualizar Evento'
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
              ¿Estás seguro de que deseas eliminar este tipo de evento? Esta acción no se puede
              deshacer. Si hay empresas con este evento activo, no podrás eliminarlo.
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
                onClick={() => handleDeleteEventTemplate(deleteConfirm)}
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
