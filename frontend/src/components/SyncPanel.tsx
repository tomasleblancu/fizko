import { useState } from 'react';
import { RefreshCw, Download, Activity, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

interface SyncAction {
  user_email: string;
  last_sync: string;
  total_syncs: number;
}

interface SyncPanelProps {
  syncActions: SyncAction[];
  sessionId?: string;
  onRefreshData?: () => void;
}

interface SyncResult {
  success: boolean;
  message: string;
  details?: {
    compras?: { total: number; nuevos: number; actualizados: number };
    ventas?: { total: number; nuevos: number; actualizados: number };
    duration_seconds?: number;
    forms_synced?: number;
    pdfs_downloaded?: number;
    pdfs_failed?: number;
    failed_folios?: string[];
  };
}

export default function SyncPanel({ syncActions, sessionId, onRefreshData }: SyncPanelProps) {
  const { session } = useAuth();
  const [syncing, setSyncing] = useState(false);
  const [syncingF29, setSyncingF29] = useState(false);
  const [downloadingF29PDFs, setDownloadingF29PDFs] = useState(false);

  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [f29SyncResult, setF29SyncResult] = useState<SyncResult | null>(null);
  const [f29PDFResult, setF29PDFResult] = useState<SyncResult | null>(null);

  const currentYear = new Date().getFullYear();
  const years = [currentYear, currentYear - 1, currentYear - 2];

  const handleSync = async (months: number) => {
    if (!sessionId) {
      setSyncResult({
        success: false,
        message: 'No hay sesiones activas para sincronizar',
      });
      return;
    }

    try {
      setSyncing(true);
      setSyncResult({
        success: true,
        message: `Sincronizando documentos de los últimos ${months} mes${months > 1 ? 'es' : ''}...`,
      });

      const response = await apiFetch(`${API_BASE_URL}/sii/sync/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          months: months,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al sincronizar');
      }

      const data = await response.json();
      const compras = data.compras || { total: 0, nuevos: 0, actualizados: 0 };
      const ventas = data.ventas || { total: 0, nuevos: 0, actualizados: 0 };
      const totalDocs = compras.total + ventas.total;

      setSyncResult({
        success: true,
        message: `Sincronización completada exitosamente`,
        details: {
          compras,
          ventas,
          duration_seconds: data.duration_seconds,
        },
      });

      // Refresh parent data after 2 seconds
      if (onRefreshData) {
        setTimeout(() => {
          onRefreshData();
        }, 2000);
      }

      // Clear message after 15 seconds
      setTimeout(() => setSyncResult(null), 15000);
    } catch (err) {
      setSyncResult({
        success: false,
        message: err instanceof Error ? err.message : 'Error al sincronizar',
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncF29 = async (year: number) => {
    if (!sessionId) {
      setF29SyncResult({
        success: false,
        message: 'No hay sesiones activas para sincronizar',
      });
      return;
    }

    try {
      setSyncingF29(true);
      setF29SyncResult({
        success: true,
        message: `Sincronizando lista de F29 del año ${year}...`,
      });

      const response = await apiFetch(`${API_BASE_URL}/sii/sync/f29/${year}?session_id=${sessionId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al sincronizar F29');
      }

      const data = await response.json();
      setF29SyncResult({
        success: true,
        message: `Lista de F29 sincronizada correctamente`,
        details: {
          forms_synced: data.forms_synced,
        },
      });

      setTimeout(() => setF29SyncResult(null), 10000);
    } catch (err) {
      setF29SyncResult({
        success: false,
        message: err instanceof Error ? err.message : 'Error al sincronizar F29',
      });
    } finally {
      setSyncingF29(false);
    }
  };

  const handleDownloadF29PDFs = async (year?: number) => {
    if (!sessionId) {
      setF29PDFResult({
        success: false,
        message: 'No hay sesiones activas para descargar PDFs',
      });
      return;
    }

    try {
      setDownloadingF29PDFs(true);
      setF29PDFResult({
        success: true,
        message: year
          ? `Descargando PDFs de F29 del año ${year}...`
          : 'Descargando todos los PDFs pendientes...',
      });

      const requestBody: { session_id: string; year?: number } = {
        session_id: sessionId,
      };

      if (year) {
        requestBody.year = year;
      }

      const response = await apiFetch(`${API_BASE_URL}/sii/sync/f29/download-pdfs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al descargar PDFs');
      }

      const data = await response.json();
      setF29PDFResult({
        success: true,
        message: 'PDFs descargados correctamente',
        details: {
          pdfs_downloaded: data.pdfs_downloaded,
          pdfs_failed: data.pdfs_failed,
          failed_folios: data.failed_folios,
        },
      });

      setTimeout(() => setF29PDFResult(null), 15000);
    } catch (err) {
      setF29PDFResult({
        success: false,
        message: err instanceof Error ? err.message : 'Error al descargar PDFs',
      });
    } finally {
      setDownloadingF29PDFs(false);
    }
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

  const ResultMessage = ({ result }: { result: SyncResult }) => {
    const baseClasses = 'rounded-lg border px-4 py-3 text-sm';
    const successClasses =
      'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-900/20 dark:text-green-300';
    const errorClasses =
      'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300';

    return (
      <div className={`${baseClasses} ${result.success ? successClasses : errorClasses}`}>
        <div className="flex items-start space-x-2">
          {result.success ? (
            <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          ) : (
            <XCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          )}
          <div className="flex-1">
            <p className="font-medium">{result.message}</p>
            {result.details && (
              <div className="mt-2 space-y-1 text-xs">
                {result.details.compras && result.details.ventas && (
                  <>
                    <div className="flex items-center justify-between">
                      <span>Compras:</span>
                      <span className="font-mono">
                        {result.details.compras.total} docs ({result.details.compras.nuevos} nuevos,{' '}
                        {result.details.compras.actualizados} actualizados)
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Ventas:</span>
                      <span className="font-mono">
                        {result.details.ventas.total} docs ({result.details.ventas.nuevos} nuevos,{' '}
                        {result.details.ventas.actualizados} actualizados)
                      </span>
                    </div>
                    {result.details.duration_seconds && (
                      <div className="flex items-center justify-between border-t border-green-200 pt-1 dark:border-green-800">
                        <span>Duración:</span>
                        <span className="font-mono">{result.details.duration_seconds.toFixed(1)}s</span>
                      </div>
                    )}
                  </>
                )}
                {result.details.forms_synced !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Formularios sincronizados:</span>
                    <span className="font-mono font-semibold">{result.details.forms_synced}</span>
                  </div>
                )}
                {result.details.pdfs_downloaded !== undefined && (
                  <>
                    <div className="flex items-center justify-between">
                      <span>PDFs descargados:</span>
                      <span className="font-mono font-semibold text-green-700 dark:text-green-400">
                        {result.details.pdfs_downloaded}
                      </span>
                    </div>
                    {result.details.pdfs_failed > 0 && (
                      <div className="flex items-center justify-between">
                        <span>Fallidos:</span>
                        <span className="font-mono font-semibold text-orange-700 dark:text-orange-400">
                          {result.details.pdfs_failed}
                        </span>
                      </div>
                    )}
                    {result.details.failed_folios && result.details.failed_folios.length > 0 && (
                      <div className="mt-1 rounded bg-white/50 p-2 dark:bg-gray-800/50">
                        <p className="font-medium">Folios fallidos:</p>
                        <p className="font-mono">
                          {result.details.failed_folios.slice(0, 5).join(', ')}
                          {result.details.failed_folios.length > 5 && ` +${result.details.failed_folios.length - 5} más`}
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-5 w-5 text-orange-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Sincronizaciones</h2>
        </div>
      </div>

      {/* Documents Sync Section */}
      <div className="mb-6 space-y-3">
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Sincronizar Documentos Tributarios
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Compras y ventas del SII
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {[1, 3, 6, 12].map((months) => (
            <button
              key={months}
              onClick={() => handleSync(months)}
              disabled={syncing || syncingF29 || downloadingF29PDFs}
              className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition-all hover:bg-gray-50 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
            >
              <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
              {months === 1 ? '1 mes' : `${months} meses`}
            </button>
          ))}
        </div>

        {syncResult && <ResultMessage result={syncResult} />}
      </div>

      {/* F29 List Sync Section */}
      <div className="mb-6 space-y-3 border-t border-gray-200 pt-6 dark:border-gray-700">
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Sincronizar Lista de Formularios F29
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Obtiene la lista de formularios desde el SII (sin descargar PDFs)
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {years.map((year) => (
            <button
              key={year}
              onClick={() => handleSyncF29(year)}
              disabled={syncing || syncingF29 || downloadingF29PDFs}
              className="inline-flex items-center gap-1.5 rounded-md border border-purple-300 bg-purple-50 px-3 py-2 text-sm font-medium text-purple-700 shadow-sm transition-all hover:bg-purple-100 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:border-purple-600 dark:bg-purple-900/20 dark:text-purple-300 dark:hover:bg-purple-900/30"
            >
              <RefreshCw className={`h-4 w-4 ${syncingF29 ? 'animate-spin' : ''}`} />
              {year}
            </button>
          ))}
        </div>

        {f29SyncResult && <ResultMessage result={f29SyncResult} />}
      </div>

      {/* F29 PDF Download Section */}
      <div className="mb-6 space-y-3 border-t border-gray-200 pt-6 dark:border-gray-700">
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Descargar PDFs de F29
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Descarga los archivos PDF de los formularios ya sincronizados
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleDownloadF29PDFs()}
            disabled={syncing || syncingF29 || downloadingF29PDFs}
            className="inline-flex items-center gap-1.5 rounded-md border border-blue-400 bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700 shadow-sm transition-all hover:bg-blue-100 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
          >
            <Download className={`h-4 w-4 ${downloadingF29PDFs ? 'animate-bounce' : ''}`} />
            Todos los pendientes
          </button>

          {years.map((year) => (
            <button
              key={year}
              onClick={() => handleDownloadF29PDFs(year)}
              disabled={syncing || syncingF29 || downloadingF29PDFs}
              className="inline-flex items-center gap-1.5 rounded-md border border-blue-300 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 shadow-sm transition-all hover:bg-blue-100 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
            >
              <Download className={`h-4 w-4 ${downloadingF29PDFs ? 'animate-bounce' : ''}`} />
              {year}
            </button>
          ))}
        </div>

        {f29PDFResult && <ResultMessage result={f29PDFResult} />}
      </div>

      {/* Sync History */}
      <div className="border-t border-gray-200 pt-6 dark:border-gray-700">
        <h3 className="mb-3 flex items-center space-x-2 text-sm font-semibold text-gray-900 dark:text-white">
          <Clock className="h-4 w-4 text-gray-500" />
          <span>Historial de Sincronizaciones</span>
        </h3>

        {syncActions.length > 0 ? (
          <div className="space-y-2">
            {syncActions.map((sync, index) => (
              <div
                key={index}
                className="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900/50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <Activity className="h-4 w-4 text-orange-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {sync.user_email}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {formatDateTime(sync.last_sync)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800 dark:bg-orange-900/20 dark:text-orange-300">
                      {sync.total_syncs} sync{sync.total_syncs !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center dark:border-gray-700 dark:bg-gray-900/50">
            <Activity className="mx-auto mb-2 h-8 w-8 text-gray-400" />
            <p className="text-sm text-gray-600 dark:text-gray-400">
              No hay sincronizaciones registradas
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
