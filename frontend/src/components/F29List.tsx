import { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  Filter,
  ExternalLink,
  Calendar,
  DollarSign,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../lib/config';
import { apiFetch } from '../lib/api-client';

interface F29Download {
  id: string;
  sii_folio: string;
  sii_id_interno: string | null;
  period_year: number;
  period_month: number;
  period_display: string;
  contributor_rut: string;
  submission_date: string | null;
  status: string; // Vigente, Rectificado, Anulado
  amount_cents: number;
  pdf_storage_url: string | null;
  pdf_download_status: string; // pending, downloaded, error
  pdf_download_error: string | null;
  pdf_downloaded_at: string | null;
  has_pdf: boolean;
  can_download_pdf: boolean;
  extra_data: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

interface F29ListProps {
  companyId: string;
}

export default function F29List({ companyId }: F29ListProps) {
  const { session } = useAuth();
  const [forms, setForms] = useState<F29Download[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedYear, setSelectedYear] = useState<number | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<string | 'all'>('all');

  // Expanded extra_data
  const [expandedForms, setExpandedForms] = useState<Set<string>>(new Set());

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  useEffect(() => {
    fetchF29List();
  }, [companyId, selectedYear, selectedStatus]);

  const fetchF29List = async () => {
    if (!session?.access_token || !companyId) return;

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (selectedYear !== 'all') params.append('year', selectedYear.toString());
      if (selectedStatus !== 'all') params.append('status', selectedStatus);

      const url = `${API_BASE_URL}/admin/company/${companyId}/f29${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await apiFetch(url, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al obtener formularios F29');
      }

      const data = await response.json();
      setForms(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (cents: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(cents);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('es-CL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      Vigente: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300',
      Rectificado: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300',
      Anulado: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300',
    };

    return (
      <span
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
          styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
        }`}
      >
        {status}
      </span>
    );
  };

  const getPDFStatusIcon = (form: F29Download) => {
    if (form.has_pdf) {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    }
    if (form.pdf_download_status === 'error') {
      return <XCircle className="h-4 w-4 text-red-600" />;
    }
    if (form.pdf_download_status === 'pending') {
      return <Clock className="h-4 w-4 text-gray-400" />;
    }
    return <AlertCircle className="h-4 w-4 text-yellow-600" />;
  };

  const getMonthName = (month: number) => {
    const months = [
      'Enero',
      'Febrero',
      'Marzo',
      'Abril',
      'Mayo',
      'Junio',
      'Julio',
      'Agosto',
      'Septiembre',
      'Octubre',
      'Noviembre',
      'Diciembre',
    ];
    return months[month - 1] || month.toString();
  };

  const toggleExtraData = (formId: string) => {
    setExpandedForms((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(formId)) {
        newSet.delete(formId);
      } else {
        newSet.add(formId);
      }
      return newSet;
    });
  };

  const hasExtraData = (form: F29Download) => {
    return form.extra_data && Object.keys(form.extra_data).length > 0;
  };

  const formatExtraDataValue = (value: any): string => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'boolean') return value ? 'Sí' : 'No';
    if (typeof value === 'number') {
      // Check if it looks like a currency amount
      if (Math.abs(value) > 100) {
        return formatCurrency(value);
      }
      return value.toLocaleString('es-CL');
    }
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  const getExtraDataLabel = (key: string): string => {
    const labels: Record<string, string> = {
      // Débitos (Lado izquierdo del F29)
      cantidad_facturas_emitidas: 'Cantidad Facturas Emitidas',
      cant_recibo_pago_medios_electronicos: 'Recibo de Pago Medios Electrónicos',
      cantidad_facturas: 'Cantidad Facturas',
      cred_iva_por_dctos_electronicos: 'Créd. IVA por Dctos. Electrónicos',
      cant_int_ex_no_grav_sin_der_cred_fiscal: 'Cant. Int. Ex. No Grav. sin Der. Créd. Fiscal',
      cant_de_dctos_fact_recib_del_mes: 'Cant. de Dctos. Fact. Recib. del Mes',
      cant_notas_de_credito_recibidas: 'Cant. Notas de Crédito Recibidas',
      cant_notas_de_debito_recibidas: 'Cant. Notas de Débito Recibidas',
      remanente_de_credito_fisc: 'Remanente de Crédito Fisc.',
      retencion_tasa_ley_21133_sobre_rentas: 'Retención Tasa Ley 21.133 sobre Rentas',
      base_imponible: 'Base Imponible',
      tasa_ppm_1ra_categoria: 'Tasa PPM 1ra Categoría',

      // Créditos (Lado derecho del F29)
      debitos_facturas_emitidas: 'Débitos Facturas Emitidas',
      deb_recibo_pago_medios_electronicos: 'Déb. Recibo de Pago Medios Electrónicos',
      liquidacion_de_facturas: 'Liquidación de Facturas',
      total_debitos: 'Total Débitos',
      monto_sin_der_a_cred_fiscal: 'Monto sin Der. a Créd. Fiscal',
      credito_rec_fact_de_compras_del_giro: 'Crédito Rec. Fact. de Compras del Giro',
      credito_recup_y_reint_notas_de_cred: 'Crédito Recup. y Reint. Notas de Créd.',
      notas_de_debito_rebajar_de_iva_y_reint: 'Notas de Débito Rebajar de IVA y Reint.',
      remanente_credito_mes_anterior: 'Remanente Crédito Mes Anterior',
      recup_imp_esp_art_42_n_diesel_tasa_0: 'Recup. Imp. Esp. Art. 42 N° Diesel, Tasa 0%',
      monto_de_iva_postergado_6_o_12_cuotas: 'Monto de IVA Postergado 6 o 12 Cuotas',
      total_creditos: 'Total Créditos',
      imp_determ_iva: 'Imp. Determ. IVA',
      ppm_neto_determinado: 'PPM Neto Determinado',
      sub_total_imp_determinado_anverso: 'Sub Total Imp. Determinado Anverso',
      total_determinado: 'Total Determinado',

      // Totales finales
      total_a_pagar_dentro_del_plazo_legal: 'Total a Pagar Dentro del Plazo Legal',
      mas_ipc: 'Más IPC',
      mas_interes_y_multas: 'Más Interés y Multas',
      condonacion: 'Condonación',
      total_a_pagar_con_recargo: 'Total a Pagar con Recargo',

      // Información adicional
      payment_method: 'Medio de Pago',
      payment_date: 'Fecha de Pago',
      banco: 'Banco',
      tipo_declaracion: 'Tipo de Declaración',
      fecha_presentacion: 'Fecha de Presentación',
    };
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const categorizeExtraData = (extraData: Record<string, any>) => {
    const categories = {
      debitos: {
        title: 'Débitos y Facturas',
        icon: '📊',
        color: 'blue',
        keys: [
          'cantidad_facturas_emitidas',
          'cant_recibo_pago_medios_electronicos',
          'cantidad_facturas',
          'cred_iva_por_dctos_electronicos',
          'cant_int_ex_no_grav_sin_der_cred_fiscal',
          'cant_de_dctos_fact_recib_del_mes',
          'cant_notas_de_credito_recibidas',
          'cant_notas_de_debito_recibidas',
        ],
      },
      creditos_impuestos: {
        title: 'Créditos e Impuestos',
        icon: '💰',
        color: 'green',
        keys: [
          'debitos_facturas_emitidas',
          'deb_recibo_pago_medios_electronicos',
          'liquidacion_de_facturas',
          'total_debitos',
          'credito_rec_fact_de_compras_del_giro',
          'credito_recup_y_reint_notas_de_cred',
          'notas_de_debito_rebajar_de_iva_y_reint',
          'total_creditos',
        ],
      },
      remanentes: {
        title: 'Remanentes y Recuperos',
        icon: '🔄',
        color: 'purple',
        keys: [
          'remanente_de_credito_fisc',
          'remanente_credito_mes_anterior',
          'recup_imp_esp_art_42_n_diesel_tasa_0',
          'monto_de_iva_postergado_6_o_12_cuotas',
        ],
      },
      determinacion: {
        title: 'Determinación de Impuestos',
        icon: '📝',
        color: 'orange',
        keys: [
          'monto_sin_der_a_cred_fiscal',
          'imp_determ_iva',
          'ppm_neto_determinado',
          'sub_total_imp_determinado_anverso',
          'total_determinado',
        ],
      },
      pago: {
        title: 'Información de Pago',
        icon: '💳',
        color: 'indigo',
        keys: [
          'total_a_pagar_dentro_del_plazo_legal',
          'mas_ipc',
          'mas_interes_y_multas',
          'condonacion',
          'total_a_pagar_con_recargo',
        ],
      },
      ppm_base: {
        title: 'PPM y Base Imponible',
        icon: '📈',
        color: 'teal',
        keys: [
          'retencion_tasa_ley_21133_sobre_rentas',
          'base_imponible',
          'tasa_ppm_1ra_categoria',
        ],
      },
      adicional: {
        title: 'Información Adicional',
        icon: 'ℹ️',
        color: 'gray',
        keys: [
          'payment_method',
          'payment_date',
          'banco',
          'tipo_declaracion',
          'fecha_presentacion',
        ],
      },
    };

    const categorized: Record<string, Array<{ key: string; value: any }>> = {};

    // Categorize known keys
    Object.entries(categories).forEach(([categoryKey, category]) => {
      const items = category.keys
        .filter((key) => key in extraData && extraData[key] !== null && extraData[key] !== undefined)
        .map((key) => ({ key, value: extraData[key] }));

      if (items.length > 0) {
        categorized[categoryKey] = items;
      }
    });

    // Add uncategorized keys
    const allCategorizedKeys = new Set(
      Object.values(categories).flatMap((cat) => cat.keys)
    );
    const uncategorized = Object.entries(extraData)
      .filter(([key]) => !allCategorizedKeys.has(key))
      .map(([key, value]) => ({ key, value }));

    if (uncategorized.length > 0) {
      categorized.otros = uncategorized;
    }

    return { categorized, categories };
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="text-gray-600 dark:text-gray-400">Cargando formularios F29...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20">
        <div className="flex items-start space-x-3">
          <XCircle className="h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400" />
          <div>
            <h3 className="font-medium text-red-800 dark:text-red-300">Error al cargar formularios</h3>
            <p className="mt-1 text-sm text-red-700 dark:text-red-400">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      {/* Header */}
      <div className="mb-6 flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div className="flex items-center space-x-2">
          <FileText className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Formularios F29 ({forms.length})
          </h2>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 shadow-sm transition-colors hover:border-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:border-gray-500"
            >
              <option value="all">Todos los años</option>
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 shadow-sm transition-colors hover:border-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:border-gray-500"
          >
            <option value="all">Todos los estados</option>
            <option value="Vigente">Vigente</option>
            <option value="Rectificado">Rectificado</option>
            <option value="Anulado">Anulado</option>
          </select>
        </div>
      </div>

      {/* Forms List */}
      {forms.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center dark:border-gray-700 dark:bg-gray-900/50">
          <FileText className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <p className="text-gray-600 dark:text-gray-400">No se encontraron formularios F29</p>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-500">
            Usa la sección de sincronizaciones para obtener formularios del SII
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {forms.map((form) => (
            <div
              key={form.id}
              className="rounded-lg border border-gray-200 bg-gray-50 p-4 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-900/50 dark:hover:bg-gray-900"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Period and Status */}
                  <div className="mb-2 flex items-center space-x-3">
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {getMonthName(form.period_month)} {form.period_year}
                      </span>
                    </div>
                    {getStatusBadge(form.status)}
                    <div className="flex items-center space-x-1" title={`PDF: ${form.pdf_download_status}`}>
                      {getPDFStatusIcon(form)}
                    </div>
                  </div>

                  {/* Details Grid */}
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Folio</p>
                      <p className="font-mono text-sm font-medium text-gray-900 dark:text-white">
                        {form.sii_folio}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Monto</p>
                      <div className="flex items-center space-x-1">
                        <DollarSign className="h-3.5 w-3.5 text-gray-400" />
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(form.amount_cents)}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Fecha presentación</p>
                      <p className="text-sm text-gray-900 dark:text-white">{formatDate(form.submission_date)}</p>
                    </div>

                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">PDF descargado</p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {form.pdf_downloaded_at ? formatDate(form.pdf_downloaded_at) : 'Pendiente'}
                      </p>
                    </div>
                  </div>

                  {/* Error Message */}
                  {form.pdf_download_error && (
                    <div className="mt-2 flex items-start space-x-2 rounded-md bg-red-50 p-2 dark:bg-red-900/20">
                      <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600 dark:text-red-400" />
                      <p className="text-xs text-red-700 dark:text-red-400">{form.pdf_download_error}</p>
                    </div>
                  )}

                  {/* Extra Data Section */}
                  {hasExtraData(form) && (
                    <div className="mt-3">
                      <button
                        onClick={() => toggleExtraData(form.id)}
                        className="flex w-full items-center justify-between rounded-md border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                      >
                        <div className="flex items-center space-x-2">
                          <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                          <span>Datos Adicionales</span>
                          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                            {Object.keys(form.extra_data!).length}
                          </span>
                        </div>
                        {expandedForms.has(form.id) ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>

{expandedForms.has(form.id) && (() => {
                        const { categorized, categories } = categorizeExtraData(form.extra_data!);
                        const colorClasses = {
                          blue: 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20',
                          green: 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20',
                          purple: 'border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-900/20',
                          orange: 'border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-900/20',
                          indigo: 'border-indigo-200 bg-indigo-50 dark:border-indigo-800 dark:bg-indigo-900/20',
                          teal: 'border-teal-200 bg-teal-50 dark:border-teal-800 dark:bg-teal-900/20',
                          gray: 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900/50',
                        };

                        return (
                          <div className="mt-2 space-y-3 rounded-md border border-gray-200 bg-white p-3 dark:border-gray-600 dark:bg-gray-800">
                            {Object.entries(categorized).map(([categoryKey, items]) => {
                              const categoryInfo = (categories as any)[categoryKey] || {
                                title: 'Otros',
                                icon: '📋',
                                color: 'gray',
                              };

                              return (
                                <div
                                  key={categoryKey}
                                  className={`rounded-lg border p-3 ${
                                    colorClasses[categoryInfo.color as keyof typeof colorClasses]
                                  }`}
                                >
                                  <div className="mb-2 flex items-center space-x-2">
                                    <span className="text-lg">{categoryInfo.icon}</span>
                                    <h4 className="font-semibold text-gray-900 dark:text-white">
                                      {categoryInfo.title}
                                    </h4>
                                  </div>
                                  <div className="grid gap-2 sm:grid-cols-2">
                                    {items.map(({ key, value }) => (
                                      <div
                                        key={key}
                                        className="rounded-md bg-white/60 p-2 dark:bg-gray-800/60"
                                      >
                                        <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                                          {getExtraDataLabel(key)}
                                        </p>
                                        <p className="mt-0.5 text-sm font-semibold text-gray-900 dark:text-white">
                                          {formatExtraDataValue(value)}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        );
                      })()}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="ml-4 flex flex-col space-y-2">
                  {form.has_pdf && form.pdf_storage_url && (
                    <a
                      href={form.pdf_storage_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700"
                    >
                      <Download className="h-4 w-4" />
                      <span>Ver PDF</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}

                  {!form.has_pdf && form.can_download_pdf && (
                    <button
                      onClick={() => {
                        /* TODO: Implement individual PDF download */
                      }}
                      className="inline-flex items-center space-x-1 rounded-md border border-blue-300 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm transition-colors hover:bg-blue-100 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
                    >
                      <Download className="h-4 w-4" />
                      <span>Descargar</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {forms.length > 0 && (
        <div className="mt-6 grid gap-4 border-t border-gray-200 pt-6 sm:grid-cols-3 dark:border-gray-700">
          <div className="rounded-lg bg-green-50 p-4 dark:bg-green-900/20">
            <p className="text-sm text-gray-600 dark:text-gray-400">PDFs Descargados</p>
            <p className="mt-1 text-2xl font-bold text-green-700 dark:text-green-400">
              {forms.filter((f) => f.has_pdf).length}
            </p>
          </div>
          <div className="rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
            <p className="text-sm text-gray-600 dark:text-gray-400">Pendientes</p>
            <p className="mt-1 text-2xl font-bold text-yellow-700 dark:text-yellow-400">
              {forms.filter((f) => f.pdf_download_status === 'pending').length}
            </p>
          </div>
          <div className="rounded-lg bg-red-50 p-4 dark:bg-red-900/20">
            <p className="text-sm text-gray-600 dark:text-gray-400">Con Error</p>
            <p className="mt-1 text-2xl font-bold text-red-700 dark:text-red-400">
              {forms.filter((f) => f.pdf_download_status === 'error').length}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
