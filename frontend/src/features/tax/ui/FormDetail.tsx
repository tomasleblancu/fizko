import { FileText, ArrowLeft, MessageCircle, Download, Calendar, DollarSign } from 'lucide-react';
import clsx from 'clsx';
import type { F29Form } from "@/shared/hooks/useF29FormsQuery";
import { ChateableWrapper } from '@/shared/ui/ChateableWrapper';
import type { ColorScheme } from "@/shared/hooks/useColorScheme";

interface FormDetailProps {
  form: F29Form;
  onBack: () => void;
  scheme: ColorScheme;
  companyId?: string | null;
}

export function FormDetail({ form, onBack, scheme }: FormDetailProps) {

  const formatAmount = (amountCents: number) => {
    const amount = amountCents;
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPeriod = (periodDisplay: string) => {
    // Convert "2024-01" to "Enero 2024"
    const [year, month] = periodDisplay.split('-');
    const monthNames = [
      'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium";
    switch (status) {
      case 'Vigente':
        return `${baseClasses} bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400`;
      case 'Rectificado':
        return `${baseClasses} bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400`;
      case 'Anulado':
        return `${baseClasses} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`;
      default:
        return `${baseClasses} bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400`;
    }
  };

  const handleDownloadPDF = () => {
    if (form.pdf_url) {
      window.open(form.pdf_url, '_blank');
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-slate-200/60 bg-white/30 pb-4 pt-4 dark:border-slate-800/60 dark:bg-slate-900/30">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={onBack}
                className="flex h-10 w-10 items-center justify-center rounded-full text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                aria-label="Volver a formularios"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg">
                <FileText className="h-6 w-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 truncate">
                  Formulario 29
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-500 truncate">
                  {formatPeriod(form.period_display)}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {form.has_pdf && form.pdf_url && (
                  <button
                    onClick={handleDownloadPDF}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700"
                  >
                    <Download className="h-4 w-4" />
                    PDF
                  </button>
                )}
                <ChateableWrapper
                  message={`Dame información sobre el formulario F29 del periodo ${form.period_display} (folio: ${form.folio})`}
                  contextData={{
                    formId: form.id,
                    folio: form.folio,
                    period: form.period_display,
                    status: form.status,
                  }}
                  uiComponent="f29_form_card"
                  entityId={form.folio}
                  entityType="f29_form"
                >
                  <button className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-emerald-700 flex-shrink-0">
                    <MessageCircle className="h-4 w-4" />
                    Consultar
                  </button>
                </ChateableWrapper>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="font-mono text-slate-700 dark:text-slate-300">
                Folio: {form.folio}
              </span>
              <span className={getStatusBadge(form.status)}>
                {form.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Section */}
      <div className="flex-shrink-0 border-b border-slate-200/60 bg-white/30 py-4 dark:border-slate-800/60 dark:bg-slate-900/30">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {/* Monto Total */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                Monto Total
              </p>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {formatAmount(form.amount_cents)}
            </p>
          </div>

          {/* Fecha de Presentación */}
          {form.submission_date && (
            <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                  Fecha Presentación
                </p>
              </div>
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {new Date(form.submission_date).toLocaleDateString('es-CL', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric'
                })}
              </p>
            </div>
          )}

          {/* PDF Status */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2 mb-2">
              <Download className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                PDF
              </p>
            </div>
            <span className={clsx(
              "inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium",
              form.pdf_download_status === 'downloaded' && form.has_pdf
                ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                : form.pdf_download_status === 'error'
                ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400"
            )}>
              {form.pdf_download_status === 'downloaded' && form.has_pdf ? 'Disponible' :
               form.pdf_download_status === 'error' ? 'Error' : 'Pendiente'}
            </span>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="flex-1 min-h-0 overflow-y-auto py-4 pb-4">
        <div className="space-y-4">
          {/* Basic Info */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
              Información del Formulario
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">
                  Periodo Tributario
                </p>
                <p className="text-sm text-slate-900 dark:text-slate-100">
                  {formatPeriod(form.period_display)}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">
                  Descripción
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Declaración mensual de IVA (Impuesto al Valor Agregado) presentada ante el Servicio de Impuestos Internos.
                </p>
              </div>

              {form.submission_date && (
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 uppercase mb-1">
                    Fecha de Presentación
                  </p>
                  <p className="text-sm text-slate-900 dark:text-slate-100">
                    {new Date(form.submission_date).toLocaleDateString('es-CL', {
                      weekday: 'long',
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Detailed Breakdown - if available */}
          {form.extra_data?.f29_data?.grouped && (
            <>
              {/* Débitos Section */}
              {form.extra_data.f29_data.grouped.debitos && Object.keys(form.extra_data.f29_data.grouped.debitos).length > 0 && (
                <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <h3 className="mb-3 text-sm font-semibold text-rose-700 dark:text-rose-400">
                    Débitos Fiscales
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(form.extra_data.f29_data.grouped.debitos)
                      .filter(([code]) => code !== '538') // Excluir total
                      .map(([code, data]: [string, any]) => (
                        <div key={code} className="flex justify-between items-center py-1.5">
                          <span className="text-xs text-slate-600 dark:text-slate-400">
                            {data.glosa}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            {formatAmount(data.value)}
                          </span>
                        </div>
                      ))}
                    {form.extra_data.f29_data.grouped.debitos['538'] && (
                      <div className="flex justify-between items-center py-2 border-t border-slate-200 dark:border-slate-700 mt-2 pt-2">
                        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                          Total Débitos
                        </span>
                        <span className="text-base font-bold text-rose-700 dark:text-rose-400">
                          {formatAmount(form.extra_data.f29_data.grouped.debitos['538'].value)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Créditos Section */}
              {form.extra_data.f29_data.grouped.creditos && Object.keys(form.extra_data.f29_data.grouped.creditos).length > 0 && (
                <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <h3 className="mb-3 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                    Créditos Fiscales
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(form.extra_data.f29_data.grouped.creditos)
                      .filter(([code]) => !['537', '077'].includes(code)) // Excluir total y remanente
                      .map(([code, data]: [string, any]) => (
                        <div key={code} className="flex justify-between items-center py-1.5">
                          <span className="text-xs text-slate-600 dark:text-slate-400">
                            {data.glosa}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            {formatAmount(data.value)}
                          </span>
                        </div>
                      ))}
                    {form.extra_data.f29_data.grouped.creditos['537'] && (
                      <div className="flex justify-between items-center py-2 border-t border-slate-200 dark:border-slate-700 mt-2 pt-2">
                        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                          Total Créditos
                        </span>
                        <span className="text-base font-bold text-emerald-700 dark:text-emerald-400">
                          {formatAmount(form.extra_data.f29_data.grouped.creditos['537'].value)}
                        </span>
                      </div>
                    )}
                    {form.extra_data.f29_data.grouped.creditos['077'] && (
                      <div className="flex justify-between items-center py-2 bg-emerald-50 dark:bg-emerald-900/20 px-3 rounded-lg mt-2">
                        <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                          Remanente de Crédito Fiscal
                        </span>
                        <span className="text-base font-bold text-emerald-800 dark:text-emerald-300">
                          {formatAmount(form.extra_data.f29_data.grouped.creditos['077'].value)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Summary */}
              {form.extra_data.f29_data.summary && (
                <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                    Resumen de Impuestos
                  </h3>
                  <div className="space-y-2">
                    {form.extra_data.f29_data.summary.iva_determinado !== undefined && (
                      <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-800">
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          IVA Determinado
                        </span>
                        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {formatAmount(form.extra_data.f29_data.summary.iva_determinado)}
                        </span>
                      </div>
                    )}

                    {form.extra_data.f29_data.summary.ppm_neto !== undefined && form.extra_data.f29_data.summary.ppm_neto !== 0 && (
                      <div className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-800">
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          PPM Neto Determinado
                        </span>
                        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {formatAmount(form.extra_data.f29_data.summary.ppm_neto)}
                        </span>
                      </div>
                    )}

                    {form.extra_data.f29_data.summary.total_determinado !== undefined && (
                      <div className="flex justify-between items-center py-2 bg-blue-50 dark:bg-blue-900/20 px-3 rounded-lg mt-2">
                        <span className="text-sm font-semibold text-blue-800 dark:text-blue-300">
                          Total Determinado
                        </span>
                        <span className="text-lg font-bold text-blue-800 dark:text-blue-300">
                          {formatAmount(form.extra_data.f29_data.summary.total_determinado)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Detalles de Condonación */}
              {form.extra_data.f29_data.grouped.pagos && (
                (form.extra_data.f29_data.grouped.pagos['60'] ||
                 form.extra_data.f29_data.grouped.pagos['922'] ||
                 form.extra_data.f29_data.grouped.pagos['915']) && (
                  <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                    <h3 className="mb-3 text-sm font-semibold text-purple-700 dark:text-purple-400">
                      Detalles de Condonación
                    </h3>
                    <div className="space-y-2">
                      {form.extra_data.f29_data.grouped.pagos['60'] && (
                        <div className="flex justify-between items-center py-1.5">
                          <span className="text-xs text-slate-600 dark:text-slate-400">
                            {form.extra_data.f29_data.grouped.pagos['60'].glosa}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            {form.extra_data.f29_data.grouped.pagos['60'].value}
                          </span>
                        </div>
                      )}

                      {form.extra_data.f29_data.grouped.pagos['922'] && (
                        <div className="flex justify-between items-center py-1.5">
                          <span className="text-xs text-slate-600 dark:text-slate-400">
                            {form.extra_data.f29_data.grouped.pagos['922'].glosa}
                          </span>
                          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            {form.extra_data.f29_data.grouped.pagos['922'].value}%
                          </span>
                        </div>
                      )}

                      {form.extra_data.f29_data.grouped.pagos['915'] && (
                        <div className="flex justify-between items-center py-1.5">
                          <span className="text-xs text-slate-600 dark:text-slate-400">
                            {form.extra_data.f29_data.grouped.pagos['915'].glosa}
                          </span>
                          <span className="text-sm font-medium font-mono text-slate-900 dark:text-slate-100">
                            {form.extra_data.f29_data.grouped.pagos['915'].value}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              )}
            </>
          )}

          {/* PDF Status Alerts */}
          {form.has_pdf && form.pdf_url && (
            <div className="rounded-lg border border-blue-100 bg-blue-50/50 p-4 dark:border-blue-900/30 dark:bg-blue-900/10">
              <p className="text-sm text-blue-900 dark:text-blue-300">
                💡 El PDF del formulario está disponible para descarga. Usa el botón "PDF" en el encabezado para acceder al documento oficial.
              </p>
            </div>
          )}

          {!form.has_pdf && form.pdf_download_status === 'pending' && (
            <div className="rounded-lg border border-amber-100 bg-amber-50/50 p-4 dark:border-amber-900/30 dark:bg-amber-900/10">
              <p className="text-sm text-amber-900 dark:text-amber-300">
                ⏳ El PDF del formulario está siendo procesado. Estará disponible pronto.
              </p>
            </div>
          )}

          {form.pdf_download_status === 'error' && (
            <div className="rounded-lg border border-red-100 bg-red-50/50 p-4 dark:border-red-900/30 dark:bg-red-900/10">
              <p className="text-sm text-red-900 dark:text-red-300">
                ⚠️ Hubo un error al descargar el PDF del formulario. Intenta sincronizar nuevamente desde el SII.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
