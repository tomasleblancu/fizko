import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2,
  Users,
  FileText,
  RefreshCw,
  Mail,
  Phone,
  MapPin,
  Calendar,
  TrendingUp,
  TrendingDown,
  Activity,
  ArrowLeft,
  Download,
} from 'lucide-react';
import { CompanyDetail } from '../types/admin';
import { API_BASE_URL } from '../lib/config';
import { useAuth } from '../contexts/AuthContext';

export default function AdminCompanyView() {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const { session, loading: authLoading } = useAuth();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncingF29, setSyncingF29] = useState(false);
  const [f29SyncMessage, setF29SyncMessage] = useState<string | null>(null);
  const [downloadingF29PDFs, setDownloadingF29PDFs] = useState(false);
  const [f29PDFDownloadMessage, setF29PDFDownloadMessage] = useState<string | null>(null);

  useEffect(() => {
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
        const response = await fetch(`${API_BASE_URL}/admin/company/${companyId}`, {
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

    fetchCompanyData();
  }, [companyId, session?.access_token, authLoading]);

  const handleSync = async (months: number) => {
    if (!session?.access_token || !company) return;

    // Get the first active session for this company
    const activeSession = company.users.find((user) => user.is_active);
    if (!activeSession) {
      setSyncMessage('No hay sesiones activas para sincronizar');
      return;
    }

    try {
      setSyncing(true);
      setSyncMessage('Sincronizando documentos...');

      const response = await fetch(`${API_BASE_URL}/sii/sync/documents`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: activeSession.session_id,
          months: months,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al sincronizar');
      }

      const data = await response.json();

      // Mostrar mensaje con estadísticas
      const compras = data.compras || { total: 0, nuevos: 0, actualizados: 0 };
      const ventas = data.ventas || { total: 0, nuevos: 0, actualizados: 0 };
      const totalDocs = compras.total + ventas.total;

      setSyncMessage(
        `Sincronización completada: ${totalDocs} documentos procesados ` +
        `(${compras.nuevos + ventas.nuevos} nuevos, ${compras.actualizados + ventas.actualizados} actualizados) ` +
        `en ${data.duration_seconds?.toFixed(1) || 0}s`
      );

      // Refetch company data without full page reload
      setTimeout(async () => {
        try {
          const refreshResponse = await fetch(`${API_BASE_URL}/admin/company/${companyId}`, {
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json',
            },
          });

          if (refreshResponse.ok) {
            const refreshedData = await refreshResponse.json();
            setCompany(refreshedData);
            setSyncMessage(
              `Sincronización completada: ${totalDocs} documentos procesados ` +
              `(${compras.nuevos + ventas.nuevos} nuevos, ${compras.actualizados + ventas.actualizados} actualizados)`
            );
          }
        } catch (refreshError) {
          console.error('Error refreshing company data:', refreshError);
          // Keep the success message even if refresh fails
        }
      }, 2000);
    } catch (err) {
      setSyncMessage(
        err instanceof Error ? err.message : 'Error al sincronizar'
      );
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncF29 = async (year: number) => {
    if (!session?.access_token || !company) return;

    // Get the first active session for this company
    const activeSession = company.users.find((user) => user.is_active);
    if (!activeSession) {
      setF29SyncMessage('No hay sesiones activas para sincronizar');
      return;
    }

    try {
      setSyncingF29(true);
      setF29SyncMessage(`Sincronizando lista de F29 del año ${year}...`);

      const response = await fetch(
        `${API_BASE_URL}/sii/sync/f29/${year}?session_id=${activeSession.session_id}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al sincronizar F29');
      }

      const data = await response.json();

      // Mostrar mensaje con estadísticas
      const message = `✅ ${data.forms_synced} formularios F29 sincronizados`;
      setF29SyncMessage(message);

      // Clear message after 10 seconds
      setTimeout(() => setF29SyncMessage(null), 10000);
    } catch (err) {
      setF29SyncMessage(
        `❌ ${err instanceof Error ? err.message : 'Error al sincronizar F29'}`
      );
    } finally {
      setSyncingF29(false);
    }
  };

  const handleDownloadF29PDFs = async (year?: number) => {
    if (!session?.access_token || !company) return;

    // Get the first active session for this company
    const activeSession = company.users.find((user) => user.is_active);
    if (!activeSession) {
      setF29PDFDownloadMessage('No hay sesiones activas para descargar PDFs');
      return;
    }

    try {
      setDownloadingF29PDFs(true);
      setF29PDFDownloadMessage(
        year
          ? `Descargando PDFs de F29 del año ${year}...`
          : 'Descargando todos los PDFs pendientes...'
      );

      const requestBody: { session_id: string; year?: number } = {
        session_id: activeSession.session_id,
      };

      if (year) {
        requestBody.year = year;
      }

      const response = await fetch(
        `${API_BASE_URL}/sii/sync/f29/download-pdfs`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al descargar PDFs');
      }

      const data = await response.json();

      // Mostrar mensaje detallado con estadísticas
      let message = `✅ ${data.pdfs_downloaded} PDFs descargados correctamente`;

      if (data.pdfs_failed > 0) {
        message += `, ${data.pdfs_failed} fallaron`;
        if (data.failed_folios && data.failed_folios.length > 0) {
          message += ` (folios: ${data.failed_folios.slice(0, 3).join(', ')}${
            data.failed_folios.length > 3 ? '...' : ''
          })`;
        }
      }

      setF29PDFDownloadMessage(message);

      // Clear message after 15 seconds (más tiempo para leer el resultado)
      setTimeout(() => setF29PDFDownloadMessage(null), 15000);
    } catch (err) {
      setF29PDFDownloadMessage(
        `❌ ${err instanceof Error ? err.message : 'Error al descargar PDFs'}`
      );
    } finally {
      setDownloadingF29PDFs(false);
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
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
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
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <RefreshCw className="h-5 w-5 text-orange-600" />
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Sincronizaciones
                  </h2>
                </div>
              </div>

              {/* Sync Action Buttons */}
              <div className="mb-6 space-y-3">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Sincronizar Documentos
                </h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleSync(1)}
                    disabled={syncing}
                    className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${syncing ? 'animate-spin' : ''}`} />
                    1 mes
                  </button>

                  <button
                    onClick={() => handleSync(3)}
                    disabled={syncing}
                    className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${syncing ? 'animate-spin' : ''}`} />
                    3 meses
                  </button>

                  <button
                    onClick={() => handleSync(6)}
                    disabled={syncing}
                    className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${syncing ? 'animate-spin' : ''}`} />
                    6 meses
                  </button>
                </div>

                {syncMessage && (
                  <div
                    className={`rounded-md border px-3 py-2 text-sm ${
                      syncMessage.includes('Error') || syncMessage.includes('No hay')
                        ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'
                        : 'border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400'
                    }`}
                  >
                    {syncMessage}
                  </div>
                )}
              </div>

              {/* F29 Sync Section */}
              <div className="mb-6 space-y-3 border-t border-gray-200 pt-6 dark:border-gray-700">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Sincronizar Lista de F29
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Sincroniza la lista de formularios desde el SII (sin descargar PDFs)
                </p>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleSyncF29(2024)}
                    disabled={syncingF29}
                    className="inline-flex items-center gap-1.5 rounded-md border border-purple-300 bg-purple-50 px-3 py-1.5 text-sm font-medium text-purple-700 shadow-sm transition-colors hover:bg-purple-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-purple-600 dark:bg-purple-900/20 dark:text-purple-300 dark:hover:bg-purple-900/30"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${syncingF29 ? 'animate-spin' : ''}`} />
                    2024
                  </button>

                  <button
                    onClick={() => handleSyncF29(2023)}
                    disabled={syncingF29}
                    className="inline-flex items-center gap-1.5 rounded-md border border-purple-300 bg-purple-50 px-3 py-1.5 text-sm font-medium text-purple-700 shadow-sm transition-colors hover:bg-purple-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-purple-600 dark:bg-purple-900/20 dark:text-purple-300 dark:hover:bg-purple-900/30"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${syncingF29 ? 'animate-spin' : ''}`} />
                    2023
                  </button>

                  <button
                    onClick={() => handleSyncF29(2022)}
                    disabled={syncingF29}
                    className="inline-flex items-center gap-1.5 rounded-md border border-purple-300 bg-purple-50 px-3 py-1.5 text-sm font-medium text-purple-700 shadow-sm transition-colors hover:bg-purple-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-purple-600 dark:bg-purple-900/20 dark:text-purple-300 dark:hover:bg-purple-900/30"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${syncingF29 ? 'animate-spin' : ''}`} />
                    2022
                  </button>
                </div>

                {f29SyncMessage && (
                  <div
                    className={`rounded-md border px-3 py-2 text-sm ${
                      f29SyncMessage.includes('Error') || f29SyncMessage.includes('❌')
                        ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'
                        : 'border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400'
                    }`}
                  >
                    {f29SyncMessage}
                  </div>
                )}
              </div>

              {/* F29 PDF Download Section */}
              <div className="mb-6 space-y-3 border-t border-gray-200 pt-6 dark:border-gray-700">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Descargar PDFs de F29
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Descarga los PDFs de los formularios ya sincronizados
                </p>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleDownloadF29PDFs()}
                    disabled={downloadingF29PDFs}
                    className="inline-flex items-center gap-1.5 rounded-md border border-blue-300 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm transition-colors hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
                  >
                    <Download className={`h-3.5 w-3.5 ${downloadingF29PDFs ? 'animate-bounce' : ''}`} />
                    Todos los pendientes
                  </button>

                  <button
                    onClick={() => handleDownloadF29PDFs(2024)}
                    disabled={downloadingF29PDFs}
                    className="inline-flex items-center gap-1.5 rounded-md border border-blue-300 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm transition-colors hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
                  >
                    <Download className={`h-3.5 w-3.5 ${downloadingF29PDFs ? 'animate-bounce' : ''}`} />
                    2024
                  </button>

                  <button
                    onClick={() => handleDownloadF29PDFs(2023)}
                    disabled={downloadingF29PDFs}
                    className="inline-flex items-center gap-1.5 rounded-md border border-blue-300 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm transition-colors hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
                  >
                    <Download className={`h-3.5 w-3.5 ${downloadingF29PDFs ? 'animate-bounce' : ''}`} />
                    2023
                  </button>

                  <button
                    onClick={() => handleDownloadF29PDFs(2022)}
                    disabled={downloadingF29PDFs}
                    className="inline-flex items-center gap-1.5 rounded-md border border-blue-300 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm transition-colors hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
                  >
                    <Download className={`h-3.5 w-3.5 ${downloadingF29PDFs ? 'animate-bounce' : ''}`} />
                    2022
                  </button>
                </div>

                {f29PDFDownloadMessage && (
                  <div
                    className={`rounded-md border px-3 py-2 text-sm ${
                      f29PDFDownloadMessage.includes('Error') || f29PDFDownloadMessage.includes('❌')
                        ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'
                        : 'border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400'
                    }`}
                  >
                    {f29PDFDownloadMessage}
                  </div>
                )}
              </div>

              {/* Sync History */}
              <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-white">
                Historial de Sincronizaciones
              </h3>

              {company.sync_actions.length > 0 ? (
                <div className="space-y-3">
                  {company.sync_actions.map((sync, index) => (
                    <div
                      key={index}
                      className="rounded-lg border border-gray-200 p-3 dark:border-gray-700"
                    >
                      <div className="flex items-center space-x-2">
                        <Activity className="h-4 w-4 text-orange-600" />
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {sync.user_email}
                        </p>
                      </div>
                      <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                        Última sincronización: {formatDateTime(sync.last_sync)}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        Total: {sync.total_syncs}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  No hay sincronizaciones registradas
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
