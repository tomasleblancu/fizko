"use client";

import { FileText } from "lucide-react";
import React, { useMemo, useState } from "react";
import { useF29Forms } from "@/hooks/useF29Forms";
import { useF29SIIDownloads } from "@/hooks/useF29SIIDownloads";
import { parseLocalDate } from "@/shared/lib/date-utils";
import type { CombinedF29Form, CombinedF29Status } from "@/types/f29";
import { FormsListMobile } from "./components/FormsListMobile";
import { FormsListDesktop } from "./components/FormsListDesktop";
import { FormDetailStatement } from "./components/FormDetailStatement";

interface FormsViewProps {
  companyId?: string;
}

export function FormsView({ companyId }: FormsViewProps) {
  const currentYear = new Date().getFullYear();
  const [selectedForm, setSelectedForm] = useState<CombinedF29Form | null>(null);

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

    return (
      <FormDetailStatement
        form={selectedForm}
        extractedData={extractedData}
        formatPeriod={formatPeriod}
        formatDate={formatDate}
        formatCurrency={formatCurrency}
        getStatusColor={getStatusColor}
        getStatusLabel={getStatusLabel}
        onBack={() => setSelectedForm(null)}
      />
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
          <>
            <FormsListMobile
              forms={forms}
              onSelectForm={setSelectedForm}
              formatPeriod={formatPeriod}
              formatCurrency={formatCurrency}
              getStatusColor={getStatusColor}
              getStatusLabel={getStatusLabel}
              extractF29Data={extractF29Data}
            />
            <FormsListDesktop
              forms={forms}
              onSelectForm={setSelectedForm}
              formatPeriod={formatPeriod}
              formatDate={formatDate}
              formatCurrency={formatCurrency}
              getStatusColor={getStatusColor}
              getStatusLabel={getStatusLabel}
              extractF29Data={extractF29Data}
            />
          </>
        )}
      </div>
    </div>
  );
}
