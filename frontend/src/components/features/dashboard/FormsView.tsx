"use client";

import { FileText, Download, Eye, Calendar, ArrowLeft, ChevronDown, ChevronUp } from "lucide-react";
import React, { useMemo, useState } from "react";
import { useF29Forms } from "@/hooks/useF29Forms";
import { useF29SIIDownloads } from "@/hooks/useF29SIIDownloads";
import { parseLocalDate } from "@/shared/lib/date-utils";
import type { CombinedF29Form, CombinedF29Status } from "@/types/f29";

interface FormsViewProps {
  companyId?: string;
}

export function FormsView({ companyId }: FormsViewProps) {
  const currentYear = new Date().getFullYear();
  const [selectedForm, setSelectedForm] = useState<CombinedF29Form | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    debitos: false,
    creditos: false,
    remanentes: false,
    determinacion: false,
    ppm: false,
    informacion: false,
    documentos_emitidos: false,
    documentos_recibidos: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Fetch F29 forms from local database
  const { data: formsData, isLoading: isLoadingForms } = useF29Forms({
    companyId: companyId || '',
    year: currentYear,
  });

  // Fetch F29 forms from SII downloads
  const { data: siiDownloadsData, isLoading: isLoadingSII } = useF29SIIDownloads({
    companyId: companyId || '',
    year: currentYear,
  });

  const isLoading = isLoadingForms || isLoadingSII;

  // Combine both sources, prioritizing SII downloads
  const combinedForms = useMemo(() => {
    const localForms = formsData?.data || [];
    const siiDownloads = siiDownloadsData?.data || [];

    // Create a map of periods to track which we've seen
    const periodMap = new Map<string, CombinedF29Form>();

    // First, add all SII downloads (priority)
    siiDownloads.forEach((sii) => {
      const periodKey = `${sii.period_year}-${sii.period_month}`;
      periodMap.set(periodKey, {
        id: sii.id,
        period_year: sii.period_year,
        period_month: sii.period_month,
        status: sii.status,
        amount: sii.amount_cents / 100, // Convert cents to pesos
        submission_date: sii.submission_date,
        created_at: sii.created_at,
        source: 'sii',
        sii_folio: sii.sii_folio,
        pdf_storage_url: sii.pdf_storage_url,
        pdf_download_status: sii.pdf_download_status,
        extra_data: sii.extra_data, // Include extra_data from SII
      } as any);
    });

    // Then, add local forms only if period doesn't exist in SII
    localForms.forEach((form) => {
      const periodKey = `${form.period_year}-${form.period_month}`;
      if (!periodMap.has(periodKey)) {
        periodMap.set(periodKey, {
          id: form.id,
          period_year: form.period_year,
          period_month: form.period_month,
          status: form.status,
          amount: form.net_iva,
          submission_date: form.submission_date,
          created_at: form.created_at,
          source: 'local',
          net_iva: form.net_iva,
          total_sales: form.total_sales,
          total_purchases: form.total_purchases,
        });
      }
    });

    // Convert map to array and sort by period (newest first)
    return Array.from(periodMap.values()).sort((a, b) => {
      if (a.period_year !== b.period_year) {
        return b.period_year - a.period_year;
      }
      return b.period_month - a.period_month;
    });
  }, [formsData, siiDownloadsData]);

  const forms = combinedForms;

  // Calculate stats
  const stats = useMemo(() => {
    const totalF29 = forms.length;
    const submitted = forms.filter(f => {
      // Local statuses
      if (f.status === 'submitted' || f.status === 'accepted') return true;
      // SII statuses (vigente = submitted and paid, rectificado = amended)
      if (f.status === 'vigente' || f.status === 'rectificado') return true;
      return false;
    }).length;
    const drafts = forms.filter(f => f.status === 'draft').length;

    // Find next due date (12th of next month)
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 12);

    return {
      totalF29,
      submitted,
      drafts,
      nextDueDate: nextMonth,
    };
  }, [forms]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("es-CL", {
      style: "currency",
      currency: "CLP",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat("es-CL").format(value);
  };

  const formatPeriod = (year: number, month: number) => {
    const date = new Date(year, month - 1, 1);
    return new Intl.DateTimeFormat("es-CL", {
      month: "short",
      year: "numeric",
    }).format(date);
  };

  const formatDate = (dateString: string) => {
    return parseLocalDate(dateString).toLocaleDateString("es-CL");
  };

  // Extract F29 data from extra_data
  const extractF29Data = (extra_data: Record<string, any> | null): Record<string, any> => {
    if (!extra_data) return {};

    // El backend envuelve los datos en un objeto f29_data
    const f29Data = extra_data.f29_data || extra_data;

    const extracted: Record<string, any> = {};

    // Extraer datos de codes (estructura: { "503": { field_name: "cant_facturas_emitidas", value: 2 } })
    if (f29Data.codes) {
      Object.entries(f29Data.codes).forEach(([code, codeData]: [string, any]) => {
        if (codeData && typeof codeData === 'object' && codeData.field_name && codeData.value !== undefined) {
          extracted[codeData.field_name] = codeData.value;
        }
      });
    }

    // Extraer datos del header si existen
    if (f29Data.header) {
      Object.entries(f29Data.header).forEach(([key, value]) => {
        if (!extracted[key]) {
          extracted[key] = value;
        }
      });
    }

    // Extraer datos del summary si existen
    if (f29Data.summary) {
      Object.entries(f29Data.summary).forEach(([key, value]) => {
        if (!extracted[key]) {
          extracted[key] = value;
        }
      });
    }

    return extracted;
  };

  const getFieldLabel = (key: string): string => {
    const labels: Record<string, string> = {
      // Débitos
      debitos_facturas: 'Débitos Facturas Emitidas',
      debitos_boletas: 'Débitos Boletas',
      debitos_recibos_electronicos: 'Déb. Recibos Electrónicos',
      debitos_notas_credito: 'Déb. Notas de Crédito Emitidas',
      debitos_notas_cred_vales: 'Déb. NC Vales Máquinas IVA',
      liquidacion_facturas: 'Liquidación de Facturas',
      total_debitos: 'Total Débitos',
      monto_sin_der_cred_fiscal: 'Monto Sin Derecho a Crédito Fiscal',

      // Créditos
      credito_iva_documentos_electronicos: 'Crédito IVA por Documentos Electrónicos',
      credito_facturas_giro: 'Crédito Recup. y Reint. Facturas del Giro',
      credito_notas_credito: 'Crédito Recup. y Reint. Notas de Crédito',
      credito_notas_debito: 'Crédito Notas de Débito',
      credito_pago_imp_giro: 'Crédito Recup. y Reint. Pago Impuesto del Giro',
      total_creditos: 'Total Créditos',

      // Remanentes
      remanente_mes_anterior: 'Remanente Crédito Mes Anterior',
      remanente_credito_fisc: 'Remanente de Crédito Fiscal',
      recup_imp_diesel: 'Recuperación Impuesto Especial Diesel',
      iva_postergado: 'Monto de IVA Postergado 6 o 12 Cuotas',

      // Determinación
      iva_determinado: 'IVA Determinado',
      ppm_neto: 'PPM Neto Determinado',
      retencion_imp_unico: 'Retención Impuesto Único Trabajadores Art. 74 N°1 LIR',
      retencion_tasa_ley_21133: 'Retención Tasa Ley 21.133 sobre Rentas',
      base_imponible: 'Base Imponible',
      tasa_ppm: 'Tasa PPM 1ra Categoría',
      subtotal_imp_determinado: 'Sub Total Impuestos Determinado Anverso',
      total_determinado: 'Total Determinado',

      // Totales a Pagar
      total_pagar_plazo_legal: 'Total a Pagar Dentro del Plazo Legal',
      mas_ipc: 'Más IPC',
      mas_interes_multas: 'Más Intereses y Multas',
      condonacion: 'Condonación',
      total_pagar_recargo: 'Total a Pagar con Recargo',

      // Cantidades Emitidas
      cant_facturas_emitidas: 'Cant. Facturas Emitidas',
      cant_boletas: 'Cant. Boletas',
      cant_recibos_electronicos: 'Cant. Recibos Electrónicos',
      cant_notas_credito_emitidas: 'Cant. NC Emitidas',
      cant_notas_cred_vales_maq: 'Cant. NC Vales Máquinas',
      cant_int_ex_no_grav: 'Cant. Intereses Exentos No Gravados',

      // Cantidades Recibidas
      cant_facturas_recibidas: 'Cant. Facturas Recibidas',
      cant_fact_recibidas_giro: 'Cant. Facturas Recibidas del Giro',
      cant_notas_credito_recibidas: 'Cant. NC Recibidas',
      cant_notas_debito_recibidas: 'Cant. ND Recibidas',
      cant_form_pago_imp_giro: 'Cant. Formularios Pago Impuesto del Giro',

      // Información adicional del header
      rut: 'RUT',
      razon_social: 'Razón Social',
      direccion: 'Dirección',
      telefono: 'Teléfono',
      correo: 'Correo Electrónico',
      rut_representante: 'RUT Representante',
      num_condonacion: 'N° de Condonación',
      fecha_condonacion: 'Fecha de Condonación',
      porc_condonacion: '% Condonación',
      num_resolucion: 'Número de la Resolución',
      corrige_a_folio: 'Corrige a Folio(s)',
      banco: 'Banco',
      medio_pago: 'Medio de Pago',
      fecha_presentacion: 'Fecha de Presentación',
      tipo_declaracion: 'Tipo de Declaración',
      periodo_display: 'Período',

      // Códigos adicionales
      codigo_condonacion: 'Código de Condonación',
      codigo_543: 'Total de Anticipo, Contrib. Retenidos',
      codigo_556: 'IVA Ant. del Período',
      codigo_573: 'Remanente Ant. Cambio Suj. Per. Sgte.',
    };
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const formatDueDate = (date: Date) => {
    return new Intl.DateTimeFormat("es-CL", {
      day: "numeric",
      month: "short",
    }).format(date);
  };

  const getStatusLabel = (status: CombinedF29Status) => {
    const labels: Record<CombinedF29Status, string> = {
      // Local statuses
      'draft': 'Borrador',
      'pending': 'Pendiente',
      'submitted': 'Presentado',
      'accepted': 'Aceptado',
      'rejected': 'Rechazado',
      // SII statuses
      'vigente': 'Pagado',
      'rectificado': 'Rectificado',
      'anulado': 'Anulado',
    };
    return labels[status] || status;
  };

  const getStatusColor = (status: CombinedF29Status) => {
    const colors: Record<CombinedF29Status, string> = {
      // Local statuses
      'draft': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
      'pending': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      'submitted': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400',
      'accepted': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      'rejected': 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      // SII statuses
      'vigente': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      'rectificado': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      'anulado': 'bg-slate-100 text-slate-800 dark:bg-slate-900/20 dark:text-slate-400',
    };
    return colors[status] || 'bg-slate-100 text-slate-800 dark:bg-slate-900/20 dark:text-slate-400';
  };

  // If form is selected, show detail view
  if (selectedForm) {
    const extractedData = extractF29Data(selectedForm.source === 'sii' && (selectedForm as any).extra_data ? (selectedForm as any).extra_data : null);
    const hasExtractedData = Object.keys(extractedData).length > 0;

    return (
      <div className="space-y-6">
        {/* Back Button */}
        <button
          onClick={() => setSelectedForm(null)}
          className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver a Formularios
        </button>

        {/* Form Header */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <FileText className="h-6 w-6 text-emerald-600" />
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Formulario 29 - {formatPeriod(selectedForm.period_year, selectedForm.period_month)}
                  </h2>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Declaración mensual de IVA
                  </p>
                </div>
              </div>
            </div>
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(selectedForm.status)}`}>
              {getStatusLabel(selectedForm.status)}
            </span>
          </div>

          {/* Form Metadata */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Período</p>
              <p className="mt-1 font-medium text-slate-900 dark:text-white">
                {formatPeriod(selectedForm.period_year, selectedForm.period_month)}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Fecha Creación</p>
              <p className="mt-1 font-medium text-slate-900 dark:text-white">
                {formatDate(selectedForm.created_at)}
              </p>
            </div>
            {selectedForm.submission_date && (
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Fecha Presentación</p>
                <p className="mt-1 font-medium text-slate-900 dark:text-white">
                  {formatDate(selectedForm.submission_date)}
                </p>
              </div>
            )}
            {selectedForm.sii_folio && (
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Folio SII</p>
                <p className="mt-1 font-medium text-slate-900 dark:text-white">
                  {selectedForm.sii_folio}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Financial Details */}
        {hasExtractedData ? (
          <div className="space-y-4">
            {/* Débitos (IVA a Pagar) */}
            {(extractedData.total_debitos || extractedData.debitos_facturas || extractedData.debitos_boletas) && (
              <div className="rounded-lg border border-orange-200 bg-orange-50 p-6 dark:border-orange-800 dark:bg-orange-900/20">
                <button
                  onClick={() => toggleSection('debitos')}
                  className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">📊</span>
                    Débitos (IVA a Pagar)
                  </div>
                  {expandedSections.debitos ? (
                    <ChevronUp className="h-5 w-5" />
                  ) : (
                    <ChevronDown className="h-5 w-5" />
                  )}
                </button>
                {!expandedSections.debitos && extractedData.total_debitos !== undefined && (
                  <div className="rounded-lg bg-orange-100 p-3 dark:bg-orange-800/50">
                    <p className="text-xs font-medium text-orange-700 dark:text-orange-400">{getFieldLabel('total_debitos')}</p>
                    <p className="mt-1 text-xl font-bold text-orange-900 dark:text-orange-300">
                      {formatCurrency(extractedData.total_debitos)}
                    </p>
                  </div>
                )}
                {expandedSections.debitos && (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {extractedData.debitos_facturas !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('debitos_facturas')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.debitos_facturas)}
                      </p>
                    </div>
                  )}
                  {extractedData.debitos_boletas !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('debitos_boletas')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.debitos_boletas)}
                      </p>
                    </div>
                  )}
                  {extractedData.debitos_recibos_electronicos !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('debitos_recibos_electronicos')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.debitos_recibos_electronicos)}
                      </p>
                    </div>
                  )}
                  {extractedData.debitos_notas_credito !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('debitos_notas_credito')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.debitos_notas_credito)}
                      </p>
                    </div>
                  )}
                  {extractedData.debitos_notas_cred_vales !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('debitos_notas_cred_vales')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.debitos_notas_cred_vales)}
                      </p>
                    </div>
                  )}
                  {extractedData.liquidacion_facturas !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('liquidacion_facturas')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.liquidacion_facturas)}
                      </p>
                    </div>
                  )}
                  {extractedData.monto_sin_der_cred_fiscal !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('monto_sin_der_cred_fiscal')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.monto_sin_der_cred_fiscal)}
                      </p>
                    </div>
                  )}
                  {extractedData.total_debitos !== undefined && (
                    <div className="rounded-lg bg-orange-100 p-3 dark:bg-orange-800/50">
                      <p className="text-xs font-medium text-orange-700 dark:text-orange-400">{getFieldLabel('total_debitos')}</p>
                      <p className="mt-1 text-xl font-bold text-orange-900 dark:text-orange-300">
                        {formatCurrency(extractedData.total_debitos)}
                      </p>
                    </div>
                  )}
                  </div>
                )}
              </div>
            )}

            {/* Créditos (IVA a Favor) */}
            {!!(extractedData.total_creditos || extractedData.credito_iva_documentos_electronicos || extractedData.credito_facturas_giro) && (
              <div className="rounded-lg border border-green-200 bg-green-50 p-6 dark:border-green-800 dark:bg-green-900/20">
                <button
                  onClick={() => toggleSection('creditos')}
                  className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">💰</span>
                    Créditos (IVA a Favor)
                  </div>
                  {expandedSections.creditos ? (
                    <ChevronUp className="h-5 w-5" />
                  ) : (
                    <ChevronDown className="h-5 w-5" />
                  )}
                </button>
                {!expandedSections.creditos && extractedData.total_creditos !== undefined && (
                  <div className="rounded-lg bg-green-100 p-3 dark:bg-green-800/50">
                    <p className="text-xs font-medium text-green-700 dark:text-green-400">{getFieldLabel('total_creditos')}</p>
                    <p className="mt-1 text-xl font-bold text-green-900 dark:text-green-300">
                      {formatCurrency(extractedData.total_creditos)}
                    </p>
                  </div>
                )}
                {expandedSections.creditos && (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {extractedData.credito_iva_documentos_electronicos !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('credito_iva_documentos_electronicos')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.credito_iva_documentos_electronicos)}
                      </p>
                    </div>
                  )}
                  {extractedData.credito_facturas_giro !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('credito_facturas_giro')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.credito_facturas_giro)}
                      </p>
                    </div>
                  )}
                  {extractedData.credito_notas_credito !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('credito_notas_credito')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.credito_notas_credito)}
                      </p>
                    </div>
                  )}
                  {extractedData.credito_notas_debito !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('credito_notas_debito')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.credito_notas_debito)}
                      </p>
                    </div>
                  )}
                  {extractedData.credito_pago_imp_giro !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('credito_pago_imp_giro')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.credito_pago_imp_giro)}
                      </p>
                    </div>
                  )}
                  {extractedData.total_creditos !== undefined && (
                    <div className="rounded-lg bg-green-100 p-3 dark:bg-green-800/50">
                      <p className="text-xs font-medium text-green-700 dark:text-green-400">{getFieldLabel('total_creditos')}</p>
                      <p className="mt-1 text-xl font-bold text-green-900 dark:text-green-300">
                        {formatCurrency(extractedData.total_creditos)}
                      </p>
                    </div>
                  )}
                  </div>
                )}
              </div>
            )}

            {/* Remanentes y Recuperos */}
            {(extractedData.remanente_mes_anterior || extractedData.remanente_credito_fisc || extractedData.recup_imp_diesel || extractedData.iva_postergado) && (
              <div className="rounded-lg border border-purple-200 bg-purple-50 p-6 dark:border-purple-800 dark:bg-purple-900/20">
                <button
                  onClick={() => toggleSection('remanentes')}
                  className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">🔄</span>
                    Remanentes y Recuperos
                  </div>
                  {expandedSections.remanentes ? (
                    <ChevronUp className="h-5 w-5" />
                  ) : (
                    <ChevronDown className="h-5 w-5" />
                  )}
                </button>
                {!expandedSections.remanentes && (extractedData.remanente_mes_anterior !== undefined || extractedData.remanente_credito_fisc !== undefined) && (
                  <div className="rounded-lg bg-purple-100 p-3 dark:bg-purple-800/50">
                    <p className="text-xs font-medium text-purple-700 dark:text-purple-400">Total Remanentes</p>
                    <p className="mt-1 text-xl font-bold text-purple-900 dark:text-purple-300">
                      {formatCurrency((extractedData.remanente_mes_anterior || 0) + (extractedData.remanente_credito_fisc || 0))}
                    </p>
                  </div>
                )}
                {expandedSections.remanentes && (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {extractedData.remanente_mes_anterior !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('remanente_mes_anterior')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.remanente_mes_anterior)}
                      </p>
                    </div>
                  )}
                  {extractedData.remanente_credito_fisc !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('remanente_credito_fisc')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.remanente_credito_fisc)}
                      </p>
                    </div>
                  )}
                  {extractedData.recup_imp_diesel !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('recup_imp_diesel')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.recup_imp_diesel)}
                      </p>
                    </div>
                  )}
                  {extractedData.iva_postergado !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('iva_postergado')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.iva_postergado)}
                      </p>
                    </div>
                  )}
                  </div>
                )}
              </div>
            )}

            {/* Determinación de Impuestos */}
            {(extractedData.iva_determinado || extractedData.ppm_neto || extractedData.total_determinado || extractedData.retencion_tasa_ley_21133) && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20">
                <button
                  onClick={() => toggleSection('determinacion')}
                  className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">📝</span>
                    Determinación de Impuestos
                  </div>
                  {expandedSections.determinacion ? (
                    <ChevronUp className="h-5 w-5" />
                  ) : (
                    <ChevronDown className="h-5 w-5" />
                  )}
                </button>
                {!expandedSections.determinacion && extractedData.total_determinado !== undefined && (
                  <div className="rounded-lg bg-red-100 p-3 dark:bg-red-800/50">
                    <p className="text-xs font-medium text-red-700 dark:text-red-400">{getFieldLabel('total_determinado')}</p>
                    <p className="mt-1 text-xl font-bold text-red-900 dark:text-red-300">
                      {formatCurrency(extractedData.total_determinado)}
                    </p>
                  </div>
                )}
                {expandedSections.determinacion && (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {extractedData.iva_determinado !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('iva_determinado')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.iva_determinado)}
                      </p>
                    </div>
                  )}
                  {extractedData.ppm_neto !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('ppm_neto')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.ppm_neto)}
                      </p>
                    </div>
                  )}
                  {extractedData.retencion_imp_unico !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('retencion_imp_unico')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.retencion_imp_unico)}
                      </p>
                    </div>
                  )}
                  {extractedData.retencion_tasa_ley_21133 !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('retencion_tasa_ley_21133')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.retencion_tasa_ley_21133)}
                      </p>
                    </div>
                  )}
                  {extractedData.codigo_543 !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('codigo_543')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.codigo_543)}
                      </p>
                    </div>
                  )}
                  {extractedData.codigo_556 !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('codigo_556')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.codigo_556)}
                      </p>
                    </div>
                  )}
                  {extractedData.codigo_573 !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('codigo_573')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.codigo_573)}
                      </p>
                    </div>
                  )}
                  {extractedData.subtotal_imp_determinado !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('subtotal_imp_determinado')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.subtotal_imp_determinado)}
                      </p>
                    </div>
                  )}
                  {extractedData.total_determinado !== undefined && (
                    <div className="rounded-lg bg-red-100 p-3 dark:bg-red-800/50">
                      <p className="text-xs font-medium text-red-700 dark:text-red-400">{getFieldLabel('total_determinado')}</p>
                      <p className="mt-1 text-xl font-bold text-red-900 dark:text-red-300">
                        {formatCurrency(extractedData.total_determinado)}
                      </p>
                    </div>
                  )}
                  </div>
                )}
              </div>
            )}

            {/* PPM y Base Imponible */}
            {(extractedData.base_imponible || extractedData.tasa_ppm) && (
              <div className="rounded-lg border border-teal-200 bg-teal-50 p-6 dark:border-teal-800 dark:bg-teal-900/20">
                <button
                  onClick={() => toggleSection('ppm')}
                  className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">📈</span>
                    PPM y Base Imponible
                  </div>
                  {expandedSections.ppm ? (
                    <ChevronUp className="h-5 w-5" />
                  ) : (
                    <ChevronDown className="h-5 w-5" />
                  )}
                </button>
                {!expandedSections.ppm && extractedData.ppm_neto !== undefined && (
                  <div className="rounded-lg bg-teal-100 p-3 dark:bg-teal-800/50">
                    <p className="text-xs font-medium text-teal-700 dark:text-teal-400">PPM Neto</p>
                    <p className="mt-1 text-xl font-bold text-teal-900 dark:text-teal-300">
                      {formatCurrency(extractedData.ppm_neto)}
                    </p>
                  </div>
                )}
                {expandedSections.ppm && (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {extractedData.base_imponible !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('base_imponible')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.base_imponible)}
                      </p>
                    </div>
                  )}
                  {extractedData.tasa_ppm !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('tasa_ppm')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {(extractedData.tasa_ppm * 100).toFixed(2)}%
                      </p>
                    </div>
                  )}
                  </div>
                )}
              </div>
            )}

            {/* Total a Pagar - NO TOGGLE per user requirement */}
            {(extractedData.total_pagar_plazo_legal || extractedData.mas_ipc || extractedData.mas_interes_multas || extractedData.total_pagar_recargo) && (
              <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-6 dark:border-indigo-800 dark:bg-indigo-900/20">
                <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-white">
                  <span className="text-2xl">💳</span>
                  Totales a Pagar
                </h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {extractedData.total_pagar_plazo_legal !== undefined && (
                    <div className="rounded-lg bg-indigo-100 p-4 dark:bg-indigo-800/50">
                      <p className="text-sm font-medium text-indigo-700 dark:text-indigo-400">{getFieldLabel('total_pagar_plazo_legal')}</p>
                      <p className="mt-2 text-2xl font-bold text-indigo-900 dark:text-indigo-300">
                        {formatCurrency(extractedData.total_pagar_plazo_legal)}
                      </p>
                    </div>
                  )}
                  {extractedData.mas_ipc !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('mas_ipc')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.mas_ipc)}
                      </p>
                    </div>
                  )}
                  {extractedData.mas_interes_multas !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('mas_interes_multas')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.mas_interes_multas)}
                      </p>
                    </div>
                  )}
                  {extractedData.condonacion !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('condonacion')}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(extractedData.condonacion)}
                      </p>
                    </div>
                  )}
                  {extractedData.total_pagar_recargo !== undefined && (
                    <div className="rounded-lg bg-indigo-100 p-4 dark:bg-indigo-800/50">
                      <p className="text-sm font-medium text-indigo-700 dark:text-indigo-400">{getFieldLabel('total_pagar_recargo')}</p>
                      <p className="mt-2 text-2xl font-bold text-indigo-900 dark:text-indigo-300">
                        {formatCurrency(extractedData.total_pagar_recargo)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Información Adicional */}
            {(extractedData.tipo_declaracion || extractedData.banco || extractedData.razon_social || extractedData.rut || extractedData.direccion ||
              extractedData.num_condonacion || extractedData.corrige_a_folio || extractedData.medio_pago) && (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 dark:border-gray-700 dark:bg-gray-900/20">
                <button
                  onClick={() => toggleSection('informacion')}
                  className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">ℹ️</span>
                    Información Adicional
                  </div>
                  {expandedSections.informacion ? (
                    <ChevronUp className="h-5 w-5" />
                  ) : (
                    <ChevronDown className="h-5 w-5" />
                  )}
                </button>
                {!expandedSections.informacion && extractedData.razon_social && (
                  <div className="rounded-lg bg-gray-100 p-3 dark:bg-gray-800/50">
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-400">Razón Social</p>
                    <p className="mt-1 text-lg font-bold text-gray-900 dark:text-gray-300">
                      {extractedData.razon_social}
                    </p>
                  </div>
                )}
                {expandedSections.informacion && (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {extractedData.tipo_declaracion !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('tipo_declaracion')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.tipo_declaracion}
                      </p>
                    </div>
                  )}
                  {extractedData.banco !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('banco')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.banco}
                      </p>
                    </div>
                  )}
                  {extractedData.razon_social !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('razon_social')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.razon_social}
                      </p>
                    </div>
                  )}
                  {extractedData.rut !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('rut')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.rut}
                      </p>
                    </div>
                  )}
                  {extractedData.direccion !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('direccion')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.direccion}
                      </p>
                    </div>
                  )}
                  {extractedData.periodo_display !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('periodo_display')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.periodo_display}
                      </p>
                    </div>
                  )}
                  {extractedData.num_condonacion !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('num_condonacion')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.num_condonacion}
                      </p>
                    </div>
                  )}
                  {extractedData.fecha_condonacion !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('fecha_condonacion')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.fecha_condonacion}
                      </p>
                    </div>
                  )}
                  {extractedData.porc_condonacion !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('porc_condonacion')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.porc_condonacion}%
                      </p>
                    </div>
                  )}
                  {extractedData.num_resolucion !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('num_resolucion')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.num_resolucion}
                      </p>
                    </div>
                  )}
                  {extractedData.corrige_a_folio !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('corrige_a_folio')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.corrige_a_folio}
                      </p>
                    </div>
                  )}
                  {extractedData.medio_pago !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('medio_pago')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.medio_pago}
                      </p>
                    </div>
                  )}
                  {extractedData.telefono !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('telefono')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.telefono}
                      </p>
                    </div>
                  )}
                  {extractedData.correo !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('correo')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.correo}
                      </p>
                    </div>
                  )}
                  {extractedData.rut_representante !== undefined && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('rut_representante')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.rut_representante}
                      </p>
                    </div>
                  )}
                  {extractedData.codigo_condonacion !== undefined && extractedData.codigo_condonacion !== null && (
                    <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                      <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('codigo_condonacion')}</p>
                      <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
                        {extractedData.codigo_condonacion}
                      </p>
                    </div>
                  )}
                  </div>
                )}
              </div>
            )}

            {/* Cantidades de Documentos */}
            {(extractedData.cant_facturas_emitidas || extractedData.cant_boletas || extractedData.cant_facturas_recibidas || extractedData.cant_recibos_electronicos) && (
              <div className="space-y-4">
                {/* Documentos Emitidos */}
                {(extractedData.cant_facturas_emitidas || extractedData.cant_boletas || extractedData.cant_recibos_electronicos || extractedData.cant_notas_credito_emitidas) && (
                  <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 dark:border-blue-800 dark:bg-blue-900/20">
                    <button
                      onClick={() => toggleSection('documentos_emitidos')}
                      className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">📤</span>
                        Documentos Emitidos
                      </div>
                      {expandedSections.documentos_emitidos ? (
                        <ChevronUp className="h-5 w-5" />
                      ) : (
                        <ChevronDown className="h-5 w-5" />
                      )}
                    </button>
                    {!expandedSections.documentos_emitidos && extractedData.cant_facturas_emitidas !== undefined && (
                      <div className="rounded-lg bg-blue-100 p-3 dark:bg-blue-800/50">
                        <p className="text-xs font-medium text-blue-700 dark:text-blue-400">Cant. Facturas Emitidas</p>
                        <p className="mt-1 text-xl font-bold text-blue-900 dark:text-blue-300">
                          {formatNumber(extractedData.cant_facturas_emitidas)}
                        </p>
                      </div>
                    )}
                    {expandedSections.documentos_emitidos && (
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      {extractedData.cant_facturas_emitidas !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_facturas_emitidas')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_facturas_emitidas.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_boletas !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_boletas')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_boletas.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_recibos_electronicos !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_recibos_electronicos')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_recibos_electronicos.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_notas_credito_emitidas !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_notas_credito_emitidas')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_notas_credito_emitidas.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_notas_cred_vales_maq !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_notas_cred_vales_maq')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_notas_cred_vales_maq.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_int_ex_no_grav !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_int_ex_no_grav')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_int_ex_no_grav.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                    </div>
                    )}
                  </div>
                )}

                {/* Documentos Recibidos */}
                {(extractedData.cant_facturas_recibidas || extractedData.cant_fact_recibidas_giro || extractedData.cant_notas_credito_recibidas) && (
                  <div className="rounded-lg border border-cyan-200 bg-cyan-50 p-6 dark:border-cyan-800 dark:bg-cyan-900/20">
                    <button
                      onClick={() => toggleSection('documentos_recibidos')}
                      className="mb-4 flex w-full items-center justify-between gap-2 text-lg font-semibold text-slate-900 dark:text-white hover:opacity-80"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">📥</span>
                        Documentos Recibidos
                      </div>
                      {expandedSections.documentos_recibidos ? (
                        <ChevronUp className="h-5 w-5" />
                      ) : (
                        <ChevronDown className="h-5 w-5" />
                      )}
                    </button>
                    {!expandedSections.documentos_recibidos && extractedData.cant_facturas_recibidas !== undefined && (
                      <div className="rounded-lg bg-cyan-100 p-3 dark:bg-cyan-800/50">
                        <p className="text-xs font-medium text-cyan-700 dark:text-cyan-400">Cant. Facturas Recibidas</p>
                        <p className="mt-1 text-xl font-bold text-cyan-900 dark:text-cyan-300">
                          {formatNumber(extractedData.cant_facturas_recibidas)}
                        </p>
                      </div>
                    )}
                    {expandedSections.documentos_recibidos && (
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      {extractedData.cant_facturas_recibidas !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_facturas_recibidas')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_facturas_recibidas.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_fact_recibidas_giro !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_fact_recibidas_giro')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_fact_recibidas_giro.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_notas_credito_recibidas !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_notas_credito_recibidas')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_notas_credito_recibidas.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_notas_debito_recibidas !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_notas_debito_recibidas')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_notas_debito_recibidas.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      {extractedData.cant_form_pago_imp_giro !== undefined && (
                        <div className="rounded-lg bg-white/80 p-3 dark:bg-slate-800/80">
                          <p className="text-xs text-slate-600 dark:text-slate-400">{getFieldLabel('cant_form_pago_imp_giro')}</p>
                          <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                            {extractedData.cant_form_pago_imp_giro.toLocaleString('es-CL')}
                          </p>
                        </div>
                      )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          // Fallback to basic data if no extra_data
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
              Resumen Financiero
            </h3>
            <div className="space-y-6">
              {selectedForm.total_sales !== undefined && (
                <div>
                  <h4 className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Ventas</h4>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800/50">
                      <p className="text-xs text-slate-600 dark:text-slate-400">Ventas Totales</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(selectedForm.total_sales)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
              {selectedForm.total_purchases !== undefined && (
                <div>
                  <h4 className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Compras</h4>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800/50">
                      <p className="text-xs text-slate-600 dark:text-slate-400">Compras Totales</p>
                      <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(selectedForm.total_purchases)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
              <div className="border-t border-slate-200 pt-6 dark:border-slate-700">
                <h4 className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">IVA</h4>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {selectedForm.net_iva !== undefined && (
                    <div className="rounded-lg bg-emerald-50 p-3 dark:bg-emerald-900/20">
                      <p className="text-xs text-emerald-700 dark:text-emerald-400">IVA Neto</p>
                      <p className="mt-1 text-lg font-semibold text-emerald-900 dark:text-emerald-300">
                        {formatCurrency(selectedForm.net_iva)}
                      </p>
                    </div>
                  )}
                  <div className={`rounded-lg p-3 ${
                    selectedForm.amount >= 0
                      ? 'bg-red-50 dark:bg-red-900/20'
                      : 'bg-green-50 dark:bg-green-900/20'
                  }`}>
                    <p className={`text-xs ${
                      selectedForm.amount >= 0
                        ? 'text-red-700 dark:text-red-400'
                        : 'text-green-700 dark:text-green-400'
                    }`}>
                      {selectedForm.amount >= 0 ? 'A Pagar' : 'A Favor'}
                    </p>
                    <p className={`mt-1 text-lg font-semibold ${
                      selectedForm.amount >= 0
                        ? 'text-red-900 dark:text-red-300'
                        : 'text-green-900 dark:text-green-300'
                    }`}>
                      {formatCurrency(Math.abs(selectedForm.amount))}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        {selectedForm.pdf_storage_url && (
          <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
              Documentos
            </h3>
            <div className="flex items-center gap-3">
              <a
                href={selectedForm.pdf_storage_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
              >
                <Download className="h-4 w-4" />
                Descargar PDF
              </a>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Formularios Tributarios
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Gestiona tus declaraciones mensuales y anuales
          </p>
        </div>
        <button className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">
          Nueva Declaración
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Total F29</p>
          <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
            {isLoading ? "-" : stats.totalF29}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Presentados</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600">
            {isLoading ? "-" : stats.submitted}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Borradores</p>
          <p className="mt-1 text-2xl font-bold text-yellow-600">
            {isLoading ? "-" : stats.drafts}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Próximo Vencimiento</p>
          <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white">
            {formatDueDate(stats.nextDueDate)}
          </p>
        </div>
      </div>

      {/* Forms Table */}
      <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
          </div>
        ) : forms.length === 0 ? (
          <div className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" />
            <p className="mt-2 text-slate-600 dark:text-slate-400">
              No hay formularios registrados para {currentYear}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Tipo
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Período
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Estado
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-slate-600 dark:text-slate-400">
                    Fecha Creación
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-medium text-slate-600 dark:text-slate-400">
                    Impuesto a Pagar
                  </th>
                </tr>
              </thead>
              <tbody>
                {forms.map((form) => {
                  // Extract total_pagar_plazo_legal from extra_data if available
                  const extractedData = extractF29Data(form.source === 'sii' && (form as any).extra_data ? (form as any).extra_data : null);
                  const displayAmount = extractedData.total_pagar_plazo_legal !== undefined
                    ? extractedData.total_pagar_plazo_legal
                    : form.amount;

                  return (
                    <tr
                      key={form.id}
                      onClick={() => setSelectedForm(form)}
                      className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-slate-400" />
                          <span className="font-medium text-slate-900 dark:text-white">
                            F29
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                        {formatPeriod(form.period_year, form.period_month)}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(form.status)}`}>
                          {getStatusLabel(form.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(form.created_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right font-medium text-slate-900 dark:text-white">
                        {formatCurrency(displayAmount)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
