/**
 * Form Detail Statement Component
 * Displays F29 details in a financial statement format (like income statement)
 * Conversational order: from revenue to final payment
 */

import React from "react";
import { ArrowLeft, FileText, Download } from "lucide-react";
import type { CombinedF29Form, CombinedF29Status } from "@/types/f29";

interface FormDetailStatementProps {
  form: CombinedF29Form;
  extractedData: Record<string, any>;
  formatPeriod: (year: number, month: number) => string;
  formatDate: (dateString: string) => string;
  formatCurrency: (amount: number) => string;
  getStatusColor: (status: CombinedF29Status) => string;
  getStatusLabel: (status: CombinedF29Status) => string;
  onBack: () => void;
}

export function FormDetailStatement({
  form,
  extractedData,
  formatPeriod,
  formatDate,
  formatCurrency,
  getStatusColor,
  getStatusLabel,
  onBack,
}: FormDetailStatementProps) {
  const hasExtractedData = Object.keys(extractedData).length > 0;

  // Helper to render a line item
  const LineItem = ({ label, value, isBold = false, isSubtotal = false, isTotal = false }: {
    label: string;
    value: number | string;
    isBold?: boolean;
    isSubtotal?: boolean;
    isTotal?: boolean;
  }) => {
    const textColor = isTotal
      ? "text-indigo-900 dark:text-indigo-300"
      : isSubtotal
      ? "text-slate-800 dark:text-slate-200"
      : "text-slate-700 dark:text-slate-300";

    const bgColor = isTotal
      ? "bg-indigo-50 dark:bg-indigo-900/30"
      : isSubtotal
      ? "bg-slate-100 dark:bg-slate-800/50"
      : "";

    return (
      <div className={`flex justify-between items-center py-2.5 px-4 ${bgColor}`}>
        <span className={`${isBold || isSubtotal || isTotal ? "font-semibold" : "font-normal"} ${textColor}`}>
          {label}
        </span>
        <span className={`${isBold || isSubtotal || isTotal ? "font-bold" : "font-medium"} ${textColor} tabular-nums`}>
          {typeof value === 'number' ? formatCurrency(value) : value}
        </span>
      </div>
    );
  };

  const Section = ({ title, icon }: { title: string; icon: string }) => (
    <div className="flex items-center gap-2 mt-6 mb-3 px-4">
      <span className="text-xl">{icon}</span>
      <h3 className="text-base font-bold text-slate-900 dark:text-white uppercase tracking-wide">
        {title}
      </h3>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver a Formularios
      </button>

      {/* Form Header */}
      <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-emerald-500 text-white">
                <FileText className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Formulario 29
                </h2>
                <p className="text-lg font-semibold text-emerald-700 dark:text-emerald-400 mt-0.5">
                  {formatPeriod(form.period_year, form.period_month)}
                </p>
              </div>
            </div>
            <span className={`rounded-full px-3 py-1.5 text-sm font-medium ${getStatusColor(form.status)}`}>
              {getStatusLabel(form.status)}
            </span>
          </div>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-6 bg-slate-50 dark:bg-slate-800/50">
          {form.submission_date && (
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Fecha Presentación</p>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {formatDate(form.submission_date)}
              </p>
            </div>
          )}
          {form.sii_folio && (
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Folio SII</p>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {form.sii_folio}
              </p>
            </div>
          )}
          {extractedData.razon_social && (
            <div className="col-span-2">
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Razón Social</p>
              <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                {extractedData.razon_social}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Financial Statement */}
      {hasExtractedData ? (
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 overflow-hidden">
          <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Declaración Mensual de Impuestos
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
              Flujo conversacional del cálculo
            </p>
          </div>

          <div>
            {/* DÉBITOS FISCALES */}
            {extractedData.total_debitos !== undefined && (
              <>
                <Section title="Débitos Fiscales (IVA Ventas)" icon="📊" />

                {extractedData.debitos_facturas !== undefined && (
                  <LineItem label="IVA Facturas" value={extractedData.debitos_facturas} />
                )}
                {extractedData.debitos_boletas !== undefined && (
                  <LineItem label="IVA Boletas" value={extractedData.debitos_boletas} />
                )}
                {extractedData.debitos_recibos_electronicos !== undefined && (
                  <LineItem label="IVA Recibos Electrónicos" value={extractedData.debitos_recibos_electronicos} />
                )}
                {extractedData.liquidacion_facturas !== undefined && (
                  <LineItem label="IVA Liquidación Facturas" value={extractedData.liquidacion_facturas} />
                )}
                {extractedData.debitos_notas_credito !== undefined && extractedData.debitos_notas_credito !== 0 && (
                  <LineItem label="(-) Notas de Crédito" value={-extractedData.debitos_notas_credito} />
                )}
                {extractedData.debitos_notas_cred_vales !== undefined && extractedData.debitos_notas_cred_vales !== 0 && (
                  <LineItem label="(-) NC Vales Máquinas" value={-extractedData.debitos_notas_cred_vales} />
                )}

                <LineItem
                  label="Total Débito Fiscal"
                  value={extractedData.total_debitos}
                  isSubtotal
                />
              </>
            )}

            {/* CRÉDITOS FISCALES */}
            {extractedData.total_creditos !== undefined && (
              <>
                <Section title="Créditos Fiscales (IVA Compras)" icon="💰" />

                {extractedData.credito_facturas_giro !== undefined && (
                  <LineItem label="IVA Activo Fijo" value={extractedData.credito_facturas_giro} />
                )}
                {extractedData.credito_pago_imp_giro !== undefined && (
                  <LineItem label="IVA Uso Común" value={extractedData.credito_pago_imp_giro} />
                )}
                {extractedData.credito_notas_credito !== undefined && extractedData.credito_notas_credito !== 0 && (
                  <LineItem label="(-) Notas de Crédito" value={-extractedData.credito_notas_credito} />
                )}
                {extractedData.credito_notas_debito !== undefined && extractedData.credito_notas_debito !== 0 && (
                  <LineItem label="(+) Notas de Débito" value={extractedData.credito_notas_debito} />
                )}

                {/* IVA Crédito Fiscal = suma de componentes anteriores */}
                {extractedData.credito_iva_documentos_electronicos !== undefined && (
                  <LineItem
                    label="IVA Crédito Fiscal"
                    value={extractedData.credito_iva_documentos_electronicos}
                    isBold
                  />
                )}

                {/* Remanente Mes Anterior (se suma al crédito) */}
                {extractedData.remanente_mes_anterior !== undefined && extractedData.remanente_mes_anterior !== 0 && (
                  <LineItem label="Remanente Mes Anterior" value={extractedData.remanente_mes_anterior} />
                )}

                <LineItem
                  label="Total Crédito Fiscal"
                  value={extractedData.total_creditos}
                  isSubtotal
                />
              </>
            )}

            {/* IVA DETERMINADO */}
            {extractedData.iva_determinado !== undefined && (
              <>
                <Section title="Determinación del IVA" icon="🧮" />

                <LineItem
                  label="IVA Determinado (Débito - Crédito)"
                  value={extractedData.iva_determinado}
                  isBold
                />

                {/* Remanente para próximo mes (si es negativo) */}
                {extractedData.iva_determinado < 0 && (
                  <LineItem
                    label="Remanente Crédito Fiscal (próximo mes)"
                    value={Math.abs(extractedData.iva_determinado)}
                    isBold
                  />
                )}
              </>
            )}

            {/* OTROS CRÉDITOS Y AJUSTES */}
            {(extractedData.remanente_credito_fisc !== undefined || extractedData.recup_imp_diesel !== undefined || extractedData.iva_postergado !== undefined) && (
              <>
                <Section title="Otros Créditos y Ajustes" icon="🔄" />

                {extractedData.remanente_credito_fisc !== undefined && extractedData.remanente_credito_fisc !== 0 && (
                  <LineItem label="(-) Remanente Crédito Fiscal" value={-extractedData.remanente_credito_fisc} />
                )}
                {extractedData.recup_imp_diesel !== undefined && extractedData.recup_imp_diesel !== 0 && (
                  <LineItem label="(-) Recuperación Impuesto Diesel" value={-extractedData.recup_imp_diesel} />
                )}
                {extractedData.iva_postergado !== undefined && extractedData.iva_postergado !== 0 && (
                  <LineItem label="IVA Postergado" value={extractedData.iva_postergado} />
                )}
              </>
            )}

            {/* PPM Y RETENCIONES */}
            {(extractedData.ppm_neto !== undefined || extractedData.retencion_imp_unico !== undefined || extractedData.retencion_tasa_ley_21133 !== undefined) && (
              <>
                <Section title="PPM y Retenciones" icon="📈" />

                {extractedData.ppm_neto !== undefined && extractedData.ppm_neto !== 0 && (
                  <LineItem
                    label={`PPM (${extractedData.tasa_ppm ? `${extractedData.tasa_ppm.toFixed(3)}%` : '0.125%'} Ingresos Netos)`}
                    value={extractedData.ppm_neto}
                  />
                )}
                {extractedData.retencion_imp_unico !== undefined && extractedData.retencion_imp_unico !== 0 && (
                  <LineItem label="Retención Impuesto Único" value={extractedData.retencion_imp_unico} />
                )}
                {extractedData.retencion_tasa_ley_21133 !== undefined && extractedData.retencion_tasa_ley_21133 !== 0 && (
                  <LineItem label="Retención Ley 21.133" value={extractedData.retencion_tasa_ley_21133} />
                )}
              </>
            )}

            {/* SUBTOTAL DETERMINADO */}
            {extractedData.subtotal_imp_determinado !== undefined && (
              <LineItem
                label="Subtotal Impuesto Determinado"
                value={extractedData.subtotal_imp_determinado}
                isSubtotal
              />
            )}

            {/* OTROS IMPUESTOS */}
            {(extractedData.codigo_543 !== undefined || extractedData.codigo_556 !== undefined || extractedData.codigo_573 !== undefined) && (
              <>
                <Section title="Otros Impuestos" icon="📋" />

                {extractedData.codigo_543 !== undefined && extractedData.codigo_543 !== 0 && (
                  <LineItem label="Código 543" value={extractedData.codigo_543} />
                )}
                {extractedData.codigo_556 !== undefined && extractedData.codigo_556 !== 0 && (
                  <LineItem label="Código 556" value={extractedData.codigo_556} />
                )}
                {extractedData.codigo_573 !== undefined && extractedData.codigo_573 !== 0 && (
                  <LineItem label="Código 573" value={extractedData.codigo_573} />
                )}
              </>
            )}

            {/* TOTAL DETERMINADO */}
            {extractedData.total_determinado !== undefined && (
              <LineItem
                label="TOTAL IMPUESTOS DETERMINADOS"
                value={extractedData.total_determinado}
                isSubtotal
              />
            )}

            {/* AJUSTES Y MULTAS */}
            {(extractedData.mas_ipc !== undefined || extractedData.mas_interes_multas !== undefined || extractedData.condonacion !== undefined) && (
              <>
                <Section title="Ajustes y Recargos" icon="⚖️" />

                {extractedData.mas_ipc !== undefined && extractedData.mas_ipc !== 0 && (
                  <LineItem label="(+) Reajuste IPC" value={extractedData.mas_ipc} />
                )}
                {extractedData.mas_interes_multas !== undefined && extractedData.mas_interes_multas !== 0 && (
                  <LineItem label="(+) Intereses y Multas" value={extractedData.mas_interes_multas} />
                )}
                {extractedData.condonacion !== undefined && extractedData.condonacion !== 0 && (
                  <LineItem label="(-) Condonación" value={-extractedData.condonacion} />
                )}
              </>
            )}

            {/* TOTAL A PAGAR */}
            {(extractedData.total_pagar_plazo_legal !== undefined || extractedData.total_pagar_recargo !== undefined) && (
              <>
                <div className="pt-4"></div>
                {extractedData.total_pagar_plazo_legal !== undefined && (
                  <LineItem
                    label="TOTAL A PAGAR (Plazo Legal)"
                    value={extractedData.total_pagar_plazo_legal}
                    isTotal
                  />
                )}
                {extractedData.total_pagar_recargo !== undefined && extractedData.total_pagar_recargo !== extractedData.total_pagar_plazo_legal && (
                  <LineItem
                    label="TOTAL A PAGAR (Con Recargo)"
                    value={extractedData.total_pagar_recargo}
                    isTotal
                  />
                )}
              </>
            )}
          </div>

          {/* Info de Pago */}
          {(extractedData.medio_pago || extractedData.banco) && (
            <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4">
              <div className="flex flex-wrap gap-6 text-sm">
                {extractedData.medio_pago && (
                  <div>
                    <span className="text-slate-600 dark:text-slate-400">Medio de Pago: </span>
                    <span className="font-medium text-slate-900 dark:text-white">{extractedData.medio_pago}</span>
                  </div>
                )}
                {extractedData.banco && (
                  <div>
                    <span className="text-slate-600 dark:text-slate-400">Banco: </span>
                    <span className="font-medium text-slate-900 dark:text-white">{extractedData.banco}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        // Fallback for forms without extracted data
        <div className="rounded-xl border border-slate-200 bg-white p-8 dark:border-slate-700 dark:bg-slate-900 text-center">
          <p className="text-slate-600 dark:text-slate-400">
            No hay datos detallados disponibles para este formulario.
          </p>
          {form.amount !== undefined && (
            <div className="mt-6">
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Monto declarado:</p>
              <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                {formatCurrency(form.amount)}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
