import { useState } from 'react';
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
  X,
} from 'lucide-react';
import { useF29List, useDownloadF29Pdf } from "@/shared/hooks/useF29List";

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
  // Filters
  const [selectedYear, setSelectedYear] = useState<number | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<string | 'all'>('all');

  // Modal state
  const [selectedFormForModal, setSelectedFormForModal] = useState<F29Download | null>(null);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  // Use React Query hooks
  const { data: forms = [], isLoading: loading, error } = useF29List(companyId, {
    year: selectedYear,
    status: selectedStatus,
  });

  const downloadMutation = useDownloadF29Pdf(companyId);

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

  const openModal = (form: F29Download) => {
    setSelectedFormForModal(form);
  };

  const closeModal = () => {
    setSelectedFormForModal(null);
  };

  const hasExtraData = (form: F29Download) => {
    return form.extra_data && Object.keys(form.extra_data).length > 0;
  };

  const extractF29Data = (extra_data: Record<string, any> | null): Record<string, any> => {
    if (!extra_data) {
      console.log('⚠️ No extra_data provided');
      return {};
    }

    // El backend envuelve los datos en un objeto f29_data
    const f29Data = extra_data.f29_data || extra_data;

    // Debug: log la estructura de datos que recibimos
    console.log('📦 F29 data structure:', f29Data);

    // El backend retorna los datos en un formato anidado con códigos y field_names
    // Necesitamos extraer los valores usando los field_names
    const extracted: Record<string, any> = {};

    // Extraer datos de codes (estructura: { "503": { field_name: "cant_facturas_emitidas", value: 2 } })
    if (f29Data.codes) {
      console.log('📊 Processing codes:', Object.keys(f29Data.codes).length, 'entries');
      Object.entries(f29Data.codes).forEach(([code, codeData]: [string, any]) => {
        if (codeData && typeof codeData === 'object' && codeData.field_name && codeData.value !== undefined) {
          extracted[codeData.field_name] = codeData.value;
        }
      });
    }

    // Extraer datos del header si existen
    if (f29Data.header) {
      console.log('📋 Processing header:', Object.keys(f29Data.header));
      Object.entries(f29Data.header).forEach(([key, value]) => {
        if (!extracted[key]) {
          extracted[key] = value;
        }
      });
    }

    // Extraer datos del summary si existen
    if (f29Data.summary) {
      console.log('📈 Processing summary:', Object.keys(f29Data.summary));
      Object.entries(f29Data.summary).forEach(([key, value]) => {
        if (!extracted[key]) {
          extracted[key] = value;
        }
      });
    }

    console.log('✅ F29 extracted data:', extracted);
    console.log('📊 Total fields extracted:', Object.keys(extracted).length);

    return extracted;
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
      // Encabezado
      folio: 'Folio',
      rut: 'RUT',
      periodo: 'Período',
      razon_social: 'Razón Social',
      direccion_calle: 'Calle',
      direccion_numero: 'Número',
      comuna: 'Comuna',
      telefono: 'Teléfono',
      correo: 'Correo Electrónico',
      rut_representante: 'RUT Representante',

      // Cantidades de documentos emitidos
      cant_facturas_emitidas: 'Cant. Facturas Emitidas',
      cant_boletas: 'Cant. Boletas',
      cant_recibos_electronicos: 'Cant. Recibos Electrónicos',
      cant_notas_credito_emitidas: 'Cant. Notas de Crédito Emitidas',
      cant_notas_cred_vales_maq: 'Cant. Notas Créd. Vales Máquinas',
      cant_int_ex_no_grav: 'Cant. Intereses Exentos No Gravados',

      // Cantidades de documentos recibidos
      cant_facturas_recibidas: 'Cant. Facturas Recibidas',
      cant_fact_recibidas_giro: 'Cant. Facturas Recibidas del Giro',
      cant_notas_credito_recibidas: 'Cant. Notas de Crédito Recibidas',
      cant_notas_debito_recibidas: 'Cant. Notas de Débito Recibidas',
      cant_form_pago_imp_giro: 'Cant. Formularios Pago Impuesto del Giro',

      // DÉBITOS (montos)
      debitos_facturas: 'Débitos Facturas Emitidas',
      debitos_boletas: 'Débitos Boletas',
      debitos_recibos_electronicos: 'Déb. Recibos Electrónicos',
      debitos_notas_credito: 'Déb. Notas de Crédito Emitidas',
      debitos_notas_cred_vales: 'Déb. Notas Créd. Vales Máquinas IVA',
      liquidacion_facturas: 'Liquidación de Facturas',
      total_debitos: 'Total Débitos',
      monto_sin_der_cred_fiscal: 'Monto Sin Derecho a Crédito Fiscal',

      // CRÉDITOS (montos)
      credito_iva_documentos_electronicos: 'Crédito IVA por Documentos Electrónicos',
      credito_facturas_giro: 'Crédito Recup. y Reint. Facturas del Giro',
      credito_notas_credito: 'Crédito Recup. y Reint. Notas de Crédito',
      credito_notas_debito: 'Crédito Notas de Débito',
      credito_pago_imp_giro: 'Crédito Recup. y Reint. Pago Impuesto del Giro',
      remanente_mes_anterior: 'Remanente Crédito Mes Anterior',
      remanente_credito_fisc: 'Remanente de Crédito Fiscal',
      recup_imp_diesel: 'Recuperación Impuesto Especial Diesel',
      iva_postergado: 'Monto de IVA Postergado 6 o 12 Cuotas',
      total_creditos: 'Total Créditos',

      // Impuestos determinados
      iva_determinado: 'IVA Determinado',
      ppm_neto: 'PPM Neto Determinado',
      retencion_imp_unico: 'Retención Impuesto Único Trabajadores Art. 74 N°1 LIR',
      base_imponible: 'Base Imponible',
      tasa_ppm: 'Tasa PPM 1ra Categoría',
      subtotal_imp_determinado: 'Sub Total Impuestos Determinado Anverso',
      total_determinado: 'Total Determinado',

      // Totales a pagar
      total_pagar_plazo_legal: 'Total a Pagar Dentro del Plazo Legal',
      mas_ipc: 'Más IPC',
      mas_interes_multas: 'Más Intereses y Multas',
      condonacion: 'Condonación',
      total_pagar_recargo: 'Total a Pagar con Recargo',

      // Información adicional del PDF
      num_condonacion: 'N° de Condonación',
      fecha_condonacion: 'Fecha de Condonación',
      porc_condonacion: '% Condonación',
      num_resolucion: 'Número de la Resolución',
      corrige_a_folio: 'Corrige a Folio(s)',
      banco: 'Banco',
      medio_pago: 'Medio de Pago',
      fecha_presentacion: 'Fecha de Presentación',
      tipo_declaracion: 'Tipo de Declaración',
    };
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const categorizeExtraData = (extraData: Record<string, any>) => {
    const categories = {
      cantidades_emitidas: {
        title: 'Cantidades Documentos Emitidos',
        icon: '📤',
        color: 'blue',
        keys: [
          'cant_facturas_emitidas',
          'cant_boletas',
          'cant_recibos_electronicos',
          'cant_notas_credito_emitidas',
          'cant_notas_cred_vales_maq',
          'cant_int_ex_no_grav',
        ],
      },
      cantidades_recibidas: {
        title: 'Cantidades Documentos Recibidos',
        icon: '📥',
        color: 'cyan',
        keys: [
          'cant_facturas_recibidas',
          'cant_fact_recibidas_giro',
          'cant_notas_credito_recibidas',
          'cant_notas_debito_recibidas',
          'cant_form_pago_imp_giro',
        ],
      },
      debitos: {
        title: 'Débitos (IVA a Pagar)',
        icon: '📊',
        color: 'orange',
        keys: [
          'debitos_facturas',
          'debitos_boletas',
          'debitos_recibos_electronicos',
          'debitos_notas_credito',
          'debitos_notas_cred_vales',
          'liquidacion_facturas',
          'total_debitos',
          'monto_sin_der_cred_fiscal',
        ],
      },
      creditos: {
        title: 'Créditos (IVA a Favor)',
        icon: '💰',
        color: 'green',
        keys: [
          'credito_iva_documentos_electronicos',
          'credito_facturas_giro',
          'credito_notas_credito',
          'credito_notas_debito',
          'credito_pago_imp_giro',
          'total_creditos',
        ],
      },
      remanentes: {
        title: 'Remanentes y Recuperos',
        icon: '🔄',
        color: 'purple',
        keys: [
          'remanente_mes_anterior',
          'remanente_credito_fisc',
          'recup_imp_diesel',
          'iva_postergado',
        ],
      },
      determinacion: {
        title: 'Determinación de Impuestos',
        icon: '📝',
        color: 'red',
        keys: [
          'iva_determinado',
          'ppm_neto',
          'retencion_imp_unico',
          'subtotal_imp_determinado',
          'total_determinado',
        ],
      },
      ppm_base: {
        title: 'PPM y Base Imponible',
        icon: '📈',
        color: 'teal',
        keys: [
          'base_imponible',
          'tasa_ppm',
        ],
      },
      totales_pago: {
        title: 'Totales a Pagar',
        icon: '💳',
        color: 'indigo',
        keys: [
          'total_pagar_plazo_legal',
          'mas_ipc',
          'mas_interes_multas',
          'condonacion',
          'total_pagar_recargo',
        ],
      },
      adicional: {
        title: 'Información Adicional',
        icon: 'ℹ️',
        color: 'gray',
        keys: [
          'num_condonacion',
          'fecha_condonacion',
          'porc_condonacion',
          'num_resolucion',
          'corrige_a_folio',
          'banco',
          'medio_pago',
          'fecha_presentacion',
          'tipo_declaracion',
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
            <p className="mt-1 text-sm text-red-700 dark:text-red-400">
              {error instanceof Error ? error.message : 'Error desconocido'}
            </p>
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

                  {/* Extra Data Button */}
                  {hasExtraData(form) && (
                    <div className="mt-3">
                      <button
                        onClick={() => openModal(form)}
                        className="flex w-full items-center justify-center space-x-2 rounded-md border border-blue-300 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-600 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30"
                      >
                        <Info className="h-4 w-4" />
                        <span>Ver Datos del Formulario</span>
                      </button>
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

      {/* Modal for F29 Details */}
      {selectedFormForModal && (() => {
        const form = selectedFormForModal;
        const extractedData = extractF29Data(form.extra_data);
        const { categorized, categories } = categorizeExtraData(extractedData);
        const colorClasses = {
          blue: 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20',
          cyan: 'border-cyan-200 bg-cyan-50 dark:border-cyan-800 dark:bg-cyan-900/20',
          green: 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20',
          purple: 'border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-900/20',
          orange: 'border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-900/20',
          red: 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20',
          indigo: 'border-indigo-200 bg-indigo-50 dark:border-indigo-800 dark:bg-indigo-900/20',
          teal: 'border-teal-200 bg-teal-50 dark:border-teal-800 dark:bg-teal-900/20',
          gray: 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900/50',
        };
        const hasCategories = Object.keys(categorized).length > 0;

        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={closeModal}>
            <div
              className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-lg bg-white shadow-2xl dark:bg-gray-800"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-700 dark:bg-gray-800">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Formulario 29 - {getMonthName(form.period_month)} {form.period_year}
                  </h2>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Folio: {form.sii_folio} • {formatCurrency(form.amount_cents)}
                  </p>
                </div>
                <button
                  onClick={closeModal}
                  className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6">
                {!hasCategories && (
                  <div className="text-center py-8">
                    <p className="text-gray-500 dark:text-gray-400">
                      No se encontraron datos estructurados.
                      <br />
                      Total de campos extraídos: {Object.keys(extractedData).length}
                    </p>
                    {Object.keys(extractedData).length > 0 && (
                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-700">
                          Ver datos raw
                        </summary>
                        <pre className="mt-2 text-left text-xs bg-gray-100 dark:bg-gray-900 p-4 rounded overflow-auto max-h-96">
                          {JSON.stringify(extractedData, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                )}

                <div className="space-y-4">
                  {Object.entries(categorized).map(([categoryKey, items]) => {
                    const categoryInfo = (categories as any)[categoryKey] || {
                      title: 'Otros',
                      icon: '📋',
                      color: 'gray',
                    };

                    return (
                      <div
                        key={categoryKey}
                        className={`rounded-lg border p-4 ${
                          colorClasses[categoryInfo.color as keyof typeof colorClasses]
                        }`}
                      >
                        <div className="mb-3 flex items-center space-x-2">
                          <span className="text-2xl">{categoryInfo.icon}</span>
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {categoryInfo.title}
                          </h3>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                          {items.map(({ key, value }) => (
                            <div
                              key={key}
                              className="rounded-md bg-white/80 p-3 dark:bg-gray-800/80"
                            >
                              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                                {getExtraDataLabel(key)}
                              </p>
                              <p className="mt-1 text-base font-semibold text-gray-900 dark:text-white">
                                {formatExtraDataValue(value)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Modal Footer */}
              <div className="sticky bottom-0 border-t border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-900">
                <div className="flex justify-end space-x-3">
                  {form.has_pdf && form.pdf_storage_url && (
                    <a
                      href={form.pdf_storage_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700"
                    >
                      <Download className="h-4 w-4" />
                      <span>Ver PDF Original</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                  <button
                    onClick={closeModal}
                    className="inline-flex items-center space-x-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

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
