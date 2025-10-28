import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2,
  Users,
  FileText,
  Mail,
  Phone,
  MapPin,
  Calendar,
  TrendingUp,
  TrendingDown,
  ArrowLeft,
  Bell,
  Send,
} from 'lucide-react';
import { CompanyDetail } from '../types/admin';
import { API_BASE_URL } from '../lib/config';
import { useAuth } from '../contexts/AuthContext';
import SyncPanel from '../components/SyncPanel';
import F29List from '../components/F29List';
import CalendarConfig from '../components/CalendarConfig';
import CalendarEventsSection from '../components/CalendarEventsSection';
import { apiFetch } from '../lib/api-client';

export default function AdminCompanyView() {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const { session, loading: authLoading } = useAuth();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'f29' | 'calendar'>('overview');
  const [sendingNotification, setSendingNotification] = useState(false);
  const [notificationResult, setNotificationResult] = useState<{
    success: boolean;
    message: string;
    details?: any[];
  } | null>(null);

  const fetchCompanyData = async () => {
    // Wait for auth to load
    if (authLoading) {
      return;
    }

    if (!companyId || !session?.access_token) {
      setLoading(false);
      if (!session?.access_token) {
        setError('No authenticated session');
      }
      return;
    }

    try {
      setLoading(true);
      const response = await apiFetch(`${API_BASE_URL}/admin/company/${companyId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch company data');
      }

      const data = await response.json();
      setCompany(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanyData();
  }, [companyId, session?.access_token, authLoading]);

  const sendTestNotification = async () => {
    if (!companyId || !session?.access_token) return;

    setSendingNotification(true);
    setNotificationResult(null);

    try {
      const response = await apiFetch(
        `${API_BASE_URL}/admin/company/${companyId}/send-test-notification`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: '🔔 Notificación de prueba desde Fizko Admin\n\nSi recibes este mensaje, el sistema de notificaciones está funcionando correctamente.',
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al enviar notificación');
      }

      const data = await response.json();
      setNotificationResult({
        success: data.success,
        message: data.message,
        details: data.details,
      });
    } catch (err) {
      setNotificationResult({
        success: false,
        message: err instanceof Error ? err.message : 'Error desconocido',
      });
    } finally {
      setSendingNotification(false);
    }
  };


  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="text-gray-600 dark:text-gray-400">Cargando datos de la empresa...</p>
        </div>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <p className="mb-4 text-red-600 dark:text-red-400">
            {error || 'Empresa no encontrada'}
          </p>
          <button
            onClick={() => navigate(-1)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
    }).format(amount);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('es-CL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate(-1)}
                className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {company.business_name}
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">RUT: {company.rut}</p>
              </div>
            </div>

            {/* Send Test Notification Button */}
            <button
              onClick={sendTestNotification}
              disabled={sendingNotification}
              className="flex items-center space-x-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {sendingNotification ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Enviando...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span>Enviar Notificación de Prueba</span>
                </>
              )}
            </button>
          </div>

          {/* Notification Result Alert */}
          {notificationResult && (
            <div className={`mt-4 rounded-lg p-4 ${
              notificationResult.success
                ? 'bg-green-50 border border-green-200 dark:bg-green-900/20 dark:border-green-800'
                : 'bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800'
            }`}>
              <div className="flex items-start space-x-3">
                <Bell className={`h-5 w-5 mt-0.5 ${
                  notificationResult.success ? 'text-green-600' : 'text-red-600'
                }`} />
                <div className="flex-1">
                  <p className={`font-medium ${
                    notificationResult.success ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'
                  }`}>
                    {notificationResult.message}
                  </p>
                  {notificationResult.details && notificationResult.details.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {notificationResult.details.map((detail, idx) => (
                        <p key={idx} className={`text-sm ${
                          notificationResult.success ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'
                        }`}>
                          • {detail.user_name} ({detail.phone}): {detail.status === 'sent' ? '✅ Enviado' : `❌ ${detail.error}`}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => setNotificationResult(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ×
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'
              }`}
            >
              Vista General
            </button>
            <button
              onClick={() => setActiveTab('f29')}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                activeTab === 'f29'
                  ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'
              }`}
            >
              Formularios 29
            </button>
            <button
              onClick={() => setActiveTab('calendar')}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                activeTab === 'calendar'
                  ? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'
              }`}
            >
              Eventos Tributarios
            </button>
          </nav>
        </div>

        {/* Tab Content: Overview */}
        {activeTab === 'overview' && (
          <div className="grid gap-6 lg:grid-cols-3">
          {/* Company Info Card */}
          <div className="lg:col-span-2">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-4 flex items-center space-x-2">
                <Building2 className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Información de la Empresa
                </h2>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Razón Social
                  </label>
                  <p className="text-gray-900 dark:text-white">{company.business_name}</p>
                </div>

                {company.trade_name && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Nombre Comercial
                    </label>
                    <p className="text-gray-900 dark:text-white">{company.trade_name}</p>
                  </div>
                )}

                {company.email && (
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4 text-gray-400" />
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Email
                      </label>
                      <p className="text-gray-900 dark:text-white">{company.email}</p>
                    </div>
                  </div>
                )}

                {company.phone && (
                  <div className="flex items-center space-x-2">
                    <Phone className="h-4 w-4 text-gray-400" />
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Teléfono
                      </label>
                      <p className="text-gray-900 dark:text-white">{company.phone}</p>
                    </div>
                  </div>
                )}

                {company.address && (
                  <div className="col-span-2 flex items-center space-x-2">
                    <MapPin className="h-4 w-4 text-gray-400" />
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Dirección
                      </label>
                      <p className="text-gray-900 dark:text-white">{company.address}</p>
                    </div>
                  </div>
                )}

                {company.tax_regime && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Régimen Tributario
                    </label>
                    <p className="text-gray-900 dark:text-white">{company.tax_regime}</p>
                  </div>
                )}

                {company.sii_activity_name && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Actividad SII
                    </label>
                    <p className="text-gray-900 dark:text-white">
                      {company.sii_activity_name} ({company.sii_activity_code})
                    </p>
                  </div>
                )}

                <div className="flex items-center space-x-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <div>
                    <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Creada
                    </label>
                    <p className="text-gray-900 dark:text-white">
                      {formatDate(company.created_at)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Document Stats Card */}
          <div>
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-4 flex items-center space-x-2">
                <FileText className="h-5 w-5 text-green-600" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Documentos
                </h2>
              </div>

              <div className="space-y-4">
                <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Ventas
                      </span>
                    </div>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">
                      {company.document_stats.total_sales_documents}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    Total: {formatCurrency(company.document_stats.total_sales_amount)}
                  </p>
                </div>

                <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <TrendingDown className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Compras
                      </span>
                    </div>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">
                      {company.document_stats.total_purchase_documents}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    Total: {formatCurrency(company.document_stats.total_purchase_amount)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Users Table */}
          <div className="lg:col-span-2">
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-4 flex items-center space-x-2">
                <Users className="h-5 w-5 text-purple-600" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Usuarios con Acceso ({company.users.length})
                </h2>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-gray-200 dark:border-gray-700">
                    <tr>
                      <th className="pb-3 text-left text-sm font-medium text-gray-600 dark:text-gray-400">
                        Usuario
                      </th>
                      <th className="pb-3 text-left text-sm font-medium text-gray-600 dark:text-gray-400">
                        Rol
                      </th>
                      <th className="pb-3 text-left text-sm font-medium text-gray-600 dark:text-gray-400">
                        Estado
                      </th>
                      <th className="pb-3 text-left text-sm font-medium text-gray-600 dark:text-gray-400">
                        Último Acceso
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {company.users.map((user) => (
                      <tr key={user.id}>
                        <td className="py-3">
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {user.full_name || `${user.name} ${user.lastname}`}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {user.email}
                            </p>
                          </div>
                        </td>
                        <td className="py-3 text-sm text-gray-600 dark:text-gray-400">
                          {user.rol || 'N/A'}
                        </td>
                        <td className="py-3">
                          <span
                            className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                              user.is_active
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                            }`}
                          >
                            {user.is_active ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td className="py-3 text-sm text-gray-600 dark:text-gray-400">
                          {formatDateTime(user.last_accessed_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Sync Actions */}
          <div>
            <SyncPanel
              syncActions={company.sync_actions}
              sessionId={company.users.find((user) => user.is_active)?.session_id}
              onRefreshData={fetchCompanyData}
            />
          </div>
        </div>
        )}

        {/* Tab Content: F29 Forms */}
        {activeTab === 'f29' && (
          <div>
            <F29List companyId={companyId!} />
          </div>
        )}

        {/* Tab Content: Calendar Events & Configuration */}
        {activeTab === 'calendar' && (
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Calendar Events Section - 2/3 width */}
            <div className="lg:col-span-2">
              <CalendarEventsSection companyId={companyId!} />
            </div>

            {/* Calendar Configuration Section - 1/3 width */}
            <div className="lg:col-span-1">
              <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
                <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
                  Configuración
                </h3>
                <CalendarConfig companyId={companyId!} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
